from __future__ import annotations

import json
from pathlib import Path

# --- B19 decision persistence: use official CognitiveMemory decision kind --------
planning_path = Path("core/planning_decision.py")
planning = planning_path.read_text(encoding="utf-8")
old = '''        return self.memory_continuity.remember(\n            "decision",\n            f"Decisão B19: {goal} -> {decision.get('selected_label')}",\n            source=_clean(source),\n            reference=_clean(reference),\n            importance=_clamp(importance),\n            context={"goal": goal, "decision": decision, "verification": deepcopy(artifact.get("verification") or {})},\n            meaning="registro auditável de decisão cognitiva; não prova execução",\n            metadata={"block": "B19", "execution_performed": False, "operational_authorization": False},\n        )\n'''
new = '''        content = f"Decisão B19: {goal} -> {decision.get('selected_label')}"\n        metadata = {\n            "block": "B19",\n            "source": _clean(source),\n            "reference": _clean(reference),\n            "goal": goal,\n            "decision": decision,\n            "verification": deepcopy(artifact.get("verification") or {}),\n            "meaning": "registro auditável de decisão cognitiva; não prova execução",\n            "execution_performed": False,\n            "operational_authorization": False,\n            "canonical_knowledge": False,\n        }\n        memory_id = self.memory_continuity.memory.remember(\n            "decision",\n            content,\n            key=f"b19:decision:{_norm(goal)}",\n            metadata=metadata,\n            importance=_clamp(importance),\n        )\n        record = self.memory_continuity.memory.store.memory_by_id(memory_id)\n        if record is None:\n            raise RuntimeError("decisão B19 persistida não pôde ser relida")\n        root = self.graph.add_entity(\n            "planning_decision_taxonomy",\n            "PLANEJAMENTO E TOMADA DE DECISÃO",\n            node_id=self.TAXONOMY_ROOT_ID,\n            data={"block": "B19", "automatic_execution": False},\n        )\n        node_id = f"PLANNING-DECISION-{memory_id:010d}"\n        self.graph.add_entity(\n            "planning_decision",\n            content[:160],\n            node_id=node_id,\n            data={"block": "B19", "memory_id": memory_id, "reference": _clean(reference), "execution_performed": False},\n        )\n        self.graph.relate(root, node_id, "has_recorded_decision", metadata={"block": "B19"})\n        return {\n            "memory_id": memory_id,\n            "memory_node_id": node_id,\n            "kind": "decision",\n            "persistent": True,\n            "record": record,\n            "execution_performed": False,\n            "operational_authorization": False,\n        }\n'''
if old not in planning:
    raise SystemExit("B19 record_decision marker not found")
planning_path.write_text(planning.replace(old, new, 1), encoding="utf-8")

# --- STAR Core -------------------------------------------------------------------
core_path = Path("core/star_core.py")
core = core_path.read_text(encoding="utf-8")
import_marker = "from core.reasoning_simulation import ReasoningSimulation\n"
if "from core.planning_decision import PlanningDecision\n" not in core:
    if import_marker not in core:
        raise SystemExit("B19 import marker missing")
    core = core.replace(import_marker, import_marker + "from core.planning_decision import PlanningDecision\n", 1)

init_marker = '''        self.mind.reasoning_simulation = self.reasoning_simulation\n\n        self.last_intent = None\n'''
init_block = '''        self.mind.reasoning_simulation = self.reasoning_simulation\n\n        # BLOCO 19: evolução integrada do Planner oficial. Coordena estado,\n        # opções, B18 simulação/risco, B14 contexto bounded e B01 boundary.\n        # Planejamento e decisão nunca executam ações automaticamente.\n        self.planning_decision = PlanningDecision(\n            self.knowledge,\n            planner=self.mind.planner,\n            reasoning_simulation=self.reasoning_simulation,\n            memory_continuity=self.memory_continuity,\n            attention_salience=self.attention_salience,\n            internal_models=self.internal_models,\n            operational_boundary=self.foundations.boundary,\n        )\n        self.mind.planning_decision = self.planning_decision\n\n        self.last_intent = None\n'''
if "self.planning_decision = PlanningDecision(" not in core:
    if init_marker not in core:
        raise SystemExit("B19 init marker missing")
    core = core.replace(init_marker, init_block, 1)

route_marker = '''        reasoning_simulation_action = self.reasoning_simulation.handle(user_input)\n        if reasoning_simulation_action:\n            self.last_intent = "reasoning_simulation"\n            return reasoning_simulation_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
route_block = '''        reasoning_simulation_action = self.reasoning_simulation.handle(user_input)\n        if reasoning_simulation_action:\n            self.last_intent = "reasoning_simulation"\n            return reasoning_simulation_action\n\n        planning_decision_action = self.planning_decision.handle(user_input)\n        if planning_decision_action:\n            self.last_intent = "planning_decision"\n            return planning_decision_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
if "planning_decision_action = self.planning_decision.handle" not in core:
    if route_marker not in core:
        raise SystemExit("B19 route marker missing")
    core = core.replace(route_marker, route_block, 1)
core_path.write_text(core, encoding="utf-8")

# --- Manifest --------------------------------------------------------------------
manifest_path = Path("STAR_MIND_MANIFEST.json")
data = json.loads(manifest_path.read_text(encoding="utf-8"))
data["schema"] = max(int(data.get("schema", 0)), 20)
principles = data.setdefault("principles", [])
for item in (
    "planning and cognitive decision remain distinct from operational execution",
    "recommendation, priority, simulation and selected option never grant permission",
    "B19 reuses the official CognitiveSuite planner and B18 simulation/risk instead of creating parallel engines",
    "large planning spaces are handled through bounded context/option selection rather than loading all logical contents",
):
    if item not in principles:
        principles.append(item)

data["block_19_planning_decision"] = {
    "status": "experimental-integrated",
    "source_of_truth": "core/planning_decision.py",
    "integration": "core/star_core.py",
    "namespace": "B19",
    "logical_capacity": 1000000000,
    "pipeline": ["GOAL", "CURRENT_STATE", "DESIRED_STATE", "OBSTACLES", "OPTIONS", "SIMULATION", "RISK", "PLAN", "DECISION", "VERIFICATION"],
    "reuse": {
        "planner": "existing CognitiveSuite.planner",
        "reasoning_simulation": "B18 ReasoningSimulation",
        "memory": "B13 cognitive_memory/working memory",
        "attention": "B14 bounded selection",
        "models": "B15 internal models",
        "operational_boundary": "B01 FoundationSuite.boundary",
        "new_planner_created": False,
        "new_table_created": False,
        "new_database_created": False,
    },
    "execution_policy": {
        "planning_is_execution": False,
        "decision_is_execution": False,
        "recommendation_is_permission": False,
        "automatic_execution": False,
        "permission_required": True,
        "capability_required": True,
        "safety_required": True,
        "B19_performs_execution": False,
    },
    "catalog": {
        "stages": 10,
        "branches": 50,
        "lenses_per_branch": 10,
        "canonical_nodes": 500,
        "variants_per_node": 2000000,
        "addressable_contents": 1000000000,
        "materialization": "on-demand",
        "prepopulated_plans": 0,
        "truthfulness_note": "1B are addressable planning contexts/representations, not 1B precomputed plans, decisions or executable actions",
    },
    "variant_matrix": {
        "context": 10,
        "constraint_mode": 10,
        "uncertainty": 10,
        "time_horizon": 10,
        "risk_level": 10,
        "source_space": 10,
        "planning_mode": 2,
        "combinations_per_node": 2000000,
    },
}

def append_namespace(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "current_namespaces" and isinstance(value, list) and "B19" not in value:
                value.append("B19")
            append_namespace(value)
    elif isinstance(obj, list):
        for value in obj:
            append_namespace(value)
append_namespace(data)
manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# --- Roadmap ---------------------------------------------------------------------
roadmap_path = Path("docs/MASTER_ROADMAP.md")
roadmap = roadmap_path.read_text(encoding="utf-8")
section = r'''### BLOCO 19 — Planejamento e Tomada de Decisão

O BLOCO 19 evolui o `CognitiveSuite.planner` existente; não cria `PlannerV2` ou
outro motor de planejamento. Ele coordena o pipeline auditável:

```text
OBJETIVO
→ ESTADO ATUAL
→ ESTADO DESEJADO
→ OBSTÁCULOS
→ OPÇÕES
→ SIMULAÇÃO
→ RISCO
→ PLANO
→ DECISÃO
→ VERIFICAÇÃO
```

Integra B13 para memória de trabalho/decisão, B14 para contexto bounded, B15 para
modelos internos, B18 para simulação/risco e o `OperationalBoundary` do B01.

Regras permanentes:

```text
PLANO ≠ AÇÃO
DECISÃO COGNITIVA ≠ EXECUÇÃO
RECOMENDAÇÃO ≠ PERMISSÃO
PRIORIDADE ≠ PERMISSÃO
RISCO ≠ PERMISSÃO
```

B19 nunca executa a opção escolhida. Mesmo quando `permission + capability +
safety_ok` tornam uma intenção elegível no `OperationalBoundary`, a resposta do
B19 continua `execution_performed=False`; execução pertence a uma camada separada.

Decisões persistentes usam o `cognitive_memory` oficial com `kind=decision` e
referência auditável, preservando B13 sem adicionar um 11º tipo central ao catálogo
de memória. O Knowledge Graph compartilhado relaciona registros de decisão.

Escala lógica B19:

- **50 ramos × 10 lentes = 500 nós canônicos**;
- contexto(10) × restrição(10) × incerteza(10) × tempo(10) × risco(10) × fonte(10) × modo(2) = **2M** por nó;
- **500 × 2M = 1.000.000.000** representações `PLAN-B19-*` sob demanda.

O 1B representa contextos, relações e estados de planejamento endereçáveis; não
significa 1B de planos pré-calculados, decisões materializadas ou ações autorizadas.

'''
if "### BLOCO 19 — Planejamento e Tomada de Decisão" not in roadmap:
    marker = "## V2.1"
    pos = roadmap.find(marker)
    if pos == -1:
        raise SystemExit("B19 roadmap V2.1 marker missing")
    roadmap = roadmap[:pos] + section + roadmap[pos:]
roadmap_path.write_text(roadmap, encoding="utf-8")
