from __future__ import annotations

import json
from pathlib import Path

# STAR Core
core_path = Path("core/star_core.py")
core = core_path.read_text(encoding="utf-8")
import_marker = "from core.memory_continuity import MemoryContinuity\n"
if "from core.metacognition import Metacognition\n" not in core:
    if import_marker not in core: raise SystemExit("B20 import marker missing")
    core = core.replace(import_marker, import_marker + "from core.metacognition import Metacognition\n", 1)

init_marker = '''        self.mind.planning_decision = self.planning_decision\n\n        self.last_intent = None\n'''
init_block = '''        self.mind.planning_decision = self.planning_decision\n\n        # BLOCO 20: metacognição sobre o MetacognitionEngine existente. Avalia\n        # conhecimento, crenças, inferências, confiança, fontes, contradições e\n        # necessidade de pesquisar/perguntar/revisar com contexto bounded.\n        self.metacognition = Metacognition(\n            self.knowledge,\n            base_engine=self.mind.metacognition,\n            verifier=self.mind.verifier,\n            memory_continuity=self.memory_continuity,\n            attention_salience=self.attention_salience,\n            reasoning_simulation=self.reasoning_simulation,\n            planning_decision=self.planning_decision,\n            self_model=self.self_model,\n        )\n        self.mind.metacognition_layer = self.metacognition\n\n        self.last_intent = None\n'''
if "self.metacognition = Metacognition(" not in core:
    if init_marker not in core: raise SystemExit("B20 init marker missing")
    core = core.replace(init_marker, init_block, 1)

route_marker = '''        planning_decision_action = self.planning_decision.handle(user_input)\n        if planning_decision_action:\n            self.last_intent = "planning_decision"\n            return planning_decision_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
route_block = '''        planning_decision_action = self.planning_decision.handle(user_input)\n        if planning_decision_action:\n            self.last_intent = "planning_decision"\n            return planning_decision_action\n\n        metacognition_action = self.metacognition.handle(user_input)\n        if metacognition_action:\n            self.last_intent = "metacognition"\n            return metacognition_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
if "metacognition_action = self.metacognition.handle" not in core:
    if route_marker not in core: raise SystemExit("B20 route marker missing")
    core = core.replace(route_marker, route_block, 1)
core_path.write_text(core, encoding="utf-8")

# Manifest
manifest_path = Path("STAR_MIND_MANIFEST.json")
data = json.loads(manifest_path.read_text(encoding="utf-8"))
data["schema"] = max(int(data.get("schema", 0)), 21)
principles = data.setdefault("principles", [])
for item in (
    "metacognition distinguishes knowledge, belief, inference and unknown states instead of collapsing them",
    "confidence scores do not become truth and contradictions remain visible until reviewed",
    "need for research never grants network permission and need for questioning does not automatically block best-effort reasoning",
    "B20 reuses CognitiveSuite.metacognition and bounded B14 attention rather than creating a parallel metacognitive engine",
):
    if item not in principles: principles.append(item)
data["block_20_metacognition"] = {
    "status":"experimental-integrated",
    "source_of_truth":"core/metacognition.py",
    "integration":"core/star_core.py",
    "namespace":"B20",
    "logical_capacity":1000000000,
    "evaluates":["known","unknown","belief","inference","confidence","source","contradictions","research_need","question_need","review_need"],
    "reuse":{
        "metacognition":"existing CognitiveSuite.metacognition",
        "verification":"CognitiveSuite.verifier",
        "memory":"B13",
        "attention":"B14 bounded selection",
        "reasoning":"B18",
        "planning":"B19",
        "new_engine_created":False,
        "new_database_created":False,
    },
    "policy":{
        "belief_is_fact":False,
        "inference_is_fact":False,
        "confidence_is_truth":False,
        "contradictions_erased":False,
        "research_need_grants_network_permission":False,
        "operational_authorization":False,
    },
    "catalog":{
        "domains":10,"branches":50,"lenses_per_branch":10,"canonical_nodes":500,
        "variants_per_node":2000000,"addressable_contents":1000000000,"materialization":"on-demand",
        "truthfulness_note":"1B are addressable metacognitive contexts, not precomputed self-assessments",
    },
}

def append_namespace(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "current_namespaces" and isinstance(value, list) and "B20" not in value: value.append("B20")
            append_namespace(value)
    elif isinstance(obj, list):
        for value in obj: append_namespace(value)
append_namespace(data)
manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Roadmap
roadmap_path = Path("docs/MASTER_ROADMAP.md")
roadmap = roadmap_path.read_text(encoding="utf-8")
section = r'''### BLOCO 20 — Metacognição

O BLOCO 20 coordena o `CognitiveSuite.metacognition` já existente com B13 memória,
B14 atenção, B18 raciocínio, B19 planejamento e o verificador oficial. Não cria
um segundo motor metacognitivo.

A STAR passa a representar explicitamente o que sabe, não sabe, acredita,
inferiu, qual confiança possui, quais fontes sustentam a avaliação, contradições
e quando precisa pesquisar, perguntar ou revisar.

Regras permanentes:

```text
SABER ≠ ACREDITAR ≠ INFERIR
CONFIANÇA ≠ VERDADE
CONTRADIÇÃO ≠ APAGAMENTO SILENCIOSO
NECESSIDADE DE PESQUISA ≠ PERMISSÃO DE REDE
```

A seleção de contexto é bounded via B14; portanto a arquitetura pode endereçar
1B de contextos metacognitivos sem carregar ou varrer o espaço inteiro.

Escala lógica B20: 50 ramos × 10 lentes = 500 nós; sete eixos somam 2M por nó;
500 × 2M = **1.000.000.000** representações `META-B20-*` sob demanda.

'''
if "### BLOCO 20 — Metacognição" not in roadmap:
    marker = "## V2.1"
    pos = roadmap.find(marker)
    if pos == -1: raise SystemExit("B20 roadmap marker missing")
    roadmap = roadmap[:pos] + section + roadmap[pos:]
roadmap_path.write_text(roadmap, encoding="utf-8")
