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
    "core.physics_topics_extended",
    "core.physics_knowledge_150k",
    "core.chemistry_topics_01",
    "core.chemistry_topics_20",
    "core.chemistry_knowledge_500k",
    "core.multidisciplinary_taxonomy",
    "core.multidisciplinary_knowledge",
    "core.knowledge_expansion_15m",
    "core.thematic_voice",
    "core.language_catalog",
    "core.offline_dictionary",
    "core.language_manager",
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
    from core.thematic_voice import THEMATIC_VOICE_VARIATIONS, thematic_voice_stats

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
    chemistry_stats = star.chemistry.stats()
    multi_stats = star.multidisciplinary.stats()
    plus_stats = star.knowledge_plus.stats()
    language_stats = star.language.stats()
    voice_theme_stats = thematic_voice_stats()

    plus_boundaries_ok = True
    for domain in plus_stats.get("domain_keys", []):
        first = star.knowledge_plus.content_id(domain, 0, 0)
        last = star.knowledge_plus.content_id(domain, 999, 999)
        plus_boundaries_ok = plus_boundaries_ok and first.endswith("-0000001") and last.endswith("-1000000")

    checks = [
        ("identidade", star.get_name() == "STAR"),
        ("saudação", bool(star.process("olá"))),
        ("criador", bool(star.process("quem criou você?"))),
        ("matemática", "4" in str(star.process("quanto é 2+2"))),
        ("knowledge pack manager", hasattr(star.packs, "stats")),
        ("física local = 150000", physics_stats.get("content_variations") == 150000),
        ("física canônica = 150 tópicos", physics_stats.get("canonical_topics") == 150),
        ("física adicionada = 100000", physics_stats.get("added_content_variations") == 100000),
        ("química local = 500000", chemistry_stats.get("content_variations") == 500000),
        ("química canônica = 500 tópicos", chemistry_stats.get("canonical_topics") == 500),
        ("química = 20 domínios", chemistry_stats.get("domains") == 20),
        ("química = 25 tópicos/domínio", set(chemistry_stats.get("domain_counts", {}).values()) == {25}),
        ("multidisciplinar = 13 matérias", multi_stats.get("subjects") == 13),
        ("multidisciplinar = 6500 nós", multi_stats.get("canonical_nodes") == 6500),
        ("multidisciplinar = 500 nós/matéria", multi_stats.get("canonical_nodes_per_subject") == 500),
        ("multidisciplinar = 500000/matéria", multi_stats.get("contents_per_subject") == 500000),
        ("multidisciplinar = 6500000 total", multi_stats.get("total_content_variations") == 6500000),
        ("PLUS = 15 domínios", plus_stats.get("domains") == 15),
        ("PLUS = 1000 nós novos/domínio", plus_stats.get("added_canonical_nodes_per_domain") == 1000),
        ("PLUS = 1000000 novos/domínio", plus_stats.get("added_content_variations_per_domain") == 1_000_000),
        ("PLUS = 15000000 novos", plus_stats.get("added_content_variations") == 15_000_000),
        ("conhecimento combinado = 22150000", plus_stats.get("combined_content_variations") == 22_150_000),
        ("IDs PLUS preservam limites 1..1000000", plus_boundaries_ok),
        ("voz temática = 1000000", voice_theme_stats.get("variations") == 1000000),
        ("idiomas = 5 famílias", language_stats.get("language_families") == 5),
        ("perfis de idioma = 6", language_stats.get("locale_profiles") == 6),
        ("expressões = 500000", language_stats.get("total_semantic_contents") == 500000),
        ("100k expressões por idioma", language_stats.get("contents_per_language") == 100000),
        (">=5 dicionários/fontes por idioma", min(language_stats.get("dictionary_sources", {}).values(), default=0) >= 5),
        ("catálogo operacional de voz >= 4000", command_count() >= 4000),
        ("catálogo total de voz > 1000000", command_count() + THEMATIC_VOICE_VARIATIONS > 1000000),
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
        f"🧪 Química local: {chemistry_stats.get('canonical_topics', 0)} tópico(s), "
        f"{chemistry_stats.get('domains', 0)} domínio(s), "
        f"{chemistry_stats.get('content_variations', 0)} conteúdo(s) variável(is)"
    )
    print(
        f"🧭 Multidisciplinar: {multi_stats.get('subjects', 0)} matéria(s), "
        f"{multi_stats.get('canonical_nodes', 0)} nó(s), "
        f"{multi_stats.get('total_content_variations', 0)} conteúdo(s) variável(is)"
    )
    print(
        f"🚀 Knowledge PLUS: {plus_stats.get('domains', 0)} domínio(s), "
        f"+{plus_stats.get('added_content_variations_per_domain', 0)} por domínio, "
        f"+{plus_stats.get('added_content_variations', 0)} novos | "
        f"combinado={plus_stats.get('combined_content_variations', 0)}"
    )
    print(
        f"🌐 Idiomas: {language_stats.get('language_families', 0)} famílias / "
        f"{language_stats.get('locale_profiles', 0)} perfis | "
        f"{language_stats.get('total_semantic_contents', 0)} conteúdos de expressão"
    )
    print(
        "📚 Dicionários configurados: "
        + ", ".join(f"{k}={v}" for k, v in sorted(language_stats.get("dictionary_sources", {}).items()))
        + f" | índice completo={'SIM' if language_stats.get('full_dictionary_index_ready') else 'NÃO (seed ativo)'}"
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
    if not language_stats.get("full_dictionary_index_ready"):
        warnings.append(
            "Dicionários completos ainda não foram materializados em SQLite; "
            "tradução contextual e léxico seed funcionam, mas vocabulário arbitrário pode não ser encontrado."
        )

    print(
        f"🗣️ Voz: {command_count()} operacionais + {THEMATIC_VOICE_VARIATIONS} temáticas = "
        f"{command_count() + THEMATIC_VOICE_VARIATIONS} variações | "
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
