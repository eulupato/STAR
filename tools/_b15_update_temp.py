from __future__ import annotations

import json
from pathlib import Path

# --- SelfModel: namespace snapshot must be dynamic -------------------------
self_path = Path("core/self_model.py")
self_text = self_path.read_text(encoding="utf-8")
old = '''    def knowledge_snapshot(self) -> dict:\n        namespaces = []\n        for index in range(1, 13):\n            key = f"B{index:02d}"\n            item = self.knowledge.store.get_namespace(key)\n            if item:\n                namespaces.append({\n                    "namespace": key,\n                    "logical_capacity": item.get("logical_capacity"),\n                    "registered": True,\n                })\n        return {\n            "registered_namespaces": namespaces,\n            "canonical_gate": "BLOCO 2 CANONICAL fact -> BLOCO 3 promotion",\n            "self_model_runtime_state_is_canonical": False,\n            "source": "UniversalKnowledgeArchitecture",\n        }\n'''
new = '''    def knowledge_snapshot(self) -> dict:\n        # Consulta a fonte oficial dinamicamente. Evita ranges hardcoded que ficam\n        # obsoletos conforme novos blocos registram namespaces no BLOCO 3.\n        namespaces = [\n            {\n                "namespace": item["namespace"],\n                "logical_capacity": item.get("logical_capacity"),\n                "registered": True,\n            }\n            for item in self.knowledge.store.list_namespaces()\n        ]\n        return {\n            "registered_namespaces": namespaces,\n            "canonical_gate": "BLOCO 2 CANONICAL fact -> BLOCO 3 promotion",\n            "self_model_runtime_state_is_canonical": False,\n            "source": "UniversalKnowledgeArchitecture",\n        }\n'''
if old in self_text:
    self_text = self_text.replace(old, new, 1)
elif "for item in self.knowledge.store.list_namespaces()" not in self_text:
    raise SystemExit("B15: SelfModel knowledge_snapshot marker not found")
self_path.write_text(self_text, encoding="utf-8")

# --- STAR Core -------------------------------------------------------------
core_path = Path("core/star_core.py")
core = core_path.read_text(encoding="utf-8")
import_marker = "from core.attention_salience import AttentionSalience\n"
new_import = "from core.internal_models import IntegratedInternalModels\n"
if new_import not in core:
    if import_marker not in core:
        raise SystemExit("B15: import marker not found")
    core = core.replace(import_marker, import_marker + new_import, 1)

init_marker = '''        self.mind.attention_salience = self.attention_salience\n\n        self.last_intent = None\n'''
init_block = '''        self.mind.attention_salience = self.attention_salience\n\n        # BLOCO 15: integra os cinco CognitiveModels já existentes no B01. Não\n        # cria frames paralelos; cada modelo referencia as fontes especializadas\n        # e coopera via SITUATION MODEL sobre o mesmo Knowledge Graph.\n        self.internal_models = IntegratedInternalModels(\n            self.knowledge,\n            foundation_models=self.foundations.models,\n            physical_world=self.physical_world,\n            human_life=self.human_life,\n            human_psychology=self.human_psychology,\n            language_communication=self.language_communication,\n            society_culture=self.society_culture,\n            human_contexts=self.human_contexts,\n            everyday_technology=self.everyday_technology,\n            self_model=self.self_model,\n            memory_continuity=self.memory_continuity,\n            attention_salience=self.attention_salience,\n        )\n        self.mind.internal_models = self.internal_models\n\n        self.last_intent = None\n'''
if "self.internal_models = IntegratedInternalModels(" not in core:
    if init_marker not in core:
        raise SystemExit("B15: init marker not found")
    core = core.replace(init_marker, init_block, 1)

handler_marker = '''        attention_action = self.attention_salience.handle(user_input)\n        if attention_action:\n            self.last_intent = "attention_salience"\n            return attention_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
handler_block = '''        attention_action = self.attention_salience.handle(user_input)\n        if attention_action:\n            self.last_intent = "attention_salience"\n            return attention_action\n\n        internal_models_action = self.internal_models.handle(user_input)\n        if internal_models_action:\n            self.last_intent = "internal_models"\n            return internal_models_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
if "internal_models_action = self.internal_models.handle(user_input)" not in core:
    if handler_marker not in core:
        raise SystemExit("B15: handler marker not found")
    core = core.replace(handler_marker, handler_block, 1)
core_path.write_text(core, encoding="utf-8")

# --- Manifest --------------------------------------------------------------
manifest_path = Path("STAR_MIND_MANIFEST.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["schema"] = 16
principles = manifest.setdefault("principles", [])
for principle in (
    "WORLD, HUMAN, SOCIAL, SELF and SITUATION models are cooperating views of one STAR and reuse BLOCO 1 CognitiveModels instead of creating parallel frames",
    "internal models reference shared knowledge, memory and state by provenance/relations instead of indiscriminately copying source datasets",
    "SITUATION MODEL integrates the current bounded context and remains temporary, revisable and non-authorizing",
    "each BLOCO 15 model has 1B logical address capacity while the five-model block has 5B total logical capacity on-demand",
):
    if principle not in principles:
        principles.append(principle)

capacity = manifest["block_3_universal_knowledge"]["namespace_capacity"]
current = capacity.setdefault("current_namespaces", [])
if "B15" not in current:
    current.append("B15")
capacity["truthfulness_note"] = (
    "B01-B14 each expose a 1B logical block space (14B total); B15 exposes five 1B model subspaces (5B); "
    "therefore the integrated architecture represents 19B logical addresses, never 19B preloaded rows/facts"
)

block15 = {
    "status": "experimental-integrated",
    "source_of_truth": "core/internal_models.py coordinating core.foundations.CognitiveModels",
    "integration": "core/star_core.py",
    "namespace": "B15",
    "logical_capacity": 5000000000,
    "models": {
        "WORLD MODEL": 1000000000,
        "HUMAN MODEL": 1000000000,
        "SOCIAL MODEL": 1000000000,
        "SELF MODEL": 1000000000,
        "SITUATION MODEL": 1000000000,
    },
    "reuse": {
        "model_frames": "BLOCO 1 CognitiveModels (exact same object)",
        "world_sources": ["B04 PhysicalWorldModel", "B05 ScientificFoundations", "B11 EverydayTechnologyFoundations"],
        "human_sources": ["B06 HumanLife", "B07 HumanPsychology", "B08 LanguageCommunication", "B10 HumanContext", "B13 Memory"],
        "social_sources": ["B08 LanguageCommunication", "B09 SocietyCulture", "B10 HumanContext", "B13 Social Memory"],
        "self_sources": ["B12 SelfModel", "B13 MemoryContinuity", "B14 AttentionSalience"],
        "situation_sources": ["B01 CognitiveModels.situation", "B12 state/permissions", "B13 recent memory", "B14 attention/salience"],
        "knowledge_graph": "existing knowledge_nodes/knowledge_edges",
        "parallel_models_created": False,
        "source_datasets_copied": False,
        "new_persistence_table_created": False,
    },
    "cooperation": "SITUATION MODEL receives bounded references/context from WORLD, HUMAN, SOCIAL and SELF plus B13/B14; all remain parts of one STAR",
    "model_catalog": {
        "models": 5,
        "areas_per_model": 10,
        "aspects_per_area": 5,
        "lenses_per_aspect": 10,
        "canonical_nodes_per_model": 500,
        "variants_per_node": 2000000,
        "addressable_per_model": 1000000000,
        "total_addressable": 5000000000,
        "materialization": "on-demand",
        "prepopulated_model_rows": 0,
        "truthfulness_note": "5B are virtual model representations over shared sources; not 5B copied facts, memories or database rows",
    },
    "variant_matrix": {
        "epistemic_class": 10,
        "temporal_scope": 10,
        "context_scope": 10,
        "relation_mode": 10,
        "confidence": 5,
        "salience": 4,
        "update_mode": 10,
        "combinations_per_node": 2000000,
    },
    "policy": {
        "model_is_star": False,
        "parallel_models_created": False,
        "copies_source_knowledge": False,
        "situation_is_temporary_and_revisable": True,
        "self_model_redefines_identity": False,
        "operational_authorization": False,
    },
}
new_manifest = {}
inserted = False
for key, value in manifest.items():
    if key == "cognitive_catalog" and not inserted:
        new_manifest["block_15_internal_models"] = block15
        inserted = True
    new_manifest[key] = value
if not inserted:
    new_manifest["block_15_internal_models"] = block15
new_manifest.setdefault("persistence", {})["internal_models"] = (
    "no new table or duplicated model store; B15 delegates runtime frames to B01 CognitiveModels, "
    "references B04-B14 sources and uses the shared Knowledge Graph for taxonomy/relations"
)
manifest_path.write_text(json.dumps(new_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# --- Roadmap ---------------------------------------------------------------
roadmap_path = Path("docs/MASTER_ROADMAP.md")
roadmap = roadmap_path.read_text(encoding="utf-8")
section = r'''
### BLOCO 15 — Cinco Modelos Internos

O BLOCO 15 integra os cinco modelos conceituais que já existem no BLOCO 1:
**WORLD MODEL, HUMAN MODEL, SOCIAL MODEL, SELF MODEL e SITUATION MODEL**. A
implementação central é `core/internal_models.py`, mas os frames continuam sendo
exatamente `FoundationSuite.models` (`CognitiveModels`); não são criados cinco
modelos paralelos.

Cada modelo funciona como uma **visão referencial** sobre fontes já existentes:

```text
WORLD MODEL      -> B04 + B05 + B11
HUMAN MODEL      -> B06 + B07 + B08 + B10 + B13
SOCIAL MODEL     -> B08 + B09 + B10 + B13
SELF MODEL       -> B12 + B13 + B14
SITUATION MODEL  -> WORLD + HUMAN + SOCIAL + SELF + B12/B13/B14
```

O mesmo Knowledge Graph conecta as visões. O B15 registra referências e relações,
não cópias indiscriminadas dos datasets. `record()` e `set_context()` delegam ao
`CognitiveModels` original do B01, então uma atualização via B15 aparece no mesmo
frame visto pelo B01.

O SITUATION MODEL é o ponto de cooperação do momento atual. Ele recebe somente um
contexto bounded: input/objetivo atuais, até 16 entidades, até 16 evidências, até
8 referências recentes de working memory, resumo de atenção/saliência e uma visão
do estado/permissões do Self Model. A situação permanece **temporária e revisável**
e nunca concede autorização operacional.

Cada modelo usa **10 áreas × 5 aspectos × 10 lentes = 500 nós canônicos**. Cada nó
cruza 10 classes epistêmicas × 10 escopos temporais × 10 contextos × 10 relações ×
5 níveis de confiança × 4 níveis de saliência × 10 modos de atualização =
**2.000.000 de variações**.

Portanto:
- WORLD MODEL: 500 × 2M = **1B**;
- HUMAN MODEL: **1B**;
- SOCIAL MODEL: **1B**;
- SELF MODEL: **1B**;
- SITUATION MODEL: **1B**;
- BLOCO 15 total = **5B** de representações lógicas endereçáveis sob demanda.

IDs independentes: `WORLD-B15-*`, `HUMAN-B15-*`, `SOCIAL-B15-*`, `SELF-B15-*` e
`SITUATION-B15-*`, todos de `0000000001` a `1000000000` em seu próprio subespaço.

Com B01–B14 (14B) + os cinco subespaços do B15 (5B), a arquitetura integrada passa
a oferecer **19B de endereços lógicos**. Isso não significa 19B de fatos ou linhas
materializadas. O BLOCO 15 fortalece a fundação dos cinco modelos da MIND, mas não
declara V2.0 completa e não altera o marco oficial V1.9 FINAL → Watch-first → V2.0.

'''
marker = "\n### V2.1\n"
if "### BLOCO 15 — Cinco Modelos Internos" not in roadmap:
    if marker not in roadmap:
        raise SystemExit("B15: roadmap marker not found")
    roadmap = roadmap.replace(marker, "\n" + section + "### V2.1\n", 1)
roadmap_path.write_text(roadmap, encoding="utf-8")
