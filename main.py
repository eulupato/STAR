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
from core.cfc_benchmark import CFC97, FunctionalCognitiveBenchmark
from core.cognitive_integration import CognitiveIntegration
from core.cognitive_maintenance import CognitiveMaintenance
from core.consciousness_frontier import ConsciousnessResearchFrontier
from core.executive import Executive
from core.internal_knowledge import StarInternalKnowledge
from core.knowledge_packs import KnowledgePackManager
from core.physics_knowledge_150k import PhysicsKnowledgeEngine
from core.chemistry_knowledge_500k import ChemistryKnowledgeEngine
from core.multidisciplinary_knowledge import MultidisciplinaryKnowledgeEngine
from core.knowledge_expansion_15m import KnowledgeExpansion15MEngine
from core.curriculum_knowledge import CurriculumKnowledgeEngine
from core.router import Router
from core.skills import SkillRegistry
from core.star_core import StarCore
from core.star_identity import StarIdentity
from core.state import StarState
from core.tools import ToolRegistry, safe_math
from gui.localized_app import LocalizedStarApp


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

    # BLOCO 32: manutenção bounded sobre os stores, memória e grafo oficiais.
    # Consolidação continua delegada ao B13 e nenhuma exclusão ocorre por padrão.
    star.cognitive_maintenance = CognitiveMaintenance(
        star.knowledge,
        memory_continuity=star.memory_continuity,
        epistemics=star.mind.epistemics,
        graph=star.mind.graph,
        self_improvement=star.mind.self_improvement,
    )
    star.mind.cognitive_maintenance = star.cognitive_maintenance

    # BLOCO 33: formaliza a fronteira de autonomia reutilizando exatamente o
    # OperationalBoundary do B01. Não existe Permission Manager paralelo.
    star.autonomy_limits = AutonomyLimits(
        star.knowledge,
        operational_boundary=star.foundations.boundary,
    )
    star.mind.autonomy_limits = star.autonomy_limits
    star.agents.autonomy_limits = star.autonomy_limits

    # BLOCO 34/35: benchmark funcional e protocolo CFC-97. O benchmark só pontua
    # resultados observados/fornecidos; não se autoaprova e não mede humanidade.
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

    # BLOCO 36: pesquisa sobre consciência via B02/B03, mantendo a conclusão
    # sobre consciência da STAR explicitamente não estabelecida.
    star.consciousness_frontier = ConsciousnessResearchFrontier(
        star.knowledge,
        self_model=star.self_model,
        metacognition=star.metacognition,
    )
    star.mind.consciousness_frontier = star.consciousness_frontier

    # Os novos blocos ficam acessíveis pelo dispatcher já existente para status
    # e IDs. Não há um segundo Router: o mesmo AgentManager apenas delega handles.
    star.agents.attach_system_handlers(
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
    print(f"🧠 Identidade: {star.get_name()}")
    print(f"👤 Criador: {star.get_creator()}")
    print("📚 Conhecimento interno: ATIVO")
    print(
        "⚛️ Física local: "
        f"{physics_stats['canonical_topics']} tópicos | "
        f"{physics_stats['content_variations']} conteúdos variáveis"
    )
    print(
        "🧪 Química local: "
        f"{chemistry_stats['canonical_topics']} tópicos | "
        f"{chemistry_stats['content_variations']} conteúdos variáveis"
    )
    print(
        "🧭 Biblioteca multidisciplinar: "
        f"{multi_stats['subjects']} matérias | "
        f"{multi_stats['canonical_nodes']} nós | "
        f"{multi_stats['total_content_variations']} conteúdos variáveis"
    )
    print(
        "🚀 Knowledge PLUS: "
        f"+{plus_stats['added_content_variations_per_domain']} por domínio | "
        f"+{plus_stats['added_content_variations']} novos | "
        f"{plus_stats['combined_content_variations']} conteúdos de conhecimento combinados"
    )
    print(
        "🧬 Currículo canônico: "
        f"{curriculum_stats['themes']} temas | "
        f"{curriculum_stats['unique_concepts']} conceitos únicos | "
        f"{curriculum_stats['deduplicated_mentions']} menções duplicadas consolidadas | "
        f"{curriculum_stats['total_new_addressable_contents']} conteúdos endereçáveis"
    )
    print(
        "🧠 STAR MIND alpha: "
        f"{mind_stats['capabilities']} capacidades | "
        f"{mind_stats['canonical_nodes_total']} nós cognitivos | "
        f"{mind_stats['support_contents_total']} conteúdos operacionais endereçáveis"
    )
    print("🔄 Cognição integrada: FAST/DELIBERATIVE + posição cognitiva")
    print("🧹 Manutenção cognitiva B32: BOUNDED/ON-DEMAND")
    print("🛡️ Limites de autonomia B33: B01 BOUNDARY / DEFAULT DENY")
    print(
        "🧪 CFC/CFC-97 B34-B35: "
        f"{len(star.cfc.stats()['dimensions'])} dimensões | "
        f"{cfc97_stats['registered_1b_blocks']}/36 blocos 1B registrados | NÃO CERTIFICADO"
    )
    print("🧠 Consciência B36: FRONTEIRA DE PESQUISA / STATUS DA STAR NÃO ESTABELECIDO")
    print("🧩 Skills: PREPARADAS")
    print("🛠️ Ferramentas: ATIVAS (matemática offline + MIND experimental)")
    print(f"📦 Knowledge Packs detectados: {pack_stats['packs']}")
    print(f"💾 Packs locais: {storage_stats['local']} | removíveis: {storage_stats['removable']}")
    print(f"📄 Entradas de conhecimento carregadas: {pack_stats['entries']}")
    print("🤖 IA externa:", "ATIVA" if EXTERNAL_AI_ENABLED else "DESATIVADA")
    print("🖥️ Interface: ATIVA")

    gateway = _start_device_gateway(star)
    try:
        LocalizedStarApp(brain=star).run()
    finally:
        if gateway is not None:
            gateway.stop()


if __name__ == "__main__":
    main()
