from pathlib import Path

import pytest

from voice.seed_vc import SeedVCBackend, SeedVCError


def _fake_runtime(tmp_path: Path) -> SeedVCBackend:
    home = tmp_path / "seed-vc"
    home.mkdir()
    for filename in (
        "inference.py",
        "inference_v2.py",
        "real-time-gui.py",
        "train.py",
        "train_v2.py",
    ):
        (home / filename).write_text("# test\n", encoding="utf-8")
    python_path = home / ".venv" / "Scripts" / "python.exe"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("test", encoding="utf-8")
    return SeedVCBackend(home=home)


def test_seed_vc_is_optional_when_runtime_is_absent(tmp_path):
    backend = SeedVCBackend(home=tmp_path / "missing")
    assert backend.configured is False
    assert "runtime Seed-VC ausente" in backend.status_message


def test_seed_vc_capabilities_are_detected_without_importing_ml(tmp_path):
    backend = _fake_runtime(tmp_path)
    assert backend.configured is True
    assert all(backend.capabilities.values())


def test_seed_vc_rejects_missing_audio_before_inference(tmp_path):
    backend = SeedVCBackend(home=tmp_path / "missing")
    with pytest.raises(SeedVCError, match="Áudio de origem"):
        backend.convert_v1(tmp_path / "source.wav", tmp_path / "target.wav")


def test_v1_builds_singing_flags_and_returns_generated_wav(tmp_path, monkeypatch):
    backend = _fake_runtime(tmp_path)
    source = tmp_path / "source.wav"
    target = tmp_path / "target.wav"
    source.write_bytes(b"source")
    target.write_bytes(b"target")
    captured = {}

    def fake_run(args, timeout=None):
        captured["args"] = args
        output = Path(args[args.index("--output") + 1])
        (output / "result.wav").write_bytes(b"wav")

    monkeypatch.setattr(backend, "_run", fake_run)
    output = backend.convert_v1(
        source,
        target,
        singing=True,
        auto_f0_adjust=True,
        semi_tone_shift=2,
    )

    assert output.name == "result.wav"
    assert captured["args"][captured["args"].index("--f0-condition") + 1] == "true"
    assert captured["args"][captured["args"].index("--auto-f0-adjust") + 1] == "true"
    assert captured["args"][captured["args"].index("--semi-tone-shift") + 1] == "2"


def test_v2_does_not_enable_compile_when_false(tmp_path, monkeypatch):
    backend = _fake_runtime(tmp_path)
    source = tmp_path / "source.wav"
    target = tmp_path / "target.wav"
    source.write_bytes(b"source")
    target.write_bytes(b"target")
    captured = {}

    def fake_run(args, timeout=None):
        captured["args"] = args
        output = Path(args[args.index("--output") + 1])
        (output / "result.wav").write_bytes(b"wav")

    monkeypatch.setattr(backend, "_run", fake_run)
    backend.convert_v2(source, target, compile_model=False)

    # O upstream usa argparse type=bool; passar a string "false" ativaria True.
    assert "--compile" not in captured["args"]


def test_v2_exposes_style_anonymization_and_compile(tmp_path, monkeypatch):
    backend = _fake_runtime(tmp_path)
    source = tmp_path / "source.wav"
    target = tmp_path / "target.wav"
    source.write_bytes(b"source")
    target.write_bytes(b"target")
    captured = {}

    def fake_run(args, timeout=None):
        captured["args"] = args
        output = Path(args[args.index("--output") + 1])
        (output / "result.wav").write_bytes(b"wav")

    monkeypatch.setattr(backend, "_run", fake_run)
    backend.convert_v2(
        source,
        target,
        convert_style=True,
        anonymization_only=True,
        compile_model=True,
    )

    args = captured["args"]
    assert args[args.index("--convert-style") + 1] == "true"
    assert args[args.index("--anonymization-only") + 1] == "true"
    assert args[args.index("--compile") + 1] == "True"


def test_external_seed_vc_runtime_is_ignored_by_git():
    root = Path(__file__).resolve().parents[1]
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    assert "voice/external/" in gitignore
