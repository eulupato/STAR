"""Diagnóstico geral e leve da instalação da STAR.

Não carrega Chatterbox, Whisper nem WebView. Testa a arquitetura local
principal e diferencia falha crítica de capacidade opcional não instalada.
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
    "core.avatar",
    "core.emotion",
    "core.photo_library",
    "core.cure",
    "core.skills",
    "core.tools",
    "core.ai_engine",
    "core.models.model_manager",
    "core.models.local.ollama",
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
    "knowledge.bootstrap",
    "knowledge.importers.pdf",
    "knowledge.importers.heroes",
    "knowledge.sources.official",
    "knowledge.heroes_builder",
    "knowledge.recipes",
    "modules.computer_control",
    "modules.media_controller",
    "modules.media_host",
    "database.database",
    "database.models",
    "database.memory",
    "voice.manager",
    "voice.audio_input",
    "gui.navigation",
    "gui.components.carousel",
    "gui.heroes_view",
    "gui.app",
]


def _whisper_model_ready(model_value: str) -> tuple[bool, str]:
    path = Path(str(model_value)).expanduser()
    required = (path / "model.bin", path / "config.json")
    ready = path.is_dir() and all(item.exists() and item.stat().st_size > 0 for item in required)
    if ready:
        return True, str(path)
    return False, f"modelo local ausente/incompleto: {path}"


def main():
    _configure_console_utf8()
    from core.release import RELEASE, STAR_VERSION
    manifest = json.loads(
        (ROOT / "STAR_MANIFEST.json").read_text(encoding="utf-8")
    )

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

        from core.islands import get_islands
        from core.media_intents import parse_media_intent
        from knowledge.recipes import RecipeBook
        from gui.navigation import NavigationManager

        recipe_count = len(
            RecipeBook(ROOT / "knowledge" / "recipes").load()
        )
        islands = get_islands()
        nav = NavigationManager()
        nav.go("hub")
        nav.go("house")
        nav.go("bedroom")
        nav.go("closet")
        nav.go("gallery")
        navigation_ok = (
            nav.back() == "closet"
            and nav.back() == "bedroom"
            and nav.back() == "house"
            and nav.back() == "hub"
            and nav.back() == "menu"
        )

        media_restore = parse_media_intent("sair da tela cheia da TV")
        media_volume = parse_media_intent("volume da TV para 42")

        checks = [
            (
                "versão única",
                STAR_VERSION == str(manifest.get("version", "")).strip()
                and RELEASE.version == STAR_VERSION,
            ),
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
            ("Livro de Receitas", recipe_count >= 1),
            (
                "Cozinha disponível",
                islands["casa"]["subareas"]["cozinha"]["status"] == "available",
            ),
            ("Navegação STAR WORLD", navigation_ok),
            (
                "Media intents",
                media_restore is not None
                and media_restore.get("action") == "restore"
                and media_volume is not None
                and media_volume.get("value") == 42,
            ),
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
    stt_backend = voice.stt_configured
    stt_model, stt_detail = _whisper_model_ready(voice.stt.model_size)
    print("-" * 64)
    print("VOZ (sem carregar modelos pesados)")
    print(f"Modo: {voice.mode}")
    print(f"STT backend: {'SIM' if stt_backend else 'NÃO'}")
    print(f"STT modelo local: {'SIM' if stt_model else 'NÃO'}")
    print(f"STT detalhe: {stt_detail}")
    print(f"TTS: {voice.tts_description}")
    if not stt_backend:
        warnings.append("faster-whisper não instalado")
    elif not stt_model:
        warnings.append("STT local indisponível: " + stt_detail)
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
