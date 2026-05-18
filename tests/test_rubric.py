import pytest

from triage.rubric import Rubric


def test_default_rubric():
    r = Rubric()
    assert r.min_spend == 1000.0
    assert r.max_proposals == 15
    assert "python" in r.skills


def test_load_none_returns_default():
    assert Rubric.load(None) == Rubric()


def test_load_from_yaml(tmp_path):
    p = tmp_path / "r.yaml"
    p.write_text("min_spend: 5000\nmax_proposals: 8\n", encoding="utf-8")
    r = Rubric.load(p)
    assert r.min_spend == 5000
    assert r.max_proposals == 8
    assert r.min_hire_rate == 0.5


def test_load_rejects_unknown_keys(tmp_path):
    p = tmp_path / "r.yaml"
    p.write_text("bogus_key: 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown rubric keys"):
        Rubric.load(p)


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(OSError):
        Rubric.load(tmp_path / "nope.yaml")
