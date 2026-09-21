import importlib
import os
import sys
import threading
from pathlib import Path
from time import perf_counter

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
from core.offline_knowledge import OfflineKnowledgeService
from core.perception_runtime import PerceptionRuntime
from core.personal_integrations import PersonalIntegrations
from core.person_auth import LocalPersonAuthenticator
from core.router import Router
from core.security_agent import SecurityAgent
from core.skills import SkillRegistry
from core.star_core import StarCore
from core.star_identity import StarIdentity
from core.state import StarState
from core.tools import ToolRegistry, safe_math
from modules.automation import AgendaManager


class _LazyComponent:
    """Proxy thread-safe para serviços pesados carregados somente no primeiro uso.

    Preserva a API pública do serviço real via getattr e evita importar ou
    instanciar grandes catálogos durante a abertura da interface.
    """

    def __init__(self, label: str, module_name: str, class_name: str):
        self.label = str(label)
        self.module_name = str(module_name)
        self.class_name = str(class_name)
        self._instance = None
        self._load_seconds = None
        self._lock = threading.RLock()

    @property
    def loaded(self) -> bool:
        return self._instance is not None

    @property
    def load_seconds(self):
        return self._load_seconds

    def _load(self):
        if self._instance is not None:
            return self._instance
        with self._lock:
            if self._instance is None:
                started = perf_counter()
                module = importlib.import_module(self.module_name)
                component = getattr(module, self.class_name)
                self._instance = component()
                self._load_seconds = round(perf_counter() - started, 4)
        return self._instance

    def runtime_status(self) -> dict:
        return {
            "label": self.label,
            "loaded": self.loaded,
            "load_seconds": self._load_seconds,
            "target": f"{self.module_name}.{self.class_name}",
        }

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self._load(), name)

    def __bool__(self):
        # O Executive usa truthiness para saber se a capacidade existe.
        # Existir não deve forçar o carregamento do catálogo.
        return True


def _lazy_knowledge_components():
    return {
        "physics": _LazyComponent(
            "physics", "core.physics_knowledge_150k", "PhysicsKnowledgeEngine"
        ),
        "chemistry": _LazyComponent(
            "chemistry", "core.chemistry_knowledge_500k", "ChemistryKnowledgeEngine"
        ),
        "multidisciplinary": _LazyComponent(
            "multidisciplinary", "core.multidisciplinary_knowledge",
            "MultidisciplinaryKnowledgeEngine"
        ),
        "knowledge_plus": _LazyComponent(
            "knowledge_plus", "core.knowledge_expansion_15m",
            "KnowledgeExpansion15MEngine"
        ),
        "curriculum": _LazyComponent(
            "curriculum", "core.curriculum_knowledge", "CurriculumKnowledgeEngine"
        ),
    }


def _env_true(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return bool(default)
    return raw.strip().casefold() in {"1", "true", "yes", "on", "sim"}

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
    knowledge_components = _lazy_knowledge_components()
    physics = knowledge_components["physics"]
    chemistry = knowledge_components["chemistry"]
    multidisciplinary = knowledge_components["multidisciplinary"]
    knowledge_plus = knowledge_components["knowledge_plus"]
    curriculum = knowledge_components["curriculum"]
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

    # Conhecimento real offline: reutiliza o mesmo EpistemicStore/CognitiveStore e
    # o ledger físico do Grupo 3. A consulta factual ocorre antes dos matchers
    # temáticos legados, e Kiwix/ZIM é usado apenas localmente quando instalado.
    star.offline_knowledge = OfflineKnowledgeService(
        star.mind.store,
        real_materializer=star.group3.real_knowledge,
    )
    star.mind.offline_knowledge = star.offline_knowledge
    executive.offline_knowledge = star.offline_knowledge

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


def _print_startup_summary(star):
    """Resumo rápido sem carregar catálogos pesados apenas para imprimir métricas."""
    pack_stats = star.packs.stats()
    lazy_components = (
        star.physics,
        star.chemistry,
        star.multidisciplinary,
        star.knowledge_plus,
        star.curriculum,
    )
    loaded = sum(1 for component in lazy_components if component.loaded)

    print(f"🧠 Identidade: {star.get_name()}")
    print(f"👤 Criador: {star.get_creator()}")
    print("📚 Conhecimento interno: ATIVO")
    print("⚡ Catálogos científicos: ON-DEMAND "
          f"({loaded}/{len(lazy_components)} carregados no startup)")
    print("🔄 Cognição integrada: FAST/DELIBERATIVE + posição cognitiva")
    print("👁️ Percepção: providers locais/lazy; captura contínua=NÃO")
    print("🛡️ Guardian/limites: DEFAULT DENY + execução separada da cognição")
    print(f"📦 Knowledge Packs detectados: {pack_stats.get('packs', 0)}")
    print("🤖 IA externa:", "ATIVA" if EXTERNAL_AI_ENABLED else "DESATIVADA")
    print("🖥️ Interface: ATIVA")

    if _env_true("STAR_STARTUP_VERBOSE", False):
        _print_verbose_startup_stats(star)


def _print_verbose_startup_stats(star):
    """Diagnóstico opcional de startup; pode materializar serviços lazy."""
    physics_stats = star.physics.stats()
    chemistry_stats = star.chemistry.stats()
    multi_stats = star.multidisciplinary.stats()
    plus_stats = star.knowledge_plus.stats()
    curriculum_stats = star.curriculum.stats()
    mind_stats = star.mind.stats()
    group3_stats = star.group3.stats()
    offline_stats = star.offline_knowledge.stats()

    print("-" * 60)
    print("DIAGNÓSTICO DETALHADO DE STARTUP")
    print(f"⚛️ Física: {physics_stats['canonical_topics']} tópicos | "
          f"{physics_stats['content_variations']} variações")
    print(f"🧪 Química: {chemistry_stats['canonical_topics']} tópicos | "
          f"{chemistry_stats['content_variations']} variações")
    print(f"🧭 Multidisciplinar: {multi_stats['subjects']} matérias | "
          f"{multi_stats['canonical_nodes']} nós")
    print(f"🚀 Knowledge PLUS: +{plus_stats['added_content_variations']} endereçáveis")
    print(f"🧬 Currículo: {curriculum_stats['themes']} temas | "
          f"{curriculum_stats['unique_concepts']} conceitos")
    print(f"🧠 MIND: {mind_stats['capabilities']} capacidades | "
          f"{mind_stats['canonical_nodes_total']} nós")
    print(f"🌐 Grupo 3: arquivos={group3_stats['semantic_files']['vector_backend']} | "
          f"offline={offline_stats['categories']} categorias")
    for component in (
        star.physics, star.chemistry, star.multidisciplinary,
        star.knowledge_plus, star.curriculum,
    ):
        status = component.runtime_status()
        print(f"  • {status['label']}: loaded={status['loaded']} "
              f"tempo={status['load_seconds']}s")
    print("-" * 60)


def main():
    print("=" * 60)
    print(f"⭐ INICIALIZANDO STAR V{VERSION} — MODO OFFLINE-FIRST")
    print("=" * 60)
    star = create_star()
    _print_startup_summary(star)

    gateway = _start_device_gateway(star)
    star.proactivity.start()
    try:
        # Import tardio: CLI/testes que só usam create_star não carregam Tk/Pillow.
        from gui.localized_app import LocalizedStarApp

        LocalizedStarApp(brain=star).run()
    finally:
        star.proactivity.stop()
        if gateway is not None:
            gateway.stop()

if __name__ == "__main__":
    main()
