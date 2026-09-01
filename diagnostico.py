"""Diagnóstico geral e leve da instalação da STAR.

Não carrega Chatterbox nem WebView. Testa a arquitetura local principal.
"""
from pathlib import Path
import importlib
import json
import tempfile

ROOT = Path(__file__).resolve().parent


def _configure_console_utf8():
    import sys

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            continue


MODULES = [
    "config",
    "core.release",
    "core.logging_config",
    "core.star_identity",
    "core.internal_knowledge",
    "core.router",
    "core.executive",
    "core.star_core",
    "core.conversation",
    "core.personality",
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
    "core.math_engine",
    "core.media_intents",
    "knowledge.entities",
    "knowledge.store",
    "knowledge.graph",
    "knowledge.engine",
    "knowledge.importers.pdf",
    "knowledge.importers.heroes",
    "knowledge.sources.official",
    "knowledge.heroes_builder",
    "modules.computer_control",
    "modules.media_controller",
    "database.database",
    "database.memory",
    "voice.manager",
    "voice.audio_input",
    "gui.navigation",
    "gui.components.carousel",
    "gui.heroes_view",
    "gui.app",
]


def main():
    _configure_console_utf8()
    from core.release import RELEASE, STAR_VERSION

    print("=" * 64)
    print(f"⭐ DIAGNÓSTICO GERAL {RELEASE.label}")
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

    with tempfile.TemporaryDirectory(prefix="star_diag_") as temp:
        db_path = Path(temp) / "knowledge.db"
        star = create_star(knowledge_db=db_path)

        star.process("meu nome é TesteMind")
        name_answer = star.process("qual meu nome")
        greeting = star.process("olá")
        math_answer = star.process("quanto é 2+2")

        checks = [
            ("versão única", STAR_VERSION == "3.0"),
            ("identidade", star.get_name() == "STAR"),
            ("MIND ativa", star.mind_status().get("active") is True),
            ("Event Bus", star.mind is not None and star.mind.events.count() > 0),
            (
                "Working Memory",
                star.mind is not None
                and star.mind.working_memory.snapshot()["turn_count"] >= 2,
            ),
            ("Context Engine", "TesteMind" in name_answer),
            ("Conversation Engine", bool(greeting)),
            (
                "Conversation 1000+",
                star.conversation.status()["greeting_variations"] >= 1000
                and star.conversation.status()["status_variations"] >= 1000,
            ),
            ("matemática", "4" in str(math_answer)),
            ("Knowledge Engine", star.knowledge_status().get("active") is True),
            ("Entity System", star.knowledge_status().get("entities", 0) >= 1),
            ("Knowledge Packs", bool(star.packs.list())),
        ]
        for name, ok in checks:
            print(("🟢 " if ok else "🔴 ") + name)
            if not ok:
                failures.append((name, "check failed"))

        print("-" * 64)
        print("MIND")
        mind_status = star.mind_status()
        print(f"Ativa: {'SIM' if mind_status.get('active') else 'NÃO'}")
        print(f"Eventos: {mind_status.get('events')}")
        print(f"Turnos em working memory: {mind_status.get('working_memory_turns')}")
        print(f"Último executor: {mind_status.get('last_executor')}")

        print("-" * 64)
        print("KNOWLEDGE")
        knowledge_status = star.knowledge_status()
        print(f"Ativo: {'SIM' if knowledge_status.get('active') else 'NÃO'}")
        print(f"Entidades: {knowledge_status.get('entities')}")
        print(f"Personagens: {knowledge_status.get('heroes')}")

    from voice.manager import VoiceManager

    voice = VoiceManager()
    print("-" * 64)
    print("VOZ (sem carregar modelos pesados)")
    print(f"Modo: {voice.mode}")
    print(f"STT instalado: {'SIM' if voice.stt_configured else 'NÃO'}")
    print(f"TTS: {voice.tts_description}")
    if not voice.official.configured:
        warnings.append("voz oficial indisponível: " + voice.official.status_message)
    voice.close()

    settings_path = ROOT / "user_settings.json"
    if settings_path.exists():
        try:
            json.loads(settings_path.read_text(encoding="utf-8"))
            print("🟢 user_settings.json")
        except (OSError, json.JSONDecodeError) as exc:
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
