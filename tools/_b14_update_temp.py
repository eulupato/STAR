from __future__ import annotations

import json
from pathlib import Path

# STAR Core
core_path = Path("core/star_core.py")
core = core_path.read_text(encoding="utf-8")
import_marker = "from core.agents import AgentManager\n"
new_import = "from core.attention_salience import AttentionSalience\n"
if new_import not in core:
    if import_marker not in core:
        raise SystemExit("B14 import marker not found")
    core = core.replace(import_marker, import_marker + new_import, 1)

init_marker = "        self.mind.memory_continuity = self.memory_continuity\n\n        self.last_intent = None\n"
init_block = '''        self.mind.memory_continuity = self.memory_continuity\n\n        # BLOCO 14: atenção/saliência sobre a working memory do B13 e o StarState\n        # oficial. Seleção é bounded e nunca concede autorização operacional.\n        self.attention_salience = AttentionSalience(\n            self.knowledge,\n            memory_continuity=self.memory_continuity,\n            state=self.state,\n            self_model=self.self_model,\n        )\n        self.mind.attention_salience = self.attention_salience\n\n        self.last_intent = None\n'''
if "self.attention_salience = AttentionSalience(" not in core:
    if init_marker not in core:
        raise SystemExit("B14 init marker not found")
    core = core.replace(init_marker, init_block, 1)

handler_marker = '''        memory_action = self.memory_continuity.handle(user_input)\n        if memory_action:\n            self.last_intent = "memory_continuity"\n            return memory_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
handler_block = '''        memory_action = self.memory_continuity.handle(user_input)\n        if memory_action:\n            self.last_intent = "memory_continuity"\n            return memory_action\n\n        attention_action = self.attention_salience.handle(user_input)\n        if attention_action:\n            self.last_intent = "attention_salience"\n            return attention_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
if "attention_action = self.attention_salience.handle(user_input)" not in core:
    if handler_marker not in core:
        raise SystemExit("B14 handler marker not found")
    core = core.replace(handler_marker, handler_block, 1)
core_path.write_text(core, encoding="utf-8")

# Manifest
manifest_path = Path("STAR_MIND_MANIFEST.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["schema"] = 15
principles = manifest.setdefault("principles", [])
for principle in (
    "attention and salience rank what to analyze first but do not determine truth or operational authority",
    "BLOCO 14 reuses BLOCO 13 working memory and core.state.StarState instead of creating parallel attention state",
    "candidate selection is bounded/top-k and never requires loading the billion-address logical space simultaneously",
    "risk and urgency may raise cognitive priority but never grant permission or bypass safety",
):
    if principle not in principles:
        principles.append(principle)

capacity = manifest["block_3_universal_knowledge"]["namespace_capacity"]
current = capacity.setdefault("current_namespaces", [])
if "B14" not in current:
    current.append("B14")
capacity["truthfulness_note"] = (
    "each 1B is logical capacity per block namespace, not a billion preloaded rows; "
    "integrated B01-B14 therefore represent 14B logical addresses with only materialized knowledge persisted"
)
block14 = {
    "status": "experimental-integrated",
    "source_of_truth": "core/attention_salience.py",
    "integration": "core/star_core.py",
    "namespace": "B14",
    "requested_topics": [
        "attention", "salience", "priority", "active goals", "active entities", "recent context",
        "hypotheses", "temporary results", "risks", "urgency"
    ],
    "reuse": {
        "working_memory": "BLOCO 13 WorkingMemoryBuffer",
        "attention_state": "core.state.StarState",
        "self_objectives": "BLOCO 12 when relevant",
        "knowledge_graph": "existing knowledge_nodes/knowledge_edges",
        "parallel_working_memory_created": False,
        "parallel_state_created": False,
        "new_persistence_table_created": False,
    },
    "selection_policy": {
        "bounded_candidate_window": True,
        "loads_all_available_contents": False,
        "selection_is_fact": False,
        "selection_is_operational_authorization": False,
        "salience_grants_permission": False,
        "risk_grants_permission": False,
        "urgency_grants_permission": False,
        "risk_may_raise_attention": True,
    },
    "attention_catalog": {
        "domains": 10,
        "branches": 50,
        "lenses_per_branch": 10,
        "canonical_nodes": 500,
        "variants_per_node": 2000000,
        "addressable_contents": 1000000000,
        "materialization": "on-demand",
        "preloaded_candidates": 0,
        "truthfulness_note": "1B are deterministic addressable attention/salience states, not 1B simultaneously loaded candidates",
    },
    "variant_matrix": {
        "candidate_source": 10,
        "goal_alignment": 10,
        "recency": 10,
        "risk": 10,
        "urgency": 5,
        "confidence": 4,
        "attention_state": 10,
        "combinations_per_node": 2000000,
    },
}
new_manifest = {}
inserted = False
for key, value in manifest.items():
    if key == "cognitive_catalog" and not inserted:
        new_manifest["block_14_attention_salience"] = block14
        inserted = True
    new_manifest[key] = value
if not inserted:
    new_manifest["block_14_attention_salience"] = block14
new_manifest.setdefault("persistence", {})["attention_salience"] = (
    "no new table; B14 state is bounded/transient, reuses B13 working memory and StarState, "
    "and uses the shared Knowledge Graph only for taxonomy/relations"
)
manifest_path.write_text(json.dumps(new_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Roadmap
roadmap_path = Path("docs/MASTER_ROADMAP.md")
roadmap = roadmap_path.read_text(encoding="utf-8")
section = r'''
### BLOCO 14 — Working Memory, Attention e Salience

O BLOCO 14 adiciona seleção cognitiva de relevância sobre a working memory do
BLOCO 13 e sobre o `StarState` já existente. Não cria uma segunda working memory,
um segundo estado interno ou uma tabela de atenção. A implementação central é
`core/attention_salience.py`.

A arquitetura cobre **atenção, saliência, prioridade, objetivos ativos, entidades
ativas, contexto recente, hipóteses, resultados temporários, riscos e urgência**.
Objetivos, entidades, hipóteses e resultados temporários são papéis dentro do mesmo
`WorkingMemoryBuffer` bounded do B13. `attention`, `focus`, `cognitive_load` e
`energy` são observados em `core.state.StarState`.

O motor de seleção recebe somente uma janela limitada de candidatos, calcula
relevância e devolve `top-k`. Ele nunca percorre ou carrega o espaço lógico de 1B
de conteúdos de uma vez. O score combina prioridade explícita, saliência,
relevância para objetivos e entidades, recência, risco, urgência e confiança.
Risco/urgência podem elevar a ordem de análise, mas **não concedem permissão nem
autorização operacional**.

Regras permanentes:

```text
SALIÊNCIA ≠ VERDADE
PRIORIDADE ≠ PERMISSÃO
URGÊNCIA ≠ AUTORIZAÇÃO
RISCO PODE ELEVAR ATENÇÃO, MAS NÃO IGNORA SEGURANÇA
SELEÇÃO = INFERÊNCIA COGNITIVA TRANSITÓRIA
1B DISPONÍVEIS ≠ 1B CARREGADOS SIMULTANEAMENTE
```

Escala B14:
- 10 domínios × 5 ramos = 50 ramos;
- 50 × 10 lentes = 500 nós canônicos;
- 10 fontes × 10 alinhamentos × 10 recências × 10 riscos × 5 urgências ×
  4 confianças × 10 estados de atenção = 2.000.000 variações por nó;
- 500 × 2.000.000 = **1.000.000.000** representações endereçáveis em B14;
- IDs `ATTN-B14-0000000001` até `ATTN-B14-1000000000`;
- materialização sob demanda e seleção bounded/top-k.

Com B14, B01–B14 oferecem 14B de endereços lógicos independentes. Este bloco
fortalece a fundação da MIND V2.0, mas não declara V2.0 completa.

'''
marker = "\n### V2.1\n"
if "### BLOCO 14 — Working Memory, Attention e Salience" not in roadmap:
    if marker not in roadmap:
        raise SystemExit("B14 roadmap marker not found")
    roadmap = roadmap.replace(marker, "\n" + section + "### V2.1\n", 1)
roadmap_path.write_text(roadmap, encoding="utf-8")
