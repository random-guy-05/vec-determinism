# Community Contribution submission text

## Title
VEC Determinism — scorer-aware reproducibility checker for prediction exporters

## Description
VEC Determinism runs a prediction/export command multiple times into isolated output files and distinguishes ordinary file-byte variation from genuine scorer-relevant nondeterminism. It compares SHA-256 hashes first, then canonicalizes exactly the VEC content that affects scoring: float32 expression, ordered gene names, and for T2/T3 the first three spatial_3D columns. It reports BYTE_IDENTICAL, SCORER_CONTENT_IDENTICAL, NONDETERMINISTIC_CONTENT, or RUN_FAILED with machine-readable JSON. This catches unseeded sampling/export bugs before model selection or final submission without falsely failing solely because HDF5 container bytes differ.
