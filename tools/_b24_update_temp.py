from __future__ import annotations
import json
from pathlib import Path

# 1) Robustez do B24: materializa opções bounded uma única vez.
p = Path('core/mind_loop.py')
s = p.read_text(encoding='utf-8')
old = '''        current = deepcopy(dict(current_state or {}))\n        desired = deepcopy(dict(desired_state or {}))\n        limit = max(4, min(int(active_limit), min(self.global_workspace.max_active, 32)))\n'''
new = '''        current = deepcopy(dict(current_state or {}))\n        desired = deepcopy(dict(desired_state or {}))\n        option_list = deepcopy(list(options or ())[:32])\n        limit = max(4, min(int(active_limit), min(self.global_workspace.max_active, 32)))\n'''
if old in s:
    s = s.replace(old, new, 1)
s = s.replace('first_option = next(iter(list(options or ())[:1]), None)', 'first_option = option_list[0] if option_list else None', 1)
s = s.replace('                options=options,\n', '                options=option_list,\n', 1)
p.write_text(s, encoding='utf-8')

# 2) Integração StarCore.
p = Path('core/star_core.py')
s = p.read_text(encoding='utf-8')
marker = 'from core.metacognition import Metacognition\n'
if 'from core.mind_loop import MindLoop\n' not in s:
    s = s.replace(marker, marker + 'from core.mind_loop import MindLoop\n', 1)
init_marker = '''        self.mind.global_workspace = self.global_workspace\n\n        self.last_intent = None\n'''
init_block = '''        self.mind.global_workspace = self.global_workspace\n\n        # BLOCO 24: Mind Loop. Orquestra B13-B23 em 17 etapas com recuperação\n        # bounded. A etapa AÇÃO avalia apenas a fronteira operacional; nenhuma\n        # ferramenta/dispositivo é executado pelo loop e resultados não observados\n        # nunca viram experiências inventadas.\n        self.mind_loop = MindLoop(\n            self.knowledge,\n            global_workspace=self.global_workspace,\n            memory_continuity=self.memory_continuity,\n            attention_salience=self.attention_salience,\n            internal_models=self.internal_models,\n            reasoning_simulation=self.reasoning_simulation,\n            metacognition=self.metacognition,\n            planning_decision=self.planning_decision,\n            learning_evolution=self.learning_evolution,\n            knowledge_integration=self.knowledge_integration,\n            operational_boundary=self.foundations.boundary,\n            social_cognition=self.social_cognition,\n            perception_provider=None,\n        )\n        self.mind.mind_loop = self.mind_loop\n\n        self.last_intent = None\n'''
if 'self.mind_loop = MindLoop(' not in s:
    if init_marker not in s:
        raise SystemExit('B24 init marker not found')
    s = s.replace(init_marker, init_block, 1)
route_marker = '''        workspace_action = self.global_workspace.handle(user_input)\n        if workspace_action:\n            self.last_intent = "global_workspace"\n            return workspace_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
route_block = '''        workspace_action = self.global_workspace.handle(user_input)\n        if workspace_action:\n            self.last_intent = "global_workspace"\n            return workspace_action\n\n        mind_loop_action = self.mind_loop.handle(user_input)\n        if mind_loop_action:\n            self.last_intent = "mind_loop"\n            return mind_loop_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
if 'mind_loop_action = self.mind_loop.handle' not in s:
    if route_marker not in s:
        raise SystemExit('B24 route marker not found')
    s = s.replace(route_marker, route_block, 1)
p.write_text(s, encoding='utf-8')

# 3) Manifesto.
p = Path('STAR_MIND_MANIFEST.json')
data = json.loads(p.read_text(encoding='utf-8'))
data['schema'] = max(int(data.get('schema', 0)), 25)
principles = data.setdefault('principles', [])
for item in (
    'B24 Mind Loop orchestrates existing cognition instead of duplicating memory, models, reasoning or planning',
    'each Mind Loop cycle retrieves only bounded active context through B23/B14 rather than scanning logical 1B spaces',
    'the ACTION stage evaluates operational eligibility but never executes tools or devices',
    'RESULT/EXPERIENCE/LEARNING require observed and auditable input; the loop never fabricates outcomes to complete a cycle',
):
    if item not in principles:
        principles.append(item)
data['block_24_mind_loop'] = {
    'status': 'experimental-integrated',
    'source_of_truth': 'core/mind_loop.py',
    'integration': 'core/star_core.py',
    'namespace': 'B24',
    'logical_capacity': 1_000_000_000,
    'stages': [
        'PERCEBER','CONTEXTO','WORKING MEMORY','SALIÊNCIA','MEMÓRIA','CONHECIMENTO','MODELOS',
        'INTERPRETAÇÃO','SIMULAÇÃO','METACOGNIÇÃO','JULGAMENTO','DECISÃO','AÇÃO','RESULTADO',
        'EXPERIÊNCIA','APRENDIZADO','ATUALIZAÇÃO'
    ],
    'retrieval': {'workspace': 'B23 bounded active set', 'attention': 'B14 top-k', 'memory': 'B13 limit', 'knowledge': 'B03 indexed limit'},
    'reuses': ['B13','B14','B15','B18','B19','B20','B21','B22','B23','B01 OperationalBoundary'],
    'safety': {'automatic_execution': False, 'fabricated_result': False, 'unaudited_experience': False, 'automatic_code_modification': False},
    'catalog': {'domains': 10, 'branches': 50, 'lenses_per_branch': 10, 'canonical_nodes': 500, 'variants_per_node': 2_000_000, 'addressable_contents': 1_000_000_000, 'materialization': 'on-demand'},
}
def walk(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == 'current_namespaces' and isinstance(v, list) and 'B24' not in v:
                v.append('B24')
            walk(v)
    elif isinstance(obj, list):
        for v in obj:
            walk(v)
walk(data)
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# 4) Roadmap, sem alterar marcos posteriores.
p = Path('docs/MASTER_ROADMAP.md')
r = p.read_text(encoding='utf-8')
section = '''### BLOCO 24 — Mind Loop\n\nB24 orquestra o ciclo cognitivo explícito da STAR reutilizando os sistemas já\nexistentes, sem criar memória/modelos/planner/executor paralelos:\n\n```text\nPERCEBER → CONTEXTO → WORKING MEMORY → SALIÊNCIA → MEMÓRIA → CONHECIMENTO\n→ MODELOS → INTERPRETAÇÃO → SIMULAÇÃO → METACOGNIÇÃO → JULGAMENTO → DECISÃO\n→ AÇÃO → RESULTADO → EXPERIÊNCIA → APRENDIZADO → ATUALIZAÇÃO\n```\n\nA recuperação é bounded: B23/B14 selecionam o conjunto ativo, B13/B03 são\nconsultados com limites pequenos e os espaços lógicos de 1B dos blocos anteriores\nnunca são varridos/carregados integralmente em um ciclo.\n\nA etapa **AÇÃO** somente avalia `OperationalBoundary`; B24 não executa ferramentas\nou dispositivos. RESULTADO só existe se observado/fornecido e EXPERIÊNCIA exige\nfonte + referência auditável. Sem resultado real, aprendizado/atualização não são\ninventados.\n\nEscala B24: 500 nós × 2M = **1B** `LOOP-B24-*` sob demanda.\n\n'''
if '### BLOCO 24 — Mind Loop' not in r:
    idx = r.find('## V2.1')
    if idx < 0:
        raise SystemExit('roadmap V2.1 marker not found')
    r = r[:idx] + section + r[idx:]
p.write_text(r, encoding='utf-8')
