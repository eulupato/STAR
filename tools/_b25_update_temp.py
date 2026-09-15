from __future__ import annotations
import json
from pathlib import Path

# B23: provider attached != active observations.
p = Path('core/global_workspace.py')
s = p.read_text(encoding='utf-8')
old = '''    def component_status(self):\n        return {"perception":"available" if self.perception_provider is not None else "unavailable","salience":"available","attention":"available","memory":"available","knowledge":"available","language":"available" if self.language else "unavailable","planning":"available" if self.planning else "unavailable","executive":"available" if self.executive else "unavailable","self":"available" if self.self_model else "unavailable","situation":"available" if self.internal_models else "unavailable"}\n'''
new = '''    def _perception_status(self):\n        provider=self.perception_provider\n        if provider is None:return "unavailable"\n        checker=getattr(provider,"workspace_available",None)\n        if callable(checker):\n            try:return "available" if bool(checker()) else "idle"\n            except (RuntimeError,TypeError,AttributeError):return "unknown"\n        return "available"\n    def component_status(self):\n        return {"perception":self._perception_status(),"salience":"available","attention":"available","memory":"available","knowledge":"available","language":"available" if self.language else "unavailable","planning":"available" if self.planning else "unavailable","executive":"available" if self.executive else "unavailable","self":"available" if self.self_model else "unavailable","situation":"available" if self.internal_models else "unavailable"}\n'''
if old not in s:
    raise SystemExit('B23 component_status marker missing')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# B24: attached B25 with empty buffer is idle, not fabricated provider data.
p = Path('core/mind_loop.py')
s = p.read_text(encoding='utf-8')
old = '''        if self.perception_provider is not None and hasattr(self.perception_provider, "workspace_observations"):\n            items = self.perception_provider.workspace_observations(limit=16)\n            return {"status": "provider", "items": deepcopy(list(items or ()))[:16], "provider_available": True, "fabricated": False}\n        return {"status": "unavailable", "items": [], "provider_available": False, "fabricated": False}\n'''
new = '''        if self.perception_provider is not None and hasattr(self.perception_provider, "workspace_observations"):\n            items = deepcopy(list(self.perception_provider.workspace_observations(limit=16) or ()))[:16]\n            available = bool(items)\n            checker = getattr(self.perception_provider, "workspace_available", None)\n            if callable(checker):\n                try:\n                    available = bool(checker())\n                except (RuntimeError, TypeError, AttributeError):\n                    available = bool(items)\n            return {"status": "provider" if items else "idle", "items": items, "provider_available": available, "fabricated": False}\n        return {"status": "unavailable", "items": [], "provider_available": False, "fabricated": False}\n'''
if old not in s:
    raise SystemExit('B24 perception marker missing')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# StarCore: B25 attaches to B23/B24 but starts with zero active sensor providers.
p = Path('core/star_core.py')
s = p.read_text(encoding='utf-8')
marker = 'from core.mind_loop import MindLoop\n'
if 'from core.multimodal_perception import MultimodalPerception\n' not in s:
    s = s.replace(marker, marker + 'from core.multimodal_perception import MultimodalPerception\n', 1)
init_marker = '''        self.mind.mind_loop = self.mind_loop\n\n        self.last_intent = None\n'''
init_block = '''        self.mind.mind_loop = self.mind_loop\n\n        # BLOCO 25: Percepção Multimodal + Sensor Fusion. Reutiliza as referências\n        # existentes de visão/áudio/voz/tela, mas não inicia nenhum sensor. Dados só\n        # entram explicitamente ou por coleta autorizada; B23/B24 consomem o buffer\n        # perceptivo bounded sem polling silencioso.\n        self.multimodal_perception = MultimodalPerception(self.knowledge)\n        self.global_workspace.attach_perception(self.multimodal_perception)\n        self.mind_loop.attach_perception(self.multimodal_perception)\n        self.mind.multimodal_perception = self.multimodal_perception\n\n        self.last_intent = None\n'''
if 'self.multimodal_perception = MultimodalPerception(' not in s:
    if init_marker not in s:
        raise SystemExit('B25 init marker missing')
    s = s.replace(init_marker, init_block, 1)
route_marker = '''        mind_loop_action = self.mind_loop.handle(user_input)\n        if mind_loop_action:\n            self.last_intent = "mind_loop"\n            return mind_loop_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
route_block = '''        mind_loop_action = self.mind_loop.handle(user_input)\n        if mind_loop_action:\n            self.last_intent = "mind_loop"\n            return mind_loop_action\n\n        perception_action = self.multimodal_perception.handle(user_input)\n        if perception_action:\n            self.last_intent = "multimodal_perception"\n            return perception_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
if 'perception_action = self.multimodal_perception.handle' not in s:
    if route_marker not in s:
        raise SystemExit('B25 route marker missing')
    s = s.replace(route_marker, route_block, 1)
p.write_text(s, encoding='utf-8')

# Manifesto.
p = Path('STAR_MIND_MANIFEST.json')
data = json.loads(p.read_text(encoding='utf-8'))
data['schema'] = max(int(data.get('schema', 0)), 26)
principles = data.setdefault('principles', [])
for item in (
    'B25 separates integrated sensor references from actually attached/observing providers',
    'camera, microphone, screen, location and sensor collection are never activated automatically by multimodal perception',
    'Sensor Fusion preserves modality provenance, confidence and contradictions and produces inference rather than canonical fact',
    'B25 feeds B23 Global Workspace and B24 Mind Loop through bounded perceptual buffers only',
):
    if item not in principles:
        principles.append(item)
data['block_25_multimodal_perception'] = {
    'status': 'experimental-integrated',
    'source_of_truth': 'core/multimodal_perception.py',
    'integration': 'core/star_core.py',
    'namespace': 'B25',
    'logical_capacity': 1_000_000_000,
    'modalities': ['vision','audio','voice','screen','location','sensors','motion','objects','people','environment','time'],
    'sensor_fusion': {
        'implemented': True,
        'bounded_inputs': 32,
        'preserves_sources': True,
        'preserves_contradictions': True,
        'fused_result_kind': 'inference',
        'canonical_fact': False,
    },
    'existing_references': {
        'vision': ['modules.vision','modules.vision_model (hand tracking only)'],
        'audio': ['voice.audio_input.AudioRecorder'],
        'voice': ['voice.manager','voice.audio_input.AudioRecorder'],
        'screen': ['modules.computer_control.take_screenshot (manual action only)'],
        'motion': ['modules.vision gesture/point tracking'],
        'location': [], 'sensors': [], 'objects': [], 'people': [], 'environment': [], 'time': ['system clock timestamp metadata'],
    },
    'runtime': {'observation_buffer_default': 128, 'fusion_buffer_default': 64, 'persistent_sensor_store': False, 'automatic_collection': False},
    'integration_targets': ['B23 Global Cognitive Workspace','B24 Mind Loop','shared B03 Knowledge Graph'],
    'catalog': {'domains': 10, 'branches': 50, 'lenses_per_branch': 10, 'canonical_nodes': 500, 'variants_per_node': 2_000_000, 'addressable_contents': 1_000_000_000, 'materialization': 'on-demand'},
}
def walk(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'current_namespaces' and isinstance(value, list) and 'B25' not in value:
                value.append('B25')
            walk(value)
    elif isinstance(obj, list):
        for value in obj:
            walk(value)
walk(data)
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Roadmap.
p = Path('docs/MASTER_ROADMAP.md')
r = p.read_text(encoding='utf-8')
section = '''### BLOCO 25 — Percepção Multimodal\n\nB25 integra visão, áudio, voz, tela, localização, sensores, movimento, objetos,\npessoas, ambiente e tempo em uma camada perceptiva comum com **Sensor Fusion**.\nA arquitetura reutiliza as referências existentes (`modules.vision`,\n`voice.audio_input`, `voice.manager` e captura de tela manual), mas não inicia\ncâmera, microfone, screenshot, localização ou sensores automaticamente.\nModalidades sem provider real permanecem `unavailable`; provider conectado sem\nobservação fica `idle`.\n\nObservações preservam fonte, referência, timestamp, confiança, features, objetos,\npessoas, eventos, sons, movimentos, ambiente e localização. Sensor Fusion opera\nsobre uma janela bounded, relaciona sinais por co-observação/entidades, preserva\ncontradições e produz `inference`, nunca fato canônico automático.\n\nB25 alimenta B23 e B24 por `workspace_observations()` side-effect free; esses\nconsumidores nunca fazem polling silencioso de hardware. Coleta de providers é\nexplícita e requer permissão informada ao método.\n\nEscala lógica: 500 nós × 2M = **1B** `PER-B25-*` sob demanda; buffers de runtime\nsão pequenos (128 observações / 64 fusões por padrão), sem banco de sensores paralelo.\n\n'''
if '### BLOCO 25 — Percepção Multimodal' not in r:
    idx = r.find('## V2.1')
    if idx < 0:
        raise SystemExit('roadmap V2.1 marker missing')
    r = r[:idx] + section + r[idx:]
p.write_text(r, encoding='utf-8')
