"""Diagnóstico geral e leve da instalação da STAR V1.9.

Não carrega o Chatterbox pesado. Para síntese real use DIAGNOSTICO_VOZ.bat.
"""
from pathlib import Path
import importlib
import json

ROOT = Path(__file__).resolve().parent


def _configure_console_utf8():
    """Evita falhas de Unicode em consoles Windows com code page antiga."""
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
    "core.physics_knowledge",
    "core.router",
    "core.executive",
    "core.star_core",
    "core.commands",
    "core.conversation",
    "core.weather",
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
    from core.commands import command_count
    from core.conversation import conversation_response_count

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
    pack_stats = star.packs.stats()
    physics_stats = star.physics.stats()

    checks = [
        ("identidade", star.get_name() == "STAR"),
        ("saudação", bool(star.process("olá"))),
        ("criador", bool(star.process("quem criou você?"))),
        ("matemática", "4" in str(star.process("quanto é 2+2"))),
        ("knowledge pack manager", hasattr(star.packs, "stats")),
        ("física local = 50000", physics_stats.get("content_variations") == 50000),
        ("física canônica = 50 tópicos", physics_stats.get("canonical_topics") == 50),
        ("catálogo de voz >= 4000", command_count() >= 4000),
        ("catálogo conversacional >= 5000", conversation_response_count() >= 5000),
    ]
    for name, ok in checks:
        print(("🟢 " if ok else "🔴 ") + name)
        if not ok:
            failures.append((name, "check failed"))

    print(
        f"⚛️ Física local: {physics_stats.get('canonical_topics', 0)} tópico(s), "
        f"{physics_stats.get('content_variations', 0)} conteúdo(s) variável(is)"
    )
    print(
        f"📦 Knowledge Packs: {pack_stats.get('packs', 0)} pack(s), "
        f"{pack_stats.get('entries', 0)} entrada(s) carregada(s)"
    )
    if pack_stats.get("packs", 0) and not pack_stats.get("entries", 0):
        warnings.append(
            "Knowledge Packs foram descobertos, mas nenhuma entrada de conhecimento "
            "foi carregada; descoberta de manifesto não equivale a conteúdo utilizável."
        )

    print(
        f"🗣️ Catálogo de voz: {command_count()} variações | "
        f"💬 respostas conversacionais: {conversation_response_count()}"
    )

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
