from __future__ import annotations

import subprocess
import sys
from pathlib import Path


EXPORTER = r"""
import sys
from pathlib import Path
import anndata as ad
import numpy as np
import pandas as pd

out = Path(sys.argv[1])
mode = sys.argv[2]
if mode == "det":
    seed = 4
else:
    seed = int.from_bytes(__import__("os").urandom(4), "little")
rng = np.random.default_rng(seed)
x = rng.normal(size=(30, 12)).astype(np.float32)
data = ad.AnnData(X=x, var=pd.DataFrame(index=[f"g{i}" for i in range(12)]))
data.write_h5ad(out)
"""


def _script(tmp_path: Path) -> Path:
    path = tmp_path / "exporter.py"
    path.write_text(EXPORTER)
    return path


def test_deterministic_and_nondeterministic_exporters(tmp_path):
    script = _script(tmp_path)

    deterministic = subprocess.run(
        [
            sys.executable,
            "-m",
            "vec_determinism.cli",
            "--task",
            "T1",
            "--runs",
            "3",
            "--",
            sys.executable,
            str(script),
            "{output}",
            "det",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert deterministic.returncode == 0, deterministic.stdout + deterministic.stderr
    assert deterministic.stdout.strip() in {
        "BYTE_IDENTICAL",
        "SCORER_CONTENT_IDENTICAL",
    }

    nondeterministic = subprocess.run(
        [
            sys.executable,
            "-m",
            "vec_determinism.cli",
            "--task",
            "T1",
            "--runs",
            "3",
            "--",
            sys.executable,
            str(script),
            "{output}",
            "random",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert nondeterministic.returncode == 4
    assert "NONDETERMINISTIC_CONTENT" in nondeterministic.stdout
