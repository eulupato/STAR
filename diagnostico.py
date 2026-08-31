"""Diagnóstico geral e leve da instalação da STAR V2.0 MIND.

Não carrega o Chatterbox pesado. Para síntese real use DIAGNOSTICO_VOZ.bat.
"""
from pathlib import Path
import importlib
import json

ROOT = Path(__file__).resolve().parent


def _configure_console_utf8():
    import sys

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


MODULES = [
    "config",
    "core.star_identity",
    "core.internal_knowledge",
    "core.router",
    "core.executive",
    "core.star_core",
    "core.mind",
    "core.mind.event_bus",
    "core.mind.working_memory",
    "core.mind.context",
    "core.mind.salience",
    "core.mind.planner",
    "core.mind.capabilities",
    "core.mind.executive",
    "core.mind.metacognition",
    "core.mind.cognitive_loop",
    "core.islands",
    "core.memory",
    "core.emotion",
    "core.avatar",
    "core.knowledge_registry",
    "core.cure",
    "core.math_engine",
    "modules.computer_control",
    "database.database",
    "database.memory",
    "voice.manager",
    "voice.audio_input",
    "gui.app",
]


def main():
    _configure_console_utf8()
    from config import VERSION

    print("=" * 64)
    print(f"⭐ DIAGNÓSTICO GERAL STAR V{VERSION}")
    print("=" * 64)

    failures = []
    warnings = []

    for name in MODULES:
        try:
            importlib.import_module(name)
            print(f"🟢 import {name}")
        except Exception as error:
            failures.append((name, str(error)))
            print(f"🔴 import {name}: {error}")

    from main import create_star

    star = create_star()

    if star.mind is None:
        failures.append(("MIND V2", "desativada em config.py"))
        name_answer = ""
    else:
        star.process("meu nome é TesteMind")
        name_answer = star.process("qual meu nome")

    checks = [
        ("identidade", star.get_name() == "STAR"),
        ("MIND V2 ativa", star.mind_status().get("active") is True),
        ("Event Bus", star.mind is not None and star.mind.events.count() > 0),
        (
            "Working Memory",
            star.mind is not None
            and star.mind.working_memory.snapshot()["turn_count"] >= 2,
        ),
        ("Context Engine", "TesteMind" in name_answer),
        ("saudação", bool(star.process("olá"))),
        ("criador", bool(star.process("quem criou você?"))),
        ("matemática", "4" in str(star.process("quanto é 2+2"))),
        ("knowledge packs", bool(star.packs.list())),
    ]
    for name, ok in checks:
        print(("🟢 " if ok else "🔴 ") + name)
        if not ok:
            failures.append((name, "check failed"))

    print("-" * 64)
    print("MIND V2")
    mind_status = star.mind_status()
    print(f"Ativa: {'SIM' if mind_status.get('active') else 'NÃO'}")
    print(f"Eventos: {mind_status.get('events')}")
    print(f"Turnos em working memory: {mind_status.get('working_memory_turns')}")
    print(f"Último executor: {mind_status.get('last_executor')}")

    from voice.manager import VoiceManager

    voice = VoiceManager()
    print("-" * 64)
    print("VOZ (sem carregar modelos)")
    print(f"Modo: {voice.mode}")
    print(f"STT instalado: {'SIM' if voice.stt_configured else 'NÃO'}")
    print(f"Referência resolvida: {voice.official.reference_path}")
    print(f"Referência existe: {'SIM' if voice.official.reference_path.exists() else 'NÃO'}")
    print(f"Chatterbox env: {'SIM' if voice.official.python_path.exists() else 'NÃO'}")
    print(f"Worker: {'SIM' if voice.official.worker_path.exists() else 'NÃO'}")
    print(f"TTS: {voice.tts_description}")
    if not voice.official.configured:
        warnings.append("voz oficial indisponível: " + voice.official.status_message)
    voice.close()

    settings_path = ROOT / "user_settings.json"
    if settings_path.exists():
        try:
            json.loads(settings_path.read_text(encoding="utf-8"))
            print("🟢 user_settings.json")
        except Exception as exc:
            warnings.append(f"user_settings.json inválido: {exc}")

    print("-" * 64)
    if warnings:
        print("⚠️ AVISOS:")
        for item in warnings:
            print("  -", item)

    if failures:
        print(f"❌ {len(failures)} falha(s) crítica(s).")
        for name, error in failures:
            print(f"  - {name}: {error}")
        raise SystemExit(1)

    print("✅ DIAGNÓSTICO GERAL CONCLUÍDO SEM FALHAS CRÍTICAS.")


if __name__ == "__main__":
    main()
