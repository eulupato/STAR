import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import (
    CODENAME,
    EXTERNAL_AI_ENABLED,
    KNOWLEDGE_DB,
    KNOWLEDGE_ENABLED,
    MIND_ENABLED,
    MIND_EVENT_HISTORY,
    MIND_WORKING_MEMORY_TURNS,
    VERSION,
)
from core.conversation import ConversationVariationEngine
from core.executive import Executive
from core.internal_knowledge import StarInternalKnowledge
from core.knowledge_packs import KnowledgePackManager
from core.logging_config import get_logger
from core.mind import StarMind
from core.router import Router
from core.skills import SkillRegistry
from core.star_core import StarCore
from core.star_identity import StarIdentity
from core.state import StarState
from core.tools import ToolRegistry, safe_math
from gui.app import StarApp
from knowledge.bootstrap import bootstrap_legacy_heroes
from knowledge.engine import KnowledgeEngine

log = get_logger("startup")


def create_star(*, knowledge_db=None):
    identity = StarIdentity()
    internal_knowledge = StarInternalKnowledge(identity)
    state = StarState()
    router = Router(internal_knowledge=internal_knowledge)
    executive = Executive(
        model_manager=None,
        internal_knowledge=internal_knowledge,
    )
    mind = (
        StarMind(
            event_history=MIND_EVENT_HISTORY,
            working_memory_turns=MIND_WORKING_MEMORY_TURNS,
        )
        if MIND_ENABLED
        else None
    )

    packs = KnowledgePackManager(ROOT / "knowledge" / "packs")
    db_path = Path(knowledge_db) if knowledge_db else ROOT / KNOWLEDGE_DB
    knowledge = (
        KnowledgeEngine(
            db_path,
            pack_manager=packs,
            event_bus=mind.events if mind is not None else None,
        )
        if KNOWLEDGE_ENABLED
        else None
    )
    conversation = ConversationVariationEngine()

    star = StarCore(
        router=router,
        executive=executive,
        state=state,
        identity=identity,
        internal_knowledge=internal_knowledge,
        mind=mind,
        knowledge=knowledge,
        conversation=conversation,
    )

    star.skills = SkillRegistry()
    star.tools = ToolRegistry()
    star.tools.register("math", safe_math, True, "Cálculo matemático offline")
    star.packs = packs

    if knowledge is not None:
        seed_path = ROOT / "knowledge" / "packs" / "heroes" / "heroes.json"
        migrated = bootstrap_legacy_heroes(knowledge, seed_path)
        if migrated:
            log.info("Knowledge bootstrap: %s entidades processadas.", migrated)

    return star


def main():
    log.info("Version %s — %s", VERSION, CODENAME)
    star = create_star()
    log.info("Core initialized")
    log.info("MIND: %s", "ATIVA" if star.mind is not None else "FALLBACK LOCAL")
    knowledge_status = star.knowledge_status()
    log.info(
        "Knowledge: %s entidades indexadas",
        knowledge_status.get("entities", 0),
    )
    log.info("Knowledge Packs: %s", len(star.packs.list()))
    log.info("IA externa: %s", "ATIVA" if EXTERNAL_AI_ENABLED else "DESATIVADA")
    log.info("Interface: ATIVA")
    StarApp(brain=star).run()


if __name__ == "__main__":
    main()
