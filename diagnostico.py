"""Diagnóstico leve da STAR V1.9 + MIND / Integrated Evolution alpha.

Não baixa modelos, não inicializa câmera e não carrega TTS pesado. O objetivo é
validar arquitetura, contratos, contagens e fallbacks seguros no ambiente atual.
"""
import importlib


def _configure_console_utf8():
    import sys
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


MODULES = [
    "config", "core.star_identity", "core.internal_knowledge",
    "core.physics_knowledge_150k", "core.chemistry_knowledge_500k",
    "core.multidisciplinary_knowledge", "core.knowledge_expansion_15m",
    "core.curriculum_knowledge", "core.religion_magic_taxonomy", "core.religion_magic_knowledge",
    "core.cognitive_catalog", "database.cognitive_store", "core.labs", "core.mind",
    "core.cognition_runtime", "core.goal_engine", "core.guardian", "core.semantic_rag",
    "core.ocr", "core.research_hub", "core.scientific_graph", "core.scientific_simulation",
    "core.operator_index", "core.senses", "core.evolution", "core.mdrives",
    "core.m_drive_manager", "core.knowledge_registry", "core.thematic_voice",
    "core.language_catalog", "core.offline_dictionary", "core.global_localization",
    "core.language_manager", "core.router", "core.executive", "core.star_core",
    "core.commands", "core.conversation", "core.weather", "core.islands", "core.memory",
    "core.emotion", "core.avatar", "core.cure", "core.math_engine", "modules.computer_control",
    "database.database", "database.memory", "voice.manager", "voice.audio_input",
    "gui.app", "gui.localized_app",
]


def _check(failures, name, condition):
    ok = bool(condition)
    print(("🟢 " if ok else "🔴 ") + name)
    if not ok:
        failures.append((name, "check failed"))
    return ok


def main():
    _configure_console_utf8()
    from config import VERSION
    from core.commands import command_count
    from core.conversation import conversation_response_count
    from core.thematic_voice import THEMATIC_VOICE_VARIATIONS, thematic_voice_stats

    print("=" * 72)
    print(f"⭐ DIAGNÓSTICO GERAL STAR V{VERSION} + INTEGRATED EVOLUTION ALPHA")
    print("=" * 72)
    failures, warnings = [], []

    for name in MODULES:
        try:
            importlib.import_module(name)
            print(f"🟢 import {name}")
        except Exception as error:
            failures.append((name, str(error)))
            print(f"🔴 import {name}: {error}")

    from main import create_star
    star = create_star()
    mdrive_stats = star.mdrives.stats()
    mdrive_storage = star.mdrives.storage_stats()
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
    voice_theme = thematic_voice_stats()

    plus_bounds = True
    for domain in plus.get("domain_keys", []):
        plus_bounds &= star.knowledge_plus.content_id(domain, 0, 0).endswith("-0000001")
        plus_bounds &= star.knowledge_plus.content_id(domain, 999, 999).endswith("-1000000")

    try:
        curriculum_bounds = (
            star.curriculum.materialize_theme(1, 1)["id"] == "CURRT-001-0000001"
            and star.curriculum.materialize_theme(56, 1_000_000)["id"] == "CURRT-056-1000000"
            and star.curriculum.materialize_concept(1, 1)["id"].endswith("-0000001")
            and star.curriculum.materialize_concept(curriculum["unique_concepts"], 1_000_000)["id"].endswith("-1000000")
        )
    except (KeyError, ValueError, IndexError):
        curriculum_bounds = False

    try:
        cultural_bounds = (
            star.religion_magic.materialize(1, 1)["id"] == "RCM-0001-0001"
            and star.religion_magic.materialize(5_000, 1_000)["id"] == "RCM-5000-1000"
        )
    except (KeyError, ValueError, IndexError):
        cultural_bounds = False

    cognitive_bounds = True
    for capability in mind.get("capability_keys", []):
        cognitive_bounds &= star.mind.catalog.content_id(capability, 0, 0).endswith("-0000001")
        cognitive_bounds &= star.mind.catalog.content_id(capability, 999, 999).endswith("-1000000")

    invariant_sample = "CHEMX-0000042 9.81 m/s https://example.org `x = 2 + 2`"
    translated = star.language.translate_with_report(invariant_sample, "en-US", "pt-BR")
    invariants_ok = all(token in translated.text for token in (
        "CHEMX-0000042", "9.81 m/s", "https://example.org", "`x = 2 + 2`"
    ))

    print("-" * 72)
    print("CORE / KNOWLEDGE")
    _check(failures, "identidade STAR", star.get_name() == "STAR")
    _check(failures, "saudação", bool(star.process("olá")))
    _check(failures, "criador", bool(star.process("quem criou você?")))
    _check(failures, "matemática 2+2", "4" in str(star.process("quanto é 2+2")))
    _check(failures, "M.drives oficial", hasattr(star, "mdrives") and star.mdrives is star.packs)
    _check(failures, "física = 150000", physics.get("content_variations") == 150000)
    _check(failures, "química = 500000", chemistry.get("content_variations") == 500000)
    _check(failures, "multidisciplinar = 6500000", multi.get("total_content_variations") == 6_500_000)
    _check(failures, "Knowledge PLUS = +15000000", plus.get("added_content_variations") == 15_000_000)
    _check(failures, "factual legado = 22150000", plus.get("combined_content_variations") == 22_150_000)
    _check(failures, "IDs PLUS 1..1000000", plus_bounds)
    _check(failures, "currículo = 56 temas", curriculum.get("themes") == 56)
    _check(failures, "currículo = 885 conceitos únicos", curriculum.get("unique_concepts") == 885)
    _check(failures, "currículo = 71 duplicações", curriculum.get("deduplicated_mentions") == 71)
    _check(failures, "currículo = 941000000", curriculum.get("total_new_addressable_contents") == 941_000_000)
    _check(failures, "IDs currículo 1..1000000", curriculum_bounds)
    _check(failures, "cultural = 125 assuntos", cultural.get("subjects") == 125)
    _check(failures, "cultural = 100 tradições religiosas", cultural.get("religion_subjects") == 100)
    _check(failures, "cultural = 25 magia/esoterismo", cultural.get("magic_esotericism_subjects") == 25)
    _check(failures, "cultural = 5000 nós", cultural.get("canonical_nodes") == 5_000)
    _check(failures, "cultural = 5000000 visões", cultural.get("total_addressable_contents") == 5_000_000)
    _check(failures, "IDs culturais 1..5000 / 1..1000", cultural_bounds)
    _check(failures, "magia não declarada como física", cultural.get("claims_supernatural_as_science") is False)
    _check(failures, "conhecimento restrito não reconstruído", cultural.get("restricted_knowledge_reconstruction") is False)
    _check(failures, "consulta cultural local", "Xintoísmo" in str(star.process("história do xintoísmo")))

    print("-" * 72)
    print("MIND / EVOLUTION")
    _check(failures, "MIND = 15 capacidades", mind.get("capabilities") == 15)
    _check(failures, "MIND = 15000000 conteúdos", mind.get("support_contents_total") == 15_000_000)
    _check(failures, "MIND = 15000 nós", mind.get("canonical_nodes_total") == 15_000)
    _check(failures, "IDs MIND 1..1000000", cognitive_bounds)
    _check(failures, "SymPy disponível", mind.get("math", {}).get("sympy_available"))
    _check(failures, "MIND status", "STAR MIND" in str(star.process("status mind")))
    _check(failures, "MIND planner", "Plano:" in str(star.process("planeje criar um software simples")))
    _check(failures, "MIND derivada", "2*x" in str(star.process("derive x^2 em x")))
    _check(failures, "Integrated Evolution", evolution.get("status") == "integrated-alpha")
    _check(failures, "Working Context / Salience", evolution.get("cognition_runtime", {}).get("status") == "alpha-local")
    _check(failures, "Model Router local", star.evolution.cognition.router.choose("math", network_enabled=False)["name"] == "math_sympy")
    _check(failures, "Research Hub opt-in", star.evolution.research.search("gravity", network_enabled=False).get("reason") == "network_disabled")
    _check(failures, "Guardian default-deny", not star.evolution.guardian.authorize("diagnostic.unknown", confirmed=True).allowed)
    _check(failures, "Goal Engine checkpoints", evolution.get("goal_engine", {}).get("durable_checkpoints") is True)
    _check(failures, "Goal Scheduler persistente", evolution.get("goal_engine", {}).get("persistent_scheduler_foundation") is True)
    _check(failures, "Goal Engine sem autonomia background", evolution.get("goal_engine", {}).get("background_autonomy") is False)
    _check(failures, "RAG híbrido", evolution.get("semantic_rag", {}).get("status") == "active-local")
    _check(failures, "Knowledge Graph curricular = 885", evolution.get("knowledge_graph", {}).get("concepts_available") == 885)
    _check(failures, "Knowledge Graph cultural = 125", evolution.get("knowledge_graph", {}).get("cultural_subjects_available") == 125)
    _check(failures, "Knowledge Graph sem verdade teológica inferida", evolution.get("knowledge_graph", {}).get("theological_truth_inference") is False)
    _check(failures, "Simulation Engine NumPy", "two-body orbit 2D" in evolution.get("simulation", {}).get("models", []))
    _check(failures, "Operator read-only", evolution.get("operator", {}).get("writes_or_deletes") is False)
    _check(failures, "Senses sem scene understanding falso-positivo", evolution.get("senses", {}).get("semantic_scene_understanding") is False)
    _check(failures, "Evolution reutiliza base cultural", star.evolution.cultural is star.religion_magic)

    orbit = star.evolution.simulation.two_body_orbit(dt=20.0, duration=600.0)
    _check(failures, "órbita: drift de energia baixo", orbit.get("relative_energy_drift", 1.0) < 1e-5)
    heat = star.evolution.simulation.heat_1d([0, 1, 0], alpha=0.1, dx=1.0, dt=0.1, steps=4)
    _check(failures, "calor 1D: estabilidade", heat.get("stability_ratio", 1.0) <= 0.5)

    print("-" * 72)
    print("LANGUAGE / VOICE")
    _check(failures, "voz temática = 1000000", voice_theme.get("variations") == 1_000_000)
    _check(failures, "idiomas = 5 famílias", language.get("language_families") == 5)
    _check(failures, "perfis = 6 locales", language.get("locale_profiles") == 6)
    _check(failures, "expressões = 500000", language.get("total_semantic_contents") == 500000)
    _check(failures, ">=5 fontes de dicionário/idioma", min(language.get("dictionary_sources", {}).values(), default=0) >= 5)
    _check(failures, "localização global = 6", len(localization.get("supported_locales", [])) == 6)
    _check(failures, "localização canônica = pt-BR", localization.get("canonical_locale") == "pt-BR")
    _check(failures, "tradução parcial bloqueada", localization.get("strict_no_partial_translation") is True)
    _check(failures, "invariantes de tradução", invariants_ok)
    _check(failures, "UI traduz INICIAR", star.language.localization.static("INICIAR", "fr-FR") == "DÉMARRER")
    _check(failures, "comandos operacionais >= 4000", command_count() >= 4000)
    _check(failures, "catálogo total de voz > 1M", command_count() + THEMATIC_VOICE_VARIATIONS > 1_000_000)
    _check(failures, "conversa >= 5000", conversation_response_count() >= 5000)

    print("-" * 72)
    print("RESUMO")
    print(f"⚛️ Física: {physics.get('content_variations', 0)}")
    print(f"🧪 Química: {chemistry.get('content_variations', 0)}")
    print(f"🧭 Multidisciplinar: {multi.get('total_content_variations', 0)}")
    print(f"🚀 Factual legado combinado: {plus.get('combined_content_variations', 0)}")
    print(f"🧬 Currículo: {curriculum.get('themes', 0)} temas / {curriculum.get('unique_concepts', 0)} conceitos / {curriculum.get('total_new_addressable_contents', 0)} visões")
    print(f"🌍 Cultural: {cultural.get('religion_subjects', 0)} religiões/tradições + {cultural.get('magic_esotericism_subjects', 0)} magia/esoterismo / {cultural.get('total_addressable_contents', 0)} visões")
    print(f"🧠 MIND: {mind.get('capabilities', 0)} capacidades / {mind.get('support_contents_total', 0)} conteúdos")
    print(f"🛡️ Evolution: Guardian={evolution.get('guardian', {}).get('status')} | Goal={evolution.get('goal_engine', {}).get('status')} | RAG={evolution.get('semantic_rag', {}).get('backend')}")
    print(f"💾 M.drives: {mdrive_stats.get('mdrives', 0)} | local={mdrive_storage.get('local', 0)} legado={mdrive_storage.get('legacy', 0)} removível={mdrive_storage.get('removable', 0)} | entradas={mdrive_stats.get('entries', 0)}")
    print(f"🔬 Research: {', '.join(evolution.get('research', {}).get('providers', []))}")
    print(f"🧮 Simulações: {', '.join(evolution.get('simulation', {}).get('models', []))}")
    print(f"🌐 Idiomas: {language.get('language_families', 0)} famílias / {language.get('locale_profiles', 0)} perfis")
    print(f"🗣️ Voz: {command_count()} operacionais + {THEMATIC_VOICE_VARIATIONS} temáticas | conversa={conversation_response_count()}")

    if mdrive_stats.get("mdrives", 0) and not mdrive_stats.get("entries", 0):
        warnings.append("M.drives descobertos sem entradas utilizáveis; manifesto descoberto não equivale a conhecimento materializado.")
    if not language.get("full_dictionary_index_ready"):
        warnings.append("Dicionários completos não estão materializados em SQLite; seed/contexto continuam ativos.")
    neural = localization.get("neural", {})
    if not neural.get("installed"):
        warnings.append("Argos/modelos de tradução não instalados; tradução livre sem cobertura integral preserva o original.")
    if evolution.get("semantic_rag", {}).get("neural") is False:
        warnings.append("RAG semântico usa hashing local no boot base; Sentence Transformers é opcional.")
    if not evolution.get("ocr", {}).get("pymupdf_available"):
        warnings.append("PyMuPDF/Tesseract OCR não está materializado; PDFs textuais continuam via pypdf.")
    if not mind.get("store", {}).get("fts5_available"):
        warnings.append("SQLite FTS5 indisponível; RAG usa fallback textual.")

    if warnings:
        print("-" * 72)
        print("⚠️ AVISOS ESPERADOS / OPCIONAIS:")
        for warning in warnings:
            print(f"  - {warning}")

    if failures:
        print("-" * 72)
        print("❌ FALHAS CRÍTICAS:")
        for name, detail in failures:
            print(f"  - {name}: {detail}")
        raise SystemExit(1)

    print("✅ DIAGNÓSTICO GERAL CONCLUÍDO SEM FALHAS CRÍTICAS.")


if __name__ == "__main__":
    main()
