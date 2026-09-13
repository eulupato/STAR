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
from core.executive import Executive
from core.internal_knowledge import StarInternalKnowledge
from core.m_drive_manager import MDriveManager
from core.physics_knowledge_150k import PhysicsKnowledgeEngine
from core.chemistry_knowledge_500k import ChemistryKnowledgeEngine
from core.multidisciplinary_knowledge import MultidisciplinaryKnowledgeEngine
from core.knowledge_expansion_15m import KnowledgeExpansion15MEngine
from core.curriculum_knowledge import CurriculumKnowledgeEngine
from core.religion_magic_knowledge import ReligionMagicKnowledgeEngine
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
    religion_magic = ReligionMagicKnowledgeEngine()
    mdrives = MDriveManager(
        ROOT / "knowledge" / "m_drives",
        legacy_root=ROOT / "knowledge" / "packs",
        auto_removable=True,
    )
    state = StarState()
    router = Router(internal_knowledge=knowledge)
    executive = Executive(
        model_manager=None,
        internal_knowledge=knowledge,
        knowledge_packs=mdrives,
        physics_knowledge=physics,
        chemistry_knowledge=chemistry,
        multidisciplinary_knowledge=multidisciplinary,
        knowledge_expansion=knowledge_plus,
        curriculum_knowledge=curriculum,
        religion_magic_knowledge=religion_magic,
    )
    star = StarCore(
        router=router,
        executive=executive,
        state=state,
        identity=identity,
        internal_knowledge=knowledge,
    )
    star.skills = SkillRegistry()
    star.tools = ToolRegistry()
    star.tools.register("math", safe_math, True, "Cálculo matemático offline")
    star.mdrives = mdrives
    star.packs = mdrives  # alias temporário para compatibilidade interna/externa V1.9
    star.physics = physics
    star.chemistry = chemistry
    star.multidisciplinary = multidisciplinary
    star.knowledge_plus = knowledge_plus
    star.curriculum = curriculum
    star.religion_magic = religion_magic
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
    mdrive_stats = star.mdrives.stats()
    storage_stats = star.mdrives.storage_stats()
    physics_stats = star.physics.stats()
    chemistry_stats = star.chemistry.stats()
    multi_stats = star.multidisciplinary.stats()
    plus_stats = star.knowledge_plus.stats()
    curriculum_stats = star.curriculum.stats()
    cultural_stats = star.religion_magic.stats()
    mind_stats = star.mind.stats()
    evolution_stats = star.evolution.stats()
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
        "🌍 Religiões/magia: "
        f"{cultural_stats['religion_subjects']} tradições religiosas + "
        f"{cultural_stats['magic_esotericism_subjects']} campos de magia/esoterismo | "
        f"{cultural_stats['canonical_nodes']} nós | "
        f"{cultural_stats['total_addressable_contents']} visões culturais endereçáveis"
    )
    print(
        "🧠 STAR MIND alpha: "
        f"{mind_stats['capabilities']} capacidades | "
        f"{mind_stats['canonical_nodes_total']} nós cognitivos | "
        f"{mind_stats['support_contents_total']} conteúdos operacionais endereçáveis"
    )
    print("🧩 Skills: PREPARADAS")
    print("🛠️ Ferramentas: ATIVAS (matemática offline + MIND/Evolution alpha)")
    print(f"💾 M.drives detectados: {mdrive_stats['mdrives']}")
    print(
        "💽 M.drives locais: "
        f"{storage_stats['local']} | legados: {storage_stats['legacy']} | "
        f"removíveis: {storage_stats['removable']}"
    )
    print(f"📄 Entradas M.drive carregadas: {mdrive_stats['entries']}")
    print(
        "🛡️ Guardian/Agent: "
        f"Guardian={evolution_stats['guardian']['status']} | "
        f"Goal Engine={evolution_stats['goal_engine']['status']} | "
        f"RAG híbrido={evolution_stats['semantic_rag']['status']}"
    )
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
