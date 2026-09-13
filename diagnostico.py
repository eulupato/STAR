"""Diagnóstico leve da STAR V1.9 + Integrated Evolution Alpha.

Não baixa modelos, não abre câmera, não inicia TTS e não usa internet. O objetivo é
validar os contratos reais do Core, M.drives, MIND, idiomas, People, Cura, Web
Knowledge e a trava offline antes de aceitar uma atualização como saudável.
"""
from __future__ import annotations

import importlib
import sys
import unicodedata


MODULES = (
    "config",
    "core.star_identity",
    "core.internal_knowledge",
    "core.physics_knowledge_150k",
    "core.chemistry_knowledge_500k",
    "core.multidisciplinary_knowledge",
    "core.knowledge_expansion_15m",
    "core.curriculum_knowledge",
    "core.religion_magic_knowledge",
    "core.mind",
    "core.cognition_runtime",
    "core.goal_engine",
    "core.guardian",
    "core.semantic_rag",
    "core.ocr",
    "core.research_hub",
    "core.web_knowledge",
    "core.people",
    "core.cure",
    "core.scientific_graph",
    "core.scientific_simulation",
    "core.operator_index",
    "core.senses",
    "core.evolution",
    "core.mdrives",
    "core.m_drive_manager",
    "core.language_profiles",
    "core.language_catalog",
    "core.offline_dictionary",
    "core.global_localization",
    "core.language_manager",
    "core.router",
    "core.executive",
    "core.star_core",
    "core.commands",
    "core.conversation",
    "core.weather",
    "database.database",
    "database.cognitive_store",
    "gui.localized_app",
)


def _console_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def _check(failures: list, name: str, condition, detail: str = "") -> bool:
    ok = bool(condition)
    print(("🟢 " if ok else "🔴 ") + name + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(name)
    return ok


def main() -> int:
    _console_utf8()
    from config import VERSION

    print("=" * 76)
    print(f"⭐ DIAGNÓSTICO STAR V{VERSION} + INTEGRATED EVOLUTION ALPHA")
    print("=" * 76)
    failures: list[str] = []
    warnings: list[str] = []

    for name in MODULES:
        try:
            importlib.import_module(name)
            print(f"🟢 import {name}")
        except Exception as exc:
            failures.append(f"import {name}")
            print(f"🔴 import {name}: {type(exc).__name__}: {exc}")

    if failures:
        print("\n🔴 Imports críticos falharam; diagnóstico funcional interrompido.")
        return 1

    from core.commands import command_count
    from core.conversation import conversation_response_count
    from core.offline_dictionary import normalize_term
    from core.thematic_voice import THEMATIC_VOICE_VARIATIONS
    from main import create_star

    star = create_star()
    physics = star.physics.stats()
    chemistry = star.chemistry.stats()
    multi = star.multidisciplinary.stats()
    plus = star.knowledge_plus.stats()
    curriculum = star.curriculum.stats()
    cultural = star.religion_magic.stats()
    mind = star.mind.stats()
    language = star.language.stats()
    localization = language.get("global_localization", {})
    evolution = star.evolution.stats()
    mdrives = star.mdrives.stats()

    print("\nCORE / KNOWLEDGE")
    _check(failures, "identidade STAR", star.get_name() == "STAR")
    _check(failures, "criador disponível", bool(star.get_creator()))
    _check(failures, "saudação local", bool(star.process("olá")))
    _check(failures, "matemática local 2+2", "4" in str(star.process("quanto é 2+2")))
    _check(failures, "M.drives é interface oficial", star.mdrives is star.packs)
    _check(failures, "Física 150K addressable", physics.get("content_variations") == 150_000)
    _check(failures, "Química 500K addressable", chemistry.get("content_variations") == 500_000)
    _check(failures, "Multidisciplinar 6.5M addressable", multi.get("total_content_variations") == 6_500_000)
    _check(failures, "Knowledge PLUS +15M", plus.get("added_content_variations") == 15_000_000)
    _check(failures, "legado combinado 22.15M", plus.get("combined_content_variations") == 22_150_000)
    _check(failures, "currículo 56 temas", curriculum.get("themes") == 56)
    _check(failures, "currículo 885 conceitos", curriculum.get("unique_concepts") == 885)
    _check(failures, "currículo 941M visões addressable", curriculum.get("total_new_addressable_contents") == 941_000_000)
    _check(failures, "cultura 125 assuntos", cultural.get("subjects") == 125)
    _check(failures, "cultura 5M visões addressable", cultural.get("total_addressable_contents") == 5_000_000)
    _check(failures, "M.drives carregáveis", mdrives.get("mdrives", 0) >= 1)

    print("\nMIND / EVOLUTION")
    _check(failures, "MIND 15 capacidades", mind.get("capabilities") == 15)
    _check(failures, "MIND 15M variantes operacionais", mind.get("support_contents_total") == 15_000_000)
    _check(failures, "Integrated Evolution alpha", evolution.get("status") == "integrated-alpha")
    _check(failures, "Guardian default-deny", evolution.get("guardian", {}).get("default_deny_unknown") is True)
    _check(failures, "Goal Engine persistente", evolution.get("goal_engine", {}).get("durable_checkpoints") is True)
    _check(failures, "RAG local", evolution.get("semantic_rag", {}).get("status") == "active-local")
    _check(failures, "Operator não escreve/apaga", evolution.get("operator", {}).get("writes_or_deletes") is False)
    _check(failures, "Senses não finge scene understanding", evolution.get("senses", {}).get("semantic_scene_understanding") is False)
    _check(failures, "Web Knowledge sem IA generativa", evolution.get("web_knowledge", {}).get("generative_ai") is False)
    _check(failures, "Web Knowledge preserva cache offline", evolution.get("web_knowledge", {}).get("offline_cache") is True)

    print("\nOFFLINE / NETWORK")
    _check(failures, "Core inicia OFFLINE", star.network_enabled is False)
    _check(failures, "clima inicia sem rede", star.weather.enabled is False)
    web_offline = star.web.search("diagnóstico sem rede", network_enabled=False)
    _check(failures, "busca web bloqueada offline", web_offline.get("reason") == "network_disabled")
    _check(failures, "painel AGORA não aciona clima offline", "nenhuma rede foi acionada" in star.now_status(include_weather=True))
    star.network_enabled = True
    _check(failures, "trava central habilita provider online", star.weather.enabled is True)
    star.network_enabled = False
    _check(failures, "trava central desabilita provider novamente", star.weather.enabled is False)

    print("\nLANGUAGE / LOCALIZATION")
    _check(failures, "13 famílias linguísticas", language.get("language_families") == 13)
    _check(failures, "18 perfis de locale", language.get("locale_profiles") == 18)
    _check(failures, "12 perfis modernos/dialetais", language.get("modern_locales") == 12)
    _check(failures, "6 perfis históricos", language.get("historical_locales") == 6)
    _check(failures, "catálogo contextual curado continua 5 famílias", language.get("curated_expression_families") == 5)
    _check(failures, "500K conteúdos contextuais preservados", language.get("total_semantic_contents") == 500_000)
    _check(failures, "18 locales no runtime", len(localization.get("supported_locales", [])) == 18)
    _check(failures, "sem tradução parcial falsa", localization.get("strict_no_partial_translation") is True)
    _check(failures, "sem MT moderno fingido para históricos", localization.get("historical_profiles_use_modern_mt") is False)
    _check(failures, "UI japonesa offline", star.language.localize_static("INICIAR", "ja-JP") == "開始")
    _check(failures, "UI árabe offline", star.language.localize_static("AGORA", "ar-001") == "الآن")
    _check(failures, "Unicode japonês preservado", normalize_term("日本語") == "日本語")
    _check(
        failures,
        "Unicode coreano preservado",
        unicodedata.normalize("NFC", normalize_term("한국어")) == "한국어",
    )
    _check(failures, "hieróglifo egípcio preservado", "𓂀" in normalize_term("𓂀"))
    _check(failures, ">=5 fontes por família", min(language.get("dictionary_sources", {}).values(), default=0) >= 5)

    print("\nPEOPLE / CURA")
    people = evolution.get("people", {})
    cure = evolution.get("cure", {})
    _check(failures, "People local", people.get("network_required") is False)
    _check(failures, "People sem reconhecimento biométrico", people.get("face_recognition") is False)
    _check(failures, "People sem inferência sensível", people.get("sensitive_trait_inference") is False)
    _check(failures, "People não ingere GPS EXIF", people.get("gps_exif_ingested") is False)
    _check(failures, "Cura local", cure.get("offline") is True)
    _check(failures, "Cura sem GitHub obrigatório", cure.get("github_required") is False)
    _check(failures, "Cura não gera reparo de código", cure.get("generative_code_repair") is False)
    _check(failures, "Cura restaura snapshot seguro", cure.get("safe_snapshot_restore") is True)
    health = star.cure.health_check(deep=False)
    _check(failures, "Cura health check", health.get("healthy") is True, f"falhas={len(health.get('failures', []))}")

    print("\nVOICE / UX CONTRACTS")
    _check(failures, "comandos operacionais >= 4000", command_count() >= 4_000)
    _check(failures, "catálogo voz > 1M", command_count() + THEMATIC_VOICE_VARIATIONS > 1_000_000)
    _check(failures, "smalltalk >= 5000 combinações", conversation_response_count() >= 5_000)

    neural = localization.get("neural", {})
    if not neural.get("installed"):
        warnings.append("Argos Translate/modelos neurais não materializados; fallback offline seguro permanece ativo.")

    print("\n" + "=" * 76)
    if warnings:
        print("⚠️ AVISOS")
        for warning in warnings:
            print("-", warning)
    if failures:
        print(f"🔴 DIAGNÓSTICO: {len(failures)} falha(s)")
        for failure in failures:
            print("-", failure)
        return 1

    print("🟢 DIAGNÓSTICO: STAR saudável nos contratos auditados")
    print("Nota: contagens de conhecimento são conteúdos/visões endereçáveis, não milhões de fatos pesquisados individualmente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
