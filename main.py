import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import (
    DEVICE_GATEWAY_ENABLED,
    DEVICE_GATEWAY_HOST,
    DEVICE_GATEWAY_PORT,
    EXTERNAL_AI_ENABLED,
    VERSION,
)
from core.autonomy_limits import AutonomyLimits
from core.body_proprioception import BodyActuationExecutor, TcpJsonBodyEndpoint
from core.cfc_benchmark import CFC97, FunctionalCognitiveBenchmark
from core.cognitive_integration import CognitiveIntegration
from core.cognitive_maintenance import CognitiveMaintenance
from core.consciousness_frontier import ConsciousnessResearchFrontier
from core.device_sensors import DeviceSensorHub
from core.cure import CureSystem
from core.executive import Executive
from core.home_automation import HomeAutomationService
from core.internal_knowledge import StarInternalKnowledge
from core.knowledge_packs import KnowledgePackManager
from core.knowledge_research_documents import Group3KnowledgeServices, IntelligentProactiveScheduler
from core.natural_interaction import NaturalInteraction
from core.os_sandbox import OSSandbox
from core.perception_runtime import PerceptionRuntime
from core.personal_integrations import PersonalIntegrations
from core.person_auth import LocalPersonAuthenticator
from core.physics_knowledge_150k import PhysicsKnowledgeEngine
from core.chemistry_knowledge_500k import ChemistryKnowledgeEngine
from core.multidisciplinary_knowledge import MultidisciplinaryKnowledgeEngine
from core.knowledge_expansion_15m import KnowledgeExpansion15MEngine
from core.curriculum_knowledge import CurriculumKnowledgeEngine
from core.router import Router
from core.security_agent import SecurityAgent
from core.skills import SkillRegistry
from core.star_core import StarCore
from core.star_identity import StarIdentity
from core.state import StarState
from core.tools import ToolRegistry, safe_math
from gui.localized_app import LocalizedStarApp
from modules.automation import AgendaManager


def _configure_optional_body_endpoint(star):
    host = str(os.getenv("STAR_BODY_ENDPOINT_HOST", "")).strip()
    port = str(os.getenv("STAR_BODY_ENDPOINT_PORT", "")).strip()
    if not host and not port:
        return None
    if not host or not port:
        raise ValueError("STAR_BODY_ENDPOINT_HOST e STAR_BODY_ENDPOINT_PORT devem ser definidos juntos")
    endpoint = TcpJsonBodyEndpoint(
        host, int(port),
        timeout=float(os.getenv("STAR_BODY_ENDPOINT_TIMEOUT", "2.0")),
        token=os.getenv("STAR_BODY_ENDPOINT_TOKEN") or None,
    )
    star.body_proprioception.attach_endpoint(endpoint)
    return endpoint


def create_star():
    identity = StarIdentity()
    knowledge = StarInternalKnowledge(identity)
    physics = PhysicsKnowledgeEngine()
    chemistry = ChemistryKnowledgeEngine()
    multidisciplinary = MultidisciplinaryKnowledgeEngine()
    knowledge_plus = KnowledgeExpansion15MEngine()
    curriculum = CurriculumKnowledgeEngine()
    packs = KnowledgePackManager(ROOT / "knowledge" / "packs", auto_removable=True)
    state = StarState()
    router = Router(internal_knowledge=knowledge)
    executive = Executive(
        model_manager=None,
        internal_knowledge=knowledge,
        knowledge_packs=packs,
        physics_knowledge=physics,
        chemistry_knowledge=chemistry,
        multidisciplinary_knowledge=multidisciplinary,
        knowledge_expansion=knowledge_plus,
        curriculum_knowledge=curriculum,
    )
    star = StarCore(
        router=router,
        executive=executive,
        state=state,
        identity=identity,
        internal_knowledge=knowledge,
    )

    # Integração cognitiva sobre a STAR já construída. Não cria outro Brain,
    # memória, planner ou personalidade: conecta o Router/Executive ao B12-B24.
    cognition = CognitiveIntegration(star)
    star.cognitive_integration = cognition
    router.cognitive_integration = cognition
    executive.cognitive_integration = cognition

    # Interação natural é uma camada de continuidade + expressão, não um cérebro.
    star.natural_interaction = NaturalInteraction(star)
    star.mind.natural_interaction = star.natural_interaction
    star.conversation.natural_interaction = star.natural_interaction
    cognition.natural_interaction = star.natural_interaction
    executive.natural_interaction = star.natural_interaction

    def _sync_active_person(person):
        star.natural_interaction.active_person_id = person.get("person_id")
        star.natural_interaction.active_person_name = person.get("name")

    star.people_entities.on_active_person = _sync_active_person

    # Grupo 1: providers perceptivos reais continuam subordinados ao B25/B26.
    star.perception_runtime = PerceptionRuntime(star)
    star.mind.perception_runtime = star.perception_runtime
    star.agents.attach_perception_runtime(star.perception_runtime)

    star.person_authenticator = LocalPersonAuthenticator(ROOT / "runtime" / "security" / "person_credentials.json")
    star.mind.person_authenticator = star.person_authenticator

    # Grupo 3: amplia o RAG existente e conecta web, OCR, Office, índice semântico,
    # dicionários materializados e atualização segura sem criar outro cérebro/banco.
    star.group3 = Group3KnowledgeServices(
        star.mind.store,
        star.mind.growth,
        network_enabled_provider=lambda: bool(star.network_enabled),
    )
    star.mind.rag = star.group3.rag
    star.mind.group3 = star.group3

    # Grupo 4: o CodeLab preserva o runner restrito legado, mas código não
    # confiável só usa run_sandboxed quando um backend real já está disponível.
    star.os_sandbox = OSSandbox()
    star.mind.code.attach_sandbox(star.os_sandbox)
    star.mind.os_sandbox = star.os_sandbox

    # Grupo 2 + Grupo 3: a mesma agenda/star.db ganha política de relevância.
    # create_star constrói, mas não inicia thread; main controla o lifecycle.
    star.agenda = AgendaManager()
    star.proactivity = IntelligentProactiveScheduler(
        star.agenda,
        poll_seconds=float(os.getenv("STAR_PROACTIVE_POLL_SECONDS", "1.0")),
        relevance_threshold=float(os.getenv("STAR_NOTIFICATION_RELEVANCE", "0.55")),
    )
    star.mind.agenda = star.agenda
    star.mind.proactivity = star.proactivity

    # Sensores físicos autenticados dos endpoints entram no B25/B27. O hub não
    # simula leituras ausentes e telemetria jamais concede autorização.
    star.device_sensors = DeviceSensorHub(star)
    star.mind.device_sensors = star.device_sensors

    # B27 calcula/observa. Atuação é objeto separado e continua sem rota automática
    # pelo chat. Um endpoint físico só é anexado quando configurado explicitamente.
    star.body_executor = BodyActuationExecutor(star.body_proprioception)
    star.mind.body_executor = star.body_executor
    star.body_endpoint = _configure_optional_body_endpoint(star)

    # BLOCO 32: manutenção bounded sobre os stores, memória e grafo oficiais.
    star.cognitive_maintenance = CognitiveMaintenance(
        star.knowledge,
        memory_continuity=star.memory_continuity,
        epistemics=star.mind.epistemics,
        graph=star.mind.graph,
        self_improvement=star.mind.self_improvement,
    )
    star.mind.cognitive_maintenance = star.cognitive_maintenance

    # BLOCO 33: exatamente a fronteira operacional B01.
    star.autonomy_limits = AutonomyLimits(
        star.knowledge,
        operational_boundary=star.foundations.boundary,
    )
    star.mind.autonomy_limits = star.autonomy_limits
    star.agents.autonomy_limits = star.autonomy_limits

    # Grupo 4: Guardian/CURA, segurança, casa e integrações pessoais reutilizam
    # B01/B33 e star.db. Nenhum provider guarda token/senha no banco.
    star.cure = CureSystem(
        sandbox=star.os_sandbox,
        autonomy_limits=star.autonomy_limits,
    )
    star.security_agent = SecurityAgent(
        star=star,
        root=ROOT,
        sandbox=star.os_sandbox,
    )
    star.home_automation = HomeAutomationService(
        autonomy_limits=star.autonomy_limits,
        network_enabled_provider=lambda: bool(star.network_enabled),
    )
    star.personal_integrations = PersonalIntegrations(
        agenda=star.agenda,
        autonomy_limits=star.autonomy_limits,
        network_enabled_provider=lambda: bool(star.network_enabled),
    )
    star.mind.cure = star.cure
    star.mind.security_agent = star.security_agent
    star.mind.home_automation = star.home_automation
    star.mind.personal_integrations = star.personal_integrations

    star.cfc = FunctionalCognitiveBenchmark(
        star.knowledge,
        self_improvement=star.mind.self_improvement,
    )
    star.mind.cfc = star.cfc
    star.cfc97 = CFC97(
        star.knowledge,
        benchmark=star.cfc,
        self_improvement=star.mind.self_improvement,
    )
    star.mind.cfc97 = star.cfc97

    star.consciousness_frontier = ConsciousnessResearchFrontier(
        star.knowledge,
        self_model=star.self_model,
        metacognition=star.metacognition,
    )
    star.mind.consciousness_frontier = star.consciousness_frontier

    # O mesmo AgentManager delega handles. Grupo 3 só responde comandos explícitos;
    # execução física não é registrada como handler conversacional.
    star.agents.attach_system_handlers(
        star.agenda,
        star.group3,
        star.cure,
        star.security_agent,
        star.home_automation,
        star.personal_integrations,
        star.cognitive_maintenance,
        star.autonomy_limits,
        star.cfc97,
        star.consciousness_frontier,
    )

    star.skills = SkillRegistry()
    star.tools = ToolRegistry()
    star.tools.register("math", safe_math, True, "Cálculo matemático offline")
    star.packs = packs
    star.physics = physics
    star.chemistry = chemistry
    star.multidisciplinary = multidisciplinary
    star.knowledge_plus = knowledge_plus
    star.curriculum = curriculum
    return star


def _device_gateway_requested():
    raw = os.getenv("STAR_DEVICE_GATEWAY")
    if raw is None:
        return bool(DEVICE_GATEWAY_ENABLED)
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _start_device_gateway(star):
    if not _device_gateway_requested():
        return None

    from core.device_gateway import DeviceGateway

    gateway = DeviceGateway(
        star=star,
        host=os.getenv("STAR_DEVICE_HOST", DEVICE_GATEWAY_HOST),
        port=int(os.getenv("STAR_DEVICE_PORT", str(DEVICE_GATEWAY_PORT))),
        runtime_dir=ROOT / "runtime" / "oni",
        manifest_path=ROOT / "STAR_MANIFEST.json",
    ).start()
    star.device_gateway = gateway
    print(f"📡 STAR Device Gateway: {gateway.url}")
    print(f"🔐 Código de pareamento desta sessão: {gateway.pairing_code}")
    print(f"🔄 Runtime adaptativo: {gateway.runtime.revision}")
    print("🛡️ Gateway disponível somente quando ativado explicitamente; mantenha-o na LAN privada.")
    return gateway


def main():
    print("=" * 60)
    print(f"⭐ INICIALIZANDO STAR V{VERSION} — MODO OFFLINE-FIRST")
    print("=" * 60)
    star = create_star()
    pack_stats = star.packs.stats()
    storage_stats = star.packs.storage_stats()
    physics_stats = star.physics.stats()
    chemistry_stats = star.chemistry.stats()
    multi_stats = star.multidisciplinary.stats()
    plus_stats = star.knowledge_plus.stats()
    curriculum_stats = star.curriculum.stats()
    mind_stats = star.mind.stats()
    cfc97_stats = star.cfc97.stats()
    natural_stats = star.natural_interaction.stats()
    body_stats = star.body_proprioception.stats()
    group3_stats = star.group3.stats()
    real_knowledge_stats = group3_stats.get("real_knowledge", {})
    sandbox_stats = star.os_sandbox.stats()
    home_stats = star.home_automation.stats()
    personal_stats = star.personal_integrations.stats()
    print(f"🧠 Identidade: {star.get_name()}")
    print(f"👤 Criador: {star.get_creator()}")
    print("📚 Conhecimento interno: ATIVO")
    print(f"⚛️ Física local: {physics_stats['canonical_topics']} tópicos | {physics_stats['content_variations']} conteúdos variáveis")
    print(f"🧪 Química local: {chemistry_stats['canonical_topics']} tópicos | {chemistry_stats['content_variations']} conteúdos variáveis")
    print(f"🧭 Biblioteca multidisciplinar: {multi_stats['subjects']} matérias | {multi_stats['canonical_nodes']} nós | {multi_stats['total_content_variations']} conteúdos variáveis")
    print(f"🚀 Knowledge PLUS: +{plus_stats['added_content_variations_per_domain']} por domínio | +{plus_stats['added_content_variations']} novos | {plus_stats['combined_content_variations']} conteúdos de conhecimento combinados")
    print(f"🧬 Currículo canônico: {curriculum_stats['themes']} temas | {curriculum_stats['unique_concepts']} conceitos únicos | {curriculum_stats['deduplicated_mentions']} menções duplicadas consolidadas | {curriculum_stats['total_new_addressable_contents']} conteúdos endereçáveis")
    print(f"🧠 STAR MIND alpha: {mind_stats['capabilities']} capacidades | {mind_stats['canonical_nodes_total']} nós cognitivos | {mind_stats['support_contents_total']} conteúdos operacionais endereçáveis")
    print(
        "🧱 Conhecimento real materializado: "
        f"{real_knowledge_stats.get('materialized_real_total', 0)} registros físicos | "
        "meta=1.000.000.000 por namespace | variações lógicas não contam"
    )
    print("🔄 Cognição integrada: FAST/DELIBERATIVE + posição cognitiva")
    print(f"💬 Interação natural: ATIVA | contexto multi-turn bounded | modelo local={natural_stats['local_llm_model']} (autodetectável/opcional/lazy)")
    print("👁️ Percepção Grupo 1: B25 conectado | visão/tela/áudio lazy | nenhum polling contínuo")
    print("🛰️ Sensores Grupo 2: GPS/IMU/saúde/medição via endpoints físicos autenticados; simulação=NÃO")
    print(f"🤖 B27: FK/IK ATIVOS | corpo físico={'CONECTADO' if body_stats['endpoint_available'] else 'NÃO CONFIGURADO'} | atuação direta=NÃO")
    print("⏰ Agenda/proatividade: star.db + relevância inteligente + scheduler de eventos | execução automática=NÃO")
    print(f"🌐 Grupo 3: web com proveniência | RAG Office/PDF | OCR={'ATIVO' if group3_stats['documents']['ocr']['available'] else 'OPCIONAL/TESSERACT AUSENTE'} | busca de arquivos={group3_stats['semantic_files']['vector_backend']}")
    print(f"🛡️ Grupo 4 Guardian: CURA controlada | Security read-only | sandbox={'ATIVO' if sandbox_stats['ready'] else 'INDISPONÍVEL/FAIL-CLOSED'}")
    print(f"🏠 Home: Home Assistant={'CONFIGURADO' if home_stats['configured'] else 'NÃO CONFIGURADO'} | confirmação física=2 ETAPAS")
    print(f"📨 Integrações pessoais: email={'SIM' if personal_stats['email_read'] or personal_stats['email_send'] else 'NÃO'} | mensagens={'SIM' if personal_stats['messaging'] else 'NÃO'} | CalDAV={'SIM' if personal_stats['calendar_sync'] else 'NÃO'} | envio automático=NÃO")
    print("🔐 Autenticação de pessoas: challenge local separado de reconhecimento; permissão=NÃO")
    print("🧹 Manutenção cognitiva B32: BOUNDED/ON-DEMAND")
    print("🛡️ Limites de autonomia B33: B01 BOUNDARY / DEFAULT DENY")
    print(f"🧪 CFC/CFC-97 B34-B35: {len(star.cfc.stats()['dimensions'])} dimensões | {cfc97_stats['registered_1b_blocks']}/36 blocos 1B registrados | NÃO CERTIFICADO")
    print("🧠 Consciência B36: FRONTEIRA DE PESQUISA / STATUS DA STAR NÃO ESTABELECIDO")
    print("🧩 Skills: PREPARADAS")
    print("🛠️ Ferramentas: ATIVAS (matemática offline + MIND experimental)")
    print(f"📦 Knowledge Packs detectados: {pack_stats['packs']}")
    print(f"💾 Packs locais: {storage_stats['local']} | removíveis: {storage_stats['removable']}")
    print(f"📄 Entradas de conhecimento carregadas: {pack_stats['entries']}")
    print("🤖 IA externa:", "ATIVA" if EXTERNAL_AI_ENABLED else "DESATIVADA")
    print("🖥️ Interface: ATIVA")

    gateway = _start_device_gateway(star)
    star.proactivity.start()
    try:
        LocalizedStarApp(brain=star).run()
    finally:
        star.proactivity.stop()
        if gateway is not None:
            gateway.stop()


if __name__ == "__main__":
    main()
