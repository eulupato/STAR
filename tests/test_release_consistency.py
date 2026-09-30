import json
from pathlib import Path

import config
from core.release import APP_NAME, RELEASE_CHANNEL, RELEASE_STATUS, VERSION
from core.star_identity import StarIdentity

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_is_runtime_source_of_truth():
    manifest = json.loads((ROOT / "STAR_MANIFEST.json").read_text(encoding="utf-8"))

    assert APP_NAME == manifest["name"]
    assert VERSION == manifest["version"]
    assert RELEASE_STATUS == manifest["release_status"]
    assert RELEASE_CHANNEL == manifest["release_channel"]

    assert config.APP_NAME == APP_NAME
    assert config.VERSION == VERSION
    assert config.RELEASE_STATUS == RELEASE_STATUS
    assert config.RELEASE_CHANNEL == RELEASE_CHANNEL


def test_official_identity_is_consistent():
    identity = StarIdentity()

    assert identity.get_name() == "STAR"
    assert identity.get_full_name() == "System for Thought, Analysis and Response"
    assert identity.get_creator() == "Lu"
    assert identity.is_creator("Lu") is True


def test_only_three_product_launchers_exist_and_match_manifest():
    manifest = json.loads((ROOT / "STAR_MANIFEST.json").read_text(encoding="utf-8"))
    expected = {
        "pc": "INICIAR_PC.bat",
        "mobile": "INICIAR_MOBILE.bat",
        "watch": "INICIAR_WATCH.bat",
    }

    assert manifest["launchers"] == expected
    assert manifest["launcher"] == expected["pc"]
    assert sorted(path.name for path in ROOT.glob("INICIAR_*.bat")) == sorted(expected.values())
    assert (ROOT / "clients" / "star_mobile_app.py").exists()
    assert manifest["star_mobile_app"]["core_source"] == "STAR Device Gateway -> PC StarCore"
    assert manifest["star_mobile_app"]["shares_pc_cognition"] is True
    assert manifest["star_mobile_app"]["creates_parallel_core"] is False
    assert manifest["star_watch_app"]["shares_pc_cognition"] is True
    assert manifest["star_watch_app"]["creates_parallel_core"] is False
