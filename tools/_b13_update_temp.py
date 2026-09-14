from __future__ import annotations

import json
from pathlib import Path


# ---- core/mind.py ---------------------------------------------------------
mind_path = Path("core/mind.py")
mind = mind_path.read_text(encoding="utf-8")
old_kinds = '    KINDS = {"working", "episodic", "semantic", "conversation", "project", "decision", "error", "temporal", "people", "object", "preference"}'
new_kinds = '    KINDS = {"working", "episodic", "semantic", "conversation", "project", "decision", "error", "temporal", "people", "object", "social", "autobiographical", "preference"}'
if old_kinds in mind:
    mind = mind.replace(old_kinds, new_kinds, 1)
elif new_kinds not in mind:
    raise SystemExit("B13: CognitiveMemory.KINDS marker not found")
mind_path.write_text(mind, encoding="utf-8")


# ---- database/cognitive_store.py -----------------------------------------
store_path = Path("database/cognitive_store.py")
store = store_path.read_text(encoding="utf-8")
marker = "    def upsert_node(self, node_id: str, node_type: str, label: str, *, data=None, confidence: float = 1.0):\n"
methods = '''    def memory_by_id(self, memory_id: int) -> dict | None:\n        with engine.connect() as conn:\n            row = conn.execute(text(\"\"\"\n                SELECT id, kind, memory_key, content, metadata_json, importance, created_at, updated_at\n                FROM cognitive_memory WHERE id=:id\n            \"\"\"), {\"id\": int(memory_id)}).mappings().first()\n        return None if row is None else {**dict(row), \"metadata\": _load(row[\"metadata_json\"])}\n\n    def memory_counts(self) -> dict:\n        with engine.connect() as conn:\n            rows = conn.execute(text(\"\"\"\n                SELECT kind, COUNT(*) AS count\n                FROM cognitive_memory\n                GROUP BY kind\n                ORDER BY kind\n            \"\"\")).mappings().all()\n        by_kind = {str(row[\"kind\"]): int(row[\"count\"]) for row in rows}\n        return {\"total\": sum(by_kind.values()), \"by_kind\": by_kind}\n\n'''
if "    def memory_by_id(self, memory_id: int)" not in store:
    if marker not in store:
        raise SystemExit("B13: CognitiveStore insertion marker not found")
    store = store.replace(marker, methods + marker, 1)
store_path.write_text(store, encoding="utf-8")


# ---- core/star_core.py ----------------------------------------------------
core_path = Path("core/star_core.py")
core = core_path.read_text(encoding="utf-8")
import_marker = "from core.mind import CognitiveSuite\n"
new_import = "from core.memory_continuity import MemoryContinuity\n"
if new_import not in core:
    if import_marker not in core:
        raise SystemExit("B13: StarCore import marker not found")
    core = core.replace(import_marker, new_import + import_marker, 1)

init_marker = "        self.mind.self_model = self.self_model\n\n        self.last_intent = None\n"
init_block = '''        self.mind.self_model = self.self_model\n\n        # BLOCO 13: memória e continuidade. Evolui CognitiveMemory/cognitive_memory\n        # e usa o mesmo Knowledge Graph; working memory é bounded/transitória e\n        # autobiografia só aceita fontes/referências auditáveis.\n        self.memory_continuity = MemoryContinuity(\n            self.knowledge,\n            memory=self.mind.memory,\n            graph=self.mind.graph,\n            projects=self.mind.projects,\n            self_model=self.self_model,\n        )\n        self.mind.memory_continuity = self.memory_continuity\n\n        self.last_intent = None\n'''
if "self.memory_continuity = MemoryContinuity(" not in core:
    if init_marker not in core:
        raise SystemExit("B13: StarCore init marker not found")
    core = core.replace(init_marker, init_block, 1)

handler_marker = '''        self_model_action = self.self_model.handle(user_input)\n        if self_model_action:\n            self.last_intent = "self_model"\n            return self_model_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
handler_block = '''        self_model_action = self.self_model.handle(user_input)\n        if self_model_action:\n            self.last_intent = "self_model"\n            return self_model_action\n\n        memory_action = self.memory_continuity.handle(user_input)\n        if memory_action:\n            self.last_intent = "memory_continuity"\n            return memory_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
if "memory_action = self.memory_continuity.handle(user_input)" not in core:
    if handler_marker not in core:
        raise SystemExit("B13: StarCore handler marker not found")
    core = core.replace(handler_marker, handler_block, 1)
core_path.write_text(core, encoding="utf-8")


# ---- STAR_MIND_MANIFEST.json ---------------------------------------------
manifest_path = Path("STAR_MIND_MANIFEST.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["schema"] = 14
principles = manifest.setdefault("principles", [])
for principle in (
    "memory is contextual evidence and never becomes fact merely because it was stored or recalled",
    "working memory is bounded and transient by default; persistence requires an explicit memory write",
    "memory consolidation preserves source memories and records derivation instead of silently overwriting history",
    "autobiographical memory and experiences require auditable source/reference and are never fabricated for continuity",
    "people memory does not infer sensitive attributes automatically and memory retrieval never grants operational authorization",
):
    if principle not in principles:
        principles.append(principle)

namespace_capacity = manifest["block_3_universal_knowledge"]["namespace_capacity"]
current = namespace_capacity.setdefault("current_namespaces", [])
if "B13" not in current:
    current.append("B13")
namespace_capacity["truthfulness_note"] = (
    "each 1B is logical capacity per block namespace, not a billion preloaded rows; "
    "integrated B01-B13 therefore represent 13B logical addresses with only materialized knowledge persisted"
)

block13 = {
    "status": "experimental-integrated",
    "source_of_truth": "core/memory_continuity.py",
    "integration": "core/star_core.py",
    "namespace": "B13",
    "database": "same star.db through existing cognitive_memory plus BLOCO 3 for canonical memory knowledge",
    "memory_types": [
        "working memory", "episodic memory", "semantic memory", "conversation memory", "project memory",
        "people memory", "object memory", "social memory", "autobiographical memory", "temporal memory"
    ],
    "memory_dimensions": [
        "events", "entities", "dates", "relations", "locations", "importance", "context", "experience", "sources", "meaning"
    ],
    "reuse": {
        "persistent_memory": "existing cognitive_memory table via CognitiveMemory/CognitiveStore",
        "working_memory": "bounded transient WorkingMemoryBuffer",
        "knowledge_graph": "existing knowledge_nodes/knowledge_edges",
        "projects": "existing CognitiveSuite.projects",
        "self_history": "BLOCO 12 SelfHistory when explicitly imported",
        "canonical_knowledge": "BLOCO 2 -> BLOCO 3",
        "parallel_database_created": False,
        "parallel_graph_created": False,
    },
    "continuity_policy": {
        "working_memory_persistent_by_default": False,
        "memory_equals_fact": False,
        "retrieval_equals_truth": False,
        "consolidation_overwrites_sources": False,
        "autobiographical_experience_may_be_fabricated": False,
        "autobiographical_experience_requires_reference": True,
        "memory_grants_operational_authorization": False,
    },
    "memory_catalog": {
        "memory_types": 10,
        "branches": 50,
        "lenses_per_branch": 10,
        "canonical_nodes": 500,
        "variants_per_node": 2000000,
        "addressable_contents": 1000000000,
        "materialization": "on-demand",
        "prepopulated_memory_rows": 0,
        "truthfulness_note": "1B are deterministic addressable memory/context/retrieval/consolidation representations, not 1B fabricated memories or physical database rows",
    },
    "variant_matrix": {
        "retention_scope": 10,
        "retrieval_mode": 10,
        "relation_mode": 10,
        "temporal_scope": 10,
        "source_quality": 5,
        "context_scope": 4,
        "consolidation_stage": 10,
        "combinations_per_node": 2000000,
    },
}

new_manifest = {}
inserted = False
for key, value in manifest.items():
    if key == "cognitive_catalog" and not inserted:
        new_manifest["block_13_memory_continuity"] = block13
        inserted = True
    new_manifest[key] = value
if not inserted:
    new_manifest["block_13_memory_continuity"] = block13

persistence = new_manifest.setdefault("persistence", {})
persistence["memory_continuity"] = (
    "no parallel memory database/table; B13 extends the existing cognitive_memory store, uses a bounded transient working buffer, "
    "and stores memory relations/consolidation provenance in the shared Knowledge Graph; canonical memory knowledge still requires B02/B03"
)
manifest_path.write_text(json.dumps(new_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---- docs/MASTER_ROADMAP.md ----------------------------------------------
roadmap_path = Path("docs/MASTER_ROADMAP.md")
roadmap = roadmap_path.read_text(encoding="utf-8")
section = r'''
### BLOCO 13 — Memória e Continuidade

O BLOCO 13 transforma a capacidade de memória já presente na MIND em uma
arquitetura integrada de continuidade, sem criar `memory_v2`, outro banco ou um
grafo paralelo. A base persistente continua sendo `cognitive_memory` no mesmo
`star.db`; relações, entidades, locais, datas e derivações de consolidação usam o
Knowledge Graph oficial. A implementação central é `core/memory_continuity.py`.

São integrados dez tipos: **working, episodic, semantic, conversation, project,
people, object, social, autobiographical e temporal memory**. Eventos, entidades,
datas, relações, locais, importância, contexto, experiência, fontes e significado
permanecem explícitos como dimensões da memória.

Working memory é um buffer pequeno e bounded, transitório por padrão. Guardar algo
na working memory **não** materializa automaticamente uma linha persistente. A
persistência exige escrita explícita. Memórias de longo prazo reutilizam
`CognitiveMemory`/`CognitiveStore`; `social` e `autobiographical` passam a ser tipos
válidos do mesmo store em vez de sistemas separados.

Consolidação cria uma nova memória derivada e registra `derived_from` no grafo. As
memórias de origem permanecem intactas. Recuperar uma memória não a transforma em
fato: memória, observação, conhecimento canônico e inferência continuam separados.
Conhecimento canônico sobre memória continua exigindo claim `CANONICAL` no BLOCO 2
e promoção pelo BLOCO 3.

A memória autobiográfica preserva a regra do BLOCO 12: experiências da STAR exigem
**fonte + referência auditável**. O B13 pode importar explicitamente eventos do
`SelfHistory`, mas não fabrica uma autobiografia para preencher lacunas. People
memory não infere atributos sensíveis automaticamente, e nenhuma lembrança concede
autorização operacional.

Taxonomia:

```text
MEMÓRIA E CONTINUIDADE
↓
TIPO DE MEMÓRIA
↓
RAMO
↓
EVENTO / ENTIDADE / TEMPO / RELAÇÃO / LOCAL / IMPORTÂNCIA / CONTEXTO / EXPERIÊNCIA / FONTE / SIGNIFICADO
```

Escala B13:

- **10 tipos × 5 ramos = 50 ramos**;
- **50 ramos × 10 lentes = 500 nós canônicos**;
- por nó: **10 retenções × 10 modos de recuperação × 10 modos de relação × 10
  escopos temporais × 5 qualidades de fonte × 4 contextos × 10 estágios de
  consolidação = 2.000.000 de variações**;
- **500 × 2.000.000 = 1.000.000.000 de representações endereçáveis em `B13`**;
- IDs `MEM-B13-0000000001` até `MEM-B13-1000000000`;
- materialização sob demanda; zero requisito de 1B de lembranças ou linhas físicas.

Com B13, B01–B13 oferecem **13B de endereços lógicos independentes**. O bloco é a
fundação integrada da futura **V2.1 Memory Architecture**, mas não declara V2.1
completa: políticas maduras de retenção/esquecimento, indexação semântica avançada,
embeddings e manutenção de memória em grande escala continuam como evolução futura.

'''
marker = "\n### V2.1\n"
if "### BLOCO 13 — Memória e Continuidade" not in roadmap:
    if marker not in roadmap:
        raise SystemExit("B13: roadmap V2.1 marker not found")
    roadmap = roadmap.replace(marker, "\n" + section + "### V2.1\n", 1)
roadmap_path.write_text(roadmap, encoding="utf-8")
