from __future__ import annotations

import hashlib
import subprocess
from contextlib import suppress
from pathlib import Path

import numpy as np
from scipy import sparse


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _update_matrix(digest, matrix, chunk_rows: int = 256) -> None:
    for start in range(0, int(matrix.shape[0]), chunk_rows):
        part = matrix[start : start + chunk_rows]
        if sparse.issparse(part):
            part = part.toarray()
        array = np.ascontiguousarray(np.asarray(part, dtype=np.float32))
        digest.update(array.tobytes())


def scorer_fingerprint(path: Path, task: str) -> str:
    import anndata as ad

    task = task.upper()
    if task not in {"T1", "T2", "T3"}:
        raise ValueError("task must be T1, T2, or T3")

    data = ad.read_h5ad(path, backed="r")
    try:
        digest = hashlib.sha256()
        digest.update(task.encode())
        digest.update(str(tuple(data.X.shape)).encode())
        for gene in data.var_names.astype(str):
            digest.update(gene.encode("utf-8"))
            digest.update(b"\0")
        _update_matrix(digest, data.X)

        if task in {"T2", "T3"}:
            if "spatial_3D" not in data.obsm:
                raise ValueError("T2/T3 output is missing obsm['spatial_3D']")
            coords = np.asarray(data.obsm["spatial_3D"], dtype=np.float32)
            if coords.ndim != 2 or coords.shape[0] != data.n_obs or coords.shape[1] < 3:
                raise ValueError("spatial_3D must have shape cells x >=3")
            digest.update(np.ascontiguousarray(coords[:, :3]).tobytes())
        return digest.hexdigest()
    finally:
        with suppress(Exception):
            data.file.close()


def render_command(parts: list[str], output: Path) -> list[str]:
    if sum(part.count("{output}") for part in parts) != 1:
        raise ValueError("command must contain {output} exactly once")
    return [part.replace("{output}", str(output)) for part in parts]


def run_exporter(command: list[str], output: Path) -> dict:
    rendered = render_command(command, output)
    result = subprocess.run(
        rendered,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "command": rendered,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-8000:],
        "stderr_tail": result.stderr[-8000:],
        "output_exists": output.is_file(),
    }


def classify(records: list[dict]) -> str:
    if not records or any(
        record["returncode"] != 0 or not record["output_exists"]
        for record in records
    ):
        return "RUN_FAILED"
    byte_hashes = {record["sha256"] for record in records}
    if len(byte_hashes) == 1:
        return "BYTE_IDENTICAL"
    semantic_hashes = {record["scorer_fingerprint"] for record in records}
    if len(semantic_hashes) == 1:
        return "SCORER_CONTENT_IDENTICAL"
    return "NONDETERMINISTIC_CONTENT"
