import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.device_runtime import DeviceRuntime


def test_runtime_selects_phone_and_watch_profiles(tmp_path):
    manifest = tmp_path / "STAR_MANIFEST.json"
    manifest.write_text(
        json.dumps(
            {
                "name": "STAR",
                "version": "test",
                "device_gateway": {"protocol": 1},
                "device_ecosystem": {
                    "labels": {"send": "MANDAR"},
                    "profiles": {
                        "phone": {"layout": "wide"},
                        "watch": {"layout": "tiny"},
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    runtime = DeviceRuntime(manifest)
    phone = runtime.profile_for({"metadata": {"form_factor": "phone"}})
    watch = runtime.profile_for({"metadata": {"form_factor": "watch"}})

    assert phone["profile"]["layout"] == "wide"
    assert watch["profile"]["layout"] == "tiny"
    assert phone["labels"]["send"] == "MANDAR"
    assert phone["revision"] == watch["revision"]


def test_runtime_revision_changes_when_manifest_changes(tmp_path):
    manifest = tmp_path / "STAR_MANIFEST.json"
    manifest.write_text(
        json.dumps({"device_ecosystem": {"labels": {"send": "A"}}}),
        encoding="utf-8",
    )
    runtime = DeviceRuntime(manifest)
    first = runtime.profile_for({"metadata": {"form_factor": "phone"}})

    manifest.write_text(
        json.dumps({"device_ecosystem": {"labels": {"send": "B"}}}),
        encoding="utf-8",
    )
    second = runtime.profile_for({"metadata": {"form_factor": "phone"}})

    assert first["labels"]["send"] == "A"
    assert second["labels"]["send"] == "B"
    assert first["revision"] != second["revision"]
