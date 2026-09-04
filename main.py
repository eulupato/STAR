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
from core.knowledge_packs import KnowledgePackManager
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
    packs = KnowledgePackManager(ROOT / "knowledge" / "packs", auto_removable=True)
    state = StarState()
    router = Router(internal_knowledge=knowledge)
    executive = Executive(
        model_manager=None,
        internal_knowledge=knowledge,
        knowledge_packs=packs,
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
    star.packs = packs
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
    print(f"🧠 Identidade: {star.get_name()}")
    print(f"👤 Criador: {star.get_creator()}")
    print("📚 Conhecimento interno: ATIVO")
    print("🧩 Skills: PREPARADAS")
    print("🛠️ Ferramentas: ATIVAS (matemática offline)")
    print(f"📦 Knowledge Packs detectados: {pack_stats['packs']}")
    print(f"💾 Packs locais: {storage_stats['local']} | removíveis: {storage_stats['removable']}")
    print(f"📄 Entradas de conhecimento carregadas: {pack_stats['entries']}")
    print("🤖 IA externa:", "ATIVA" if EXTERNAL_AI_ENABLED else "DESATIVADA")
    print("🖥️ Interface: ATIVA")

    gateway = _start_device_gateway(star)
    try:
        StarApp(brain=star).run()
    finally:
        if gateway is not None:
            gateway.stop()


if __name__ == "__main__":
    main()
