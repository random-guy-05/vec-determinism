import pytest

from vec_determinism.core import classify, render_command


def test_placeholder_must_appear_exactly_once(tmp_path):
    with pytest.raises(ValueError):
        render_command(["python", "x.py"], tmp_path / "x.h5ad")
    with pytest.raises(ValueError):
        render_command(
            ["python", "{output}", "{output}"],
            tmp_path / "x.h5ad",
        )


def test_classification_levels():
    rows = [
        {
            "returncode": 0,
            "output_exists": True,
            "sha256": "a",
            "scorer_fingerprint": "x",
        },
        {
            "returncode": 0,
            "output_exists": True,
            "sha256": "b",
            "scorer_fingerprint": "x",
        },
    ]
    assert classify(rows) == "SCORER_CONTENT_IDENTICAL"
    rows[1]["scorer_fingerprint"] = "y"
    assert classify(rows) == "NONDETERMINISTIC_CONTENT"
