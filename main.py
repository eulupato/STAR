import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import EXTERNAL_AI_ENABLED, MIND_ENABLED, VERSION
from core.executive import Executive
from core.internal_knowledge import StarInternalKnowledge
from core.knowledge_packs import KnowledgePackManager
from core.mind import StarMind
from core.router import Router
from core.skills import SkillRegistry
from core.star_core import StarCore
from core.star_identity import StarIdentity
from core.state import StarState
from core.tools import ToolRegistry, safe_math
from gui.app import StarApp


def create_star():
    identity = StarIdentity()
    knowledge = StarInternalKnowledge(identity)
    state = StarState()
    router = Router(internal_knowledge=knowledge)
    executive = Executive(model_manager=None, internal_knowledge=knowledge)
    mind = StarMind() if MIND_ENABLED else None

    star = StarCore(
        router=router,
        executive=executive,
        state=state,
        identity=identity,
        internal_knowledge=knowledge,
        mind=mind,
    )

    star.skills = SkillRegistry()
    star.tools = ToolRegistry()
    star.tools.register("math", safe_math, True, "Cálculo matemático offline")
    star.packs = KnowledgePackManager(ROOT / "knowledge" / "packs")
    star.packs.scan()
    return star


def main():
    print("=" * 60)
    print(f"⭐ INICIALIZANDO STAR V{VERSION} — MIND")
    print("=" * 60)

    star = create_star()
    print(f"🧠 Identidade: {star.get_name()}")
    print(f"👤 Criador: {star.get_creator()}")
    print("🧠 MIND V2:", "ATIVA" if star.mind is not None else "FALLBACK V1.9")
    if star.mind is not None:
        print("🚌 Event Bus: ATIVO")
        print("💭 Working Memory: ATIVA")
        print("🎯 Salience + Planner: ATIVOS")
    print("📚 Conhecimento interno: ATIVO")
    print("🧩 Skills: PREPARADAS")
    print("🛠️ Ferramentas: ATIVAS (matemática offline)")
    print(f"📦 Knowledge Packs detectados: {len(star.packs.list())}")
    print("🤖 IA externa:", "ATIVA" if EXTERNAL_AI_ENABLED else "DESATIVADA")
    print("🖥️ Interface: ATIVA")

    StarApp(brain=star).run()


if __name__ == "__main__":
    main()
