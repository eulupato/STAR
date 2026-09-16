"""Diagnóstico geral e leve da instalação da STAR V1.9 + MIND V2 alpha.

Não carrega o Chatterbox pesado nem força o carregamento do modelo conversacional
local. Para síntese real use DIAGNOSTICO_VOZ.bat.
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
    "config", "core.star_identity", "core.internal_knowledge", "core.physics_knowledge",
    "core.physics_topics_extended", "core.physics_knowledge_150k", "core.chemistry_topics_01",
    "core.chemistry_topics_20", "core.chemistry_knowledge_500k", "core.multidisciplinary_taxonomy",
    "core.multidisciplinary_knowledge", "core.knowledge_expansion_15m", "core.curriculum_taxonomy",
    "core.curriculum_knowledge", "core.cognitive_catalog", "database.cognitive_store", "core.labs",
    "core.mind", "core.thematic_voice", "core.language_catalog", "core.offline_dictionary",
    "core.global_localization", "core.language_manager", "core.router", "core.executive", "core.star_core",
    "core.commands", "core.conversation", "core.natural_interaction", "core.weather", "core.islands",
    "core.memory", "core.emotion", "core.avatar", "core.knowledge_registry", "core.cure", "core.math_engine",
    "modules.computer_control", "database.database", "database.memory", "voice.manager", "voice.audio_input", "gui.app",
    "core.memory_continuity", "core.attention_salience", "core.internal_models", "core.social_cognition",
    "core.affective_personality", "core.reasoning_simulation", "core.planning_decision", "core.metacognition",
    "core.learning_evolution", "core.knowledge_integration", "core.global_workspace", "core.mind_loop",
    "core.multimodal_perception", "core.people_entities", "core.body_proprioception", "core.cognitive_integration",
    "core.block_knowledge_catalog", "core.cognitive_maintenance", "core.autonomy_limits",
    "core.cfc_benchmark", "core.consciousness_frontier",
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
    curriculum_stats = star.curriculum.stats()
    mind_stats = star.mind.stats()
    language_stats = star.language.stats()
    localization_stats = language_stats.get("global_localization", {})
    voice_theme_stats = thematic_voice_stats()

    plus_boundaries_ok = True
    for domain in plus_stats.get("domain_keys", []):
        first = star.knowledge_plus.content_id(domain, 0, 0)
        last = star.knowledge_plus.content_id(domain, 999, 999)
        plus_boundaries_ok = plus_boundaries_ok and first.endswith("-0000001") and last.endswith("-1000000")

    curriculum_boundaries_ok = False
    try:
        first_theme = star.curriculum.materialize_theme(1, 1)["id"]
        last_theme = star.curriculum.materialize_theme(56, 1_000_000)["id"]
        first_concept = star.curriculum.materialize_concept(1, 1)["id"]
        last_concept = star.curriculum.materialize_concept(curriculum_stats["unique_concepts"], 1_000_000)["id"]
        curriculum_boundaries_ok = (
            first_theme == "CURRT-001-0000001"
            and last_theme == "CURRT-056-1000000"
            and first_concept.endswith("-0000001")
            and last_concept.endswith("-1000000")
        )
    except (KeyError, ValueError, IndexError):
        curriculum_boundaries_ok = False

    cognitive_boundaries_ok = True
    for theme in mind_stats.get("capability_keys", []):
        first = star.mind.catalog.content_id(theme, 0, 0)
        last = star.mind.catalog.content_id(theme, 999, 999)
        cognitive_boundaries_ok = cognitive_boundaries_ok and first.endswith("-0000001") and last.endswith("-1000000")

    invariant_sample = "CHEMX-0000042 9.81 m/s https://example.org `x = 2 + 2`"
    localized_sample = star.language.translate_with_report(invariant_sample, "en-US", "pt-BR")
    invariants_preserved = all(
        token in localized_sample.text
        for token in ("CHEMX-0000042", "9.81 m/s", "https://example.org", "`x = 2 + 2`")
    )

    b24_stats = star.mind_loop.stats()
    b25_stats = star.multimodal_perception.stats()
    b26_stats = star.people_entities.stats()
    b27_stats = star.body_proprioception.stats()
    natural_stats = star.natural_interaction.stats()
    b32_stats = star.cognitive_maintenance.stats()
    b33_stats = star.autonomy_limits.stats()
    b34_stats = star.cfc.stats()
    b35_stats = star.cfc97.stats()
    b36_stats = star.consciousness_frontier.stats()
    capacity_contract = star.cognitive_maintenance.capacity_contract()

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
        ("conhecimento combinado legado = 22150000", plus_stats.get("combined_content_variations") == 22_150_000),
        ("IDs PLUS preservam limites 1..1000000", plus_boundaries_ok),
        ("currículo = 56 temas", curriculum_stats.get("themes") == 56),
        ("currículo >400 conceitos únicos", curriculum_stats.get("unique_concepts", 0) > 400),
        ("currículo deduplica menções", curriculum_stats.get("deduplicated_mentions", 0) > 0),
        ("currículo = 1M por tema", curriculum_stats.get("variations_per_theme") == 1_000_000),
        ("currículo = 1M por conceito", curriculum_stats.get("variations_per_concept") == 1_000_000),
        ("currículo total coerente", curriculum_stats.get("total_new_addressable_contents") == (curriculum_stats.get("themes", 0) + curriculum_stats.get("unique_concepts", 0)) * 1_000_000),
        ("IDs currículo preservam limites 1..1000000", curriculum_boundaries_ok),
        ("MIND = 15 capacidades", mind_stats.get("capabilities") == 15),
        ("MIND = 1000000 conteúdos/capacidade", mind_stats.get("support_contents_per_capability") == 1_000_000),
        ("MIND = 15000000 conteúdos operacionais", mind_stats.get("support_contents_total") == 15_000_000),
        ("MIND = 15000 nós canônicos", mind_stats.get("canonical_nodes_total") == 15_000),
        ("IDs MIND preservam limites 1..1000000", cognitive_boundaries_ok),
        ("SymPy disponível", bool(mind_stats.get("math", {}).get("sympy_available"))),
        ("MIND responde status", "STAR MIND" in str(star.process("status mind"))),
        ("MIND planeja", "Plano:" in str(star.process("planeje criar um software simples"))),
        ("MIND deriva", "2*x" in str(star.process("derive x^2 em x"))),
        ("B24 Mind Loop integrado", b24_stats.get("catalog", {}).get("addressable_contents") == 1_000_000_000),
        ("B24 não executa ações", b24_stats.get("policy", {}).get("action_stage_executes_tools") is False),
        ("B25 percepção multimodal = 1B", b25_stats.get("catalog", {}).get("addressable_contents") == 1_000_000_000),
        ("B25 Sensor Fusion ativo", b25_stats.get("sensor_fusion") is True),
        ("B25 não fabrica observações", b25_stats.get("fabricates_observations") is False),
        ("B26 pessoas = 1B", b26_stats.get("addressable_contents") == 1_000_000_000),
        ("B26 reconhecimento != autenticação", b26_stats.get("recognition_is_authentication") is False),
        ("B26 perfil persistente", b26_stats.get("profile_ingestion") is True),
        ("B26 sem biometria bruta por padrão", b26_stats.get("raw_biometric_storage_by_default") is False),
        ("B27 corpo = 1B", b27_stats.get("addressable_contents") == 1_000_000_000),
        ("B27 corpo é endpoint", b27_stats.get("body_is_endpoint") is True),
        ("B27 sem atuação direta", b27_stats.get("direct_actuation") is False),
        ("B25 conectado ao B23", star.global_workspace.perception_provider is star.multimodal_perception),
        ("B25 conectado ao B24", star.mind_loop.perception_provider is star.multimodal_perception),
        ("B27 conectado ao B25", star.body_proprioception.perception is star.multimodal_perception),
        ("interação natural ativa", natural_stats.get("status") == "active-integrated"),
        ("interação natural bounded", 0 < natural_stats.get("turn_buffer_limit", 0) <= 64),
        ("conversa usa runtime único", star.conversation.natural_interaction is star.natural_interaction),
        ("executive usa runtime único", star.executive.natural_interaction is star.natural_interaction),
        ("modelo de expressão não é STAR", natural_stats.get("model_is_star") is False),
        ("modelo de expressão não decide fatos", natural_stats.get("model_decides_facts") is False),
        ("modelo de expressão não concede permissões", natural_stats.get("model_grants_permissions") is False),
        ("B32 manutenção = 1B", b32_stats.get("catalog", {}).get("addressable_contents") == 1_000_000_000),
        ("B32 bounded", b32_stats.get("bounded_windows") is True),
        ("B32 não destrutivo por padrão", b32_stats.get("destructive_by_default") is False),
        ("B33 autonomia = 1B", b33_stats.get("catalog", {}).get("addressable_contents") == 1_000_000_000),
        ("B33 reutiliza B01", star.autonomy_limits.boundary is star.foundations.boundary),
        ("B33 governa dispatcher", star.agents.autonomy_limits is star.autonomy_limits),
        ("B33 reconhecimento != autenticação", b33_stats.get("recognition_is_authentication") is False),
        ("B34 CFC = 1B", b34_stats.get("catalog", {}).get("addressable_contents") == 1_000_000_000),
        ("B34 CFC = 15 dimensões", len(b34_stats.get("dimensions", ())) == 15),
        ("B34 não se autoavalia", b34_stats.get("auto_grading") is False),
        ("B35 CFC-97 = 1B", b35_stats.get("catalog", {}).get("addressable_contents") == 1_000_000_000),
        ("B35 target funcional = 0.97", b35_stats.get("target") == 0.97),
        ("B35 inicia não certificado", b35_stats.get("passed") is None),
        ("B36 consciência = 1B", b36_stats.get("catalog", {}).get("addressable_contents") == 1_000_000_000),
        ("B36 sem autoafirmação", b36_stats.get("automatic_consciousness_claim") is False),
        ("B36 consciência STAR não estabelecida", b36_stats.get("self_consciousness_status") == "not_established"),
        ("voz temática = 1000000", voice_theme_stats.get("variations") == 1000000),
        ("idiomas = 5 famílias", language_stats.get("language_families") == 5),
        ("perfis de idioma = 6", language_stats.get("locale_profiles") == 6),
        ("expressões = 500000", language_stats.get("total_semantic_contents") == 500000),
        ("100k expressões por idioma", language_stats.get("contents_per_language") == 100000),
        (">=5 dicionários/fontes por idioma", min(language_stats.get("dictionary_sources", {}).values(), default=0) >= 5),
        ("localização global = 6 locales", len(localization_stats.get("supported_locales", [])) == 6),
        ("localização canônica = pt-BR", localization_stats.get("canonical_locale") == "pt-BR"),
        ("tradução parcial bloqueada", localization_stats.get("strict_no_partial_translation") is True),
        ("invariantes preservados na tradução", invariants_preserved),
        ("catálogo UI traduz INICIAR", star.language.localization.static("INICIAR", "fr-FR") == "DÉMARRER"),
        ("catálogo operacional de voz >= 4000", command_count() >= 4000),
        ("catálogo total de voz > 1000000", command_count() + THEMATIC_VOICE_VARIATIONS > 1000000),
        ("catálogo conversacional fallback >= 5000", conversation_response_count() >= 5000),
    ]
    for name, ok in checks:
        print(("🟢 " if ok else "🔴 ") + name)
        if not ok:
            failures.append((name, "check failed"))

    print(f"⚛️ Física local: {physics_stats.get('canonical_topics', 0)} tópico(s), {physics_stats.get('content_variations', 0)} conteúdo(s) variável(is)")
    print(f"🧪 Química local: {chemistry_stats.get('canonical_topics', 0)} tópico(s), {chemistry_stats.get('domains', 0)} domínio(s), {chemistry_stats.get('content_variations', 0)} conteúdo(s) variável(is)")
    print(f"🧭 Multidisciplinar: {multi_stats.get('subjects', 0)} matéria(s), {multi_stats.get('canonical_nodes', 0)} nó(s), {multi_stats.get('total_content_variations', 0)} conteúdo(s) variável(is)")
    print(f"🚀 Knowledge PLUS: {plus_stats.get('domains', 0)} domínio(s), +{plus_stats.get('added_content_variations_per_domain', 0)} por domínio, +{plus_stats.get('added_content_variations', 0)} novos | combinado legado={plus_stats.get('combined_content_variations', 0)}")
    print(
        "🧬 Currículo: "
        f"{curriculum_stats.get('themes', 0)} temas | "
        f"{curriculum_stats.get('raw_topic_mentions', 0)} menções brutas -> "
        f"{curriculum_stats.get('unique_concepts', 0)} conceitos únicos | "
        f"{curriculum_stats.get('deduplicated_mentions', 0)} duplicações consolidadas | "
        f"{curriculum_stats.get('total_new_addressable_contents', 0)} visões/conteúdos curriculares endereçáveis"
    )
    print(f"🧠 MIND alpha: {mind_stats.get('capabilities', 0)} capacidades, {mind_stats.get('canonical_nodes_total', 0)} nós canônicos, {mind_stats.get('support_contents_total', 0)} conteúdos operacionais | FTS5={'SIM' if mind_stats.get('store', {}).get('fts5_available') else 'fallback textual'}")
    print(f"🧠 B24 Mind Loop: {b24_stats.get('catalog', {}).get('addressable_contents', 0)} representações | ação automática=NÃO")
    print(f"👁️ B25 Percepção: {b25_stats.get('catalog', {}).get('addressable_contents', 0)} padrões | Sensor Fusion={'SIM' if b25_stats.get('sensor_fusion') else 'NÃO'}")
    print(f"👥 B26 Pessoas: {b26_stats.get('addressable_contents', 0)} representações | perfil persistente=SIM | reconhecimento ≠ autenticação")
    print(f"🤖 B27 Corpo: {b27_stats.get('addressable_contents', 0)} representações | endpoint={'SIM' if b27_stats.get('body_is_endpoint') else 'NÃO'} | atuação direta=NÃO")
    print(
        "💬 Interação natural: "
        f"{natural_stats.get('status')} | contexto={natural_stats.get('turn_buffer_limit')} turnos bounded | "
        f"modelo local={natural_stats.get('local_llm_model')} opcional/lazy | modelo≠STAR"
    )
    print(f"🧹 B32 Manutenção: {b32_stats.get('catalog', {}).get('addressable_contents', 0)} representações | bounded=SIM | destrutivo por padrão=NÃO")
    print(f"🛡️ B33 Autonomia: {b33_stats.get('catalog', {}).get('addressable_contents', 0)} situações | autoridade=B01 | default deny=SIM")
    print(f"🧪 B34 CFC: {b34_stats.get('catalog', {}).get('addressable_contents', 0)} situações | {len(b34_stats.get('dimensions', ())) } dimensões | auto-score=NÃO")
    print(f"🎯 B35 CFC-97: target={b35_stats.get('target')} | blocos 1B registrados={b35_stats.get('registered_1b_blocks', 0)}/36 | certificado=NÃO")
    print(f"🧠 B36 Consciência: {b36_stats.get('catalog', {}).get('addressable_contents', 0)} conteúdos de pesquisa | STAR={b36_stats.get('self_consciousness_status')}")
    print(f"🌐 Idiomas: {language_stats.get('language_families', 0)} famílias / {language_stats.get('locale_profiles', 0)} perfis | {language_stats.get('total_semantic_contents', 0)} conteúdos de expressão")
    neural_stats = localization_stats.get("neural", {})
    print(
        "🌍 Localização global: "
        f"{len(localization_stats.get('supported_locales', []))} locales | "
        f"canônico={localization_stats.get('canonical_locale', '?')} | "
        f"UI fixa={localization_stats.get('static_strings', 0)} superfícies | "
        f"neural={'SIM' if neural_stats.get('installed') else 'opcional/não instalado'}"
    )
    print("📚 Dicionários configurados: " + ", ".join(f"{k}={v}" for k, v in sorted(language_stats.get("dictionary_sources", {}).items())) + f" | índice completo={'SIM' if language_stats.get('full_dictionary_index_ready') else 'NÃO (seed ativo)'}")
    print(f"📦 Knowledge Packs: {pack_stats.get('packs', 0)} pack(s), {pack_stats.get('entries', 0)} entrada(s) carregada(s)")
    if pack_stats.get("packs", 0) and not pack_stats.get("entries", 0):
        warnings.append("Knowledge Packs foram descobertos, mas nenhuma entrada de conhecimento foi carregada; descoberta de manifesto não equivale a conteúdo utilizável.")
    if capacity_contract.get("missing"):
        warnings.append(
            "Contrato 1B B01..B36: blocos ainda sem namespace/engine definida: "
            + ", ".join(capacity_contract["missing"])
            + ". Eles não foram fabricados apenas para fechar a numeração."
        )
    if capacity_contract.get("invalid_capacity"):
        warnings.append(
            "Namespaces registrados fora da capacidade lógica de 1B: "
            + ", ".join(capacity_contract["invalid_capacity"])
        )
    if not language_stats.get("full_dictionary_index_ready"):
        warnings.append("Dicionários completos ainda não foram materializados em SQLite; tradução contextual e léxico seed funcionam, mas vocabulário arbitrário pode não ser encontrado.")
    if not neural_stats.get("installed"):
        warnings.append("Argos Translate/modelos não estão instalados; textos livres sem cobertura integral são preservados no original, sem tradução parcial.")
    if not mind_stats.get("store", {}).get("fts5_available"):
        warnings.append("SQLite FTS5 indisponível neste build; o RAG usa busca textual fallback, com menor qualidade de ranking.")

    print(f"🗣️ Voz: {command_count()} operacionais + {THEMATIC_VOICE_VARIATIONS} temáticas = {command_count() + THEMATIC_VOICE_VARIATIONS} variações | 💬 fallback conversacional: {conversation_response_count()}")

    from voice.manager import VoiceManager

    voice = VoiceManager()
    print("-" * 64)
    print("VOZ (sem carregar modelos)")
    print(f"Modo: {voice.mode}")
    print(f"STT instalado: {'SIM' if voice.stt_configured else 'NÃO'}")
    print(f"Referência resolvida: {voice.reference_voice if getattr(voice, 'reference_voice', None) else 'NÃO'}")

    settings_path = ROOT / "config" / "user_settings.json"
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
