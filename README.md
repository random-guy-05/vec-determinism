# VEC Determinism

**Does your export pipeline actually produce the same scorer-relevant prediction twice?**

File hashes alone are too strict for H5AD reproducibility: HDF5 metadata can change bytes without changing the prediction. VEC Determinism runs an exporter repeatedly and checks two levels:

1. **byte identity** — SHA-256 of each output file;
2. **scorer-content identity** — float32 expression, ordered gene names, and for T2/T3 the first three `spatial_3D` columns.

## Usage

Your command must contain the literal placeholder `{output}`.

```bash
pip install -e .

vec-determinism \
  --task T2 \
  --runs 3 \
  --json determinism.json \
  -- python export.py --checkpoint best.pt --out {output}
```

Classifications:

- `BYTE_IDENTICAL`: exact same file bytes every run;
- `SCORER_CONTENT_IDENTICAL`: file bytes differ, but the content read by the current scorer is identical;
- `NONDETERMINISTIC_CONTENT`: scorer-relevant content differs;
- `RUN_FAILED`: exporter failed or did not create an output.

The tool uses isolated temporary output paths and does not mutate your original artifacts.

## Development

```bash
pip install -e '.[dev]'
pytest
ruff check src tests
```

The integration tests execute synthetic deterministic and nondeterministic exporters and verify the scorer-aware classification.
