from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from .core import classify, run_exporter, scorer_fingerprint, sha256_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check whether a VEC exporter is scorer-content deterministic."
    )
    parser.add_argument("--task", required=True, choices=["T1", "T2", "T3"])
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--json", type=Path, dest="json_path")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command:
        raise SystemExit("provide an exporter command after --")
    if args.runs < 2:
        raise SystemExit("--runs must be >= 2")

    records: list[dict] = []
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for index in range(args.runs):
            output = root / f"run_{index}.h5ad"
            record = run_exporter(command, output)
            if record["returncode"] == 0 and record["output_exists"]:
                try:
                    record["sha256"] = sha256_file(output)
                    record["scorer_fingerprint"] = scorer_fingerprint(output, args.task)
                except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
                    record["fingerprint_error"] = f"{type(exc).__name__}: {exc}"
                    record["returncode"] = 2
            records.append(record)

    classification = classify(records)
    payload = {"classification": classification, "task": args.task, "runs": records}
    print(classification)

    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )

    return 0 if classification in {"BYTE_IDENTICAL", "SCORER_CONTENT_IDENTICAL"} else 4


if __name__ == "__main__":
    raise SystemExit(main())
