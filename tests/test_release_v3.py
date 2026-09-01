from pathlib import Path
import json

from core.release import RELEASE, STAR_CODENAME, STAR_VERSION


def test_star_v3_release_is_loaded_from_manifest():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "STAR_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["version_source"] == "STAR_MANIFEST.json"
    assert STAR_VERSION == manifest["version"] == "3.0"
    assert STAR_CODENAME == manifest["codename"] == "KNOWLEDGE"
    assert RELEASE.label == "STAR V3.0 — KNOWLEDGE"


def test_config_uses_release_source_of_truth():
    import config

    assert config.VERSION == STAR_VERSION
    assert config.CODENAME == STAR_CODENAME
