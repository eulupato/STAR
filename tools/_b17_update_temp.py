from __future__ import annotations

import json
from pathlib import Path

# --- CognitiveStore: key-based append-only memory retrieval ----------------
store_path = Path("database/cognitive_store.py")
store = store_path.read_text(encoding="utf-8")
marker = '''    def memory_counts(self) -> dict:\n'''
methods = '''    def memory_by_key(self, memory_key: str, *, kind: str | None = None) -> dict | None:\n        key = str(memory_key or "").strip()\n        if not key:\n            raise ValueError("memory_key vazio")\n        params = {"key": key}\n        kind_clause = ""\n        if kind is not None:\n            params["kind"] = str(kind)\n            kind_clause = " AND kind=:kind"\n        with engine.connect() as conn:\n            row = conn.execute(text(f"""\n                SELECT id, kind, memory_key, content, metadata_json, importance, created_at, updated_at\n                FROM cognitive_memory\n                WHERE memory_key=:key{kind_clause}\n                ORDER BY id DESC LIMIT 1\n            """), params).mappings().first()\n        return None if row is None else {**dict(row), "metadata": _load(row["metadata_json"])}\n\n    def memory_history(self, memory_key: str, *, kind: str | None = None, limit: int = 50) -> list[dict]:\n        key = str(memory_key or "").strip()\n        if not key:\n            raise ValueError("memory_key vazio")\n        params = {"key": key, "limit": max(1, min(int(limit), 500))}\n        kind_clause = ""\n        if kind is not None:\n            params["kind"] = str(kind)\n            kind_clause = " AND kind=:kind"\n        with engine.connect() as conn:\n            rows = conn.execute(text(f"""\n                SELECT id, kind, memory_key, content, metadata_json, importance, created_at, updated_at\n                FROM cognitive_memory\n                WHERE memory_key=:key{kind_clause}\n                ORDER BY id DESC LIMIT :limit\n            """), params).mappings().all()\n        return [{**dict(row), "metadata": _load(row["metadata_json"])} for row in rows]\n\n'''
if "def memory_by_key(" not in store:
    if marker not in store:
        raise SystemExit("B17: CognitiveStore marker not found")
    store = store.replace(marker, methods + marker, 1)
store_path.write_text(store, encoding="utf-8")

# --- STAR Core -------------------------------------------------------------
core_path = Path("core/star_core.py")
core = core_path.read_text(encoding="utf-8")
import_marker = "from core.attention_salience import AttentionSalience\n"
if "from core.affective_personality import AffectivePersonality\n" not in core:
    if import_marker not in core:
        raise SystemExit("B17: import marker not found")
    core = core.replace(import_marker, import_marker + "from core.affective_personality import AffectivePersonality\n", 1)

init_marker = '''        self.mind.social_cognition = self.social_cognition\n\n        self.last_intent = None\n'''
init_block = '''        self.mind.social_cognition = self.social_cognition\n\n        # BLOCO 17: afeto e personalidade persistente. Estados transitórios\n        # continuam no StarState; baselines/preferências ficam no cognitive_memory\n        # existente. Identidade, valores e permissões continuam sob autoridade B12.\n        self.affective_personality = AffectivePersonality(\n            self.knowledge,\n            state=self.state,\n            memory_continuity=self.memory_continuity,\n            self_model=self.self_model,\n            internal_models=self.internal_models,\n            social_cognition=self.social_cognition,\n        )\n        self.mind.affective_personality = self.affective_personality\n\n        self.last_intent = None\n'''
if "self.affective_personality = AffectivePersonality(" not in core:
    if init_marker not in core:
        raise SystemExit("B17: init marker not found")
    core = core.replace(init_marker, init_block, 1)

route_marker = '''        social_cognition_action = self.social_cognition.handle(user_input)\n        if social_cognition_action:\n            self.last_intent = "social_cognition"\n            return social_cognition_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
route_block = '''        social_cognition_action = self.social_cognition.handle(user_input)\n        if social_cognition_action:\n            self.last_intent = "social_cognition"\n            return social_cognition_action\n\n        personality_action = self.affective_personality.handle(user_input)\n        if personality_action:\n            self.last_intent = "affective_personality"\n            return personality_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
if "personality_action = self.affective_personality.handle" not in core:
    if route_marker not in core:
        raise SystemExit("B17: route marker not found")
    core = core.replace(route_marker, route_block, 1)
core_path.write_text(core, encoding="utf-8")

# --- Manifest --------------------------------------------------------------
manifest_path = Path("STAR_MIND_MANIFEST.json")
data = json.loads(manifest_path.read_text(encoding="utf-8"))
data["schema"] = max(int(data.get("schema", 0)), 18)
principles = data.setdefault("principles", [])
for item in (
    "affect and adaptive personality remain distinct from the official STAR identity and fundamental values",
    "persistent personality is represented in audited memory/history rather than existing only as a prompt",
    "personality adaptation is bounded, append-only and linked to auditable experiences; previous states remain recoverable",
    "preferences, style, confidence, familiarity and affect never grant operational permission",
):
    if item not in principles:
        principles.append(item)

data["block_17_affective_personality"] = {
    "status": "experimental-integrated",
    "source_of_truth": "core/affective_personality.py",
    "integration": "core/star_core.py",
    "namespace": "B17",
    "logical_capacity": 1000000000,
    "requested_components": [
        "valence", "energy", "curiosity", "caution", "familiarity", "confidence", "interest", "alert",
        "preferences", "style", "history", "relationships", "experiences", "adaptive personality"
    ],
    "persistence": {
        "store": "existing cognitive_memory",
        "lookup": "memory_key + latest/history accessors on CognitiveStore",
        "append_only_history": True,
        "new_table_created": False,
        "new_database_created": False,
        "prompt_only": False
    },
    "reuse": {
        "transient_energy_curiosity_confidence": "existing core.state.StarState",
        "experiences_relationships": "BLOCO 13 MemoryContinuity",
        "identity_values_limits_permissions": "BLOCO 12 SelfModel/core.star_identity",
        "self_and_situation_views": "BLOCO 15 IntegratedInternalModels",
        "social_context": "BLOCO 16 SocialCognition",
        "knowledge_graph": "existing knowledge_nodes/knowledge_edges"
    },
    "adaptation_policy": {
        "max_learning_rate_per_experience": 0.1,
        "auditable_experience_required": True,
        "identity_mutation": False,
        "fundamental_values_mutation": False,
        "permission_mutation": False,
        "source_memory_preserved": True,
        "operational_authorization": False
    },
    "catalog": {
        "domains": 10,
        "branches": 50,
        "lenses_per_branch": 10,
        "canonical_nodes": 500,
        "variants_per_node": 2000000,
        "addressable_contents": 1000000000,
        "materialization": "on-demand",
        "prepopulated_personality_states": 0,
        "truthfulness_note": "1B are addressable affect/personality representations, not 1B fabricated experiences or physically stored personality rows"
    },
    "variant_matrix": {
        "context": 10,
        "valence_state": 10,
        "energy_state": 10,
        "familiarity_state": 10,
        "confidence_state": 10,
        "experience_state": 10,
        "adaptation_mode": 2,
        "combinations_per_node": 2000000
    }
}

def append_namespace(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "current_namespaces" and isinstance(value, list) and "B17" not in value:
                value.append("B17")
            append_namespace(value)
    elif isinstance(obj, list):
        for value in obj:
            append_namespace(value)
append_namespace(data)
manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# --- Roadmap ---------------------------------------------------------------
roadmap_path = Path("docs/MASTER_ROADMAP.md")
roadmap = roadmap_path.read_text(encoding="utf-8")
section = r'''### BLOCO 17 — Modelo Afetivo e Personalidade

O BLOCO 17 transforma afeto/personalidade em estado e memória persistentes sem
criar outra identidade ou outro banco. A personalidade deixa de ser tratável como
um simples prompt: seus baselines, preferências, estilos e revisões são registros
auditáveis append-only no `cognitive_memory` oficial.

Integra:

- valência, energia, curiosidade, cautela, familiaridade, confiança, interesse e alerta;
- preferências e estilo persistentes;
- história, relações e experiências auditáveis;
- personalidade adaptativa com mudanças pequenas e reversíveis;
- `StarState` para energia/curiosidade/confiança transitórias;
- B12 para identidade, valores, limites e permissões;
- B13 para experiências/relações e continuidade;
- B15 para SELF/SITUATION MODEL;
- B16 para contexto social;
- mesmo Knowledge Graph compartilhado.

Regras permanentes:

```text
AFETO ≠ IDENTIDADE
PERSONALIDADE ≠ IDENTIDADE OFICIAL
PREFERÊNCIA ≠ REGRA FUNDAMENTAL
CONFIANÇA ≠ PERMISSÃO
EXPERIÊNCIA SEM FONTE/REFERÊNCIA ≠ AUTOBIOGRAFIA
```

A adaptação exige uma memória autobiográfica auditável já existente, usa taxa de
aprendizado limitada a no máximo **0,1 por experiência**, cria um novo registro e
preserva o estado anterior. B17 não pode alterar automaticamente `core.star_identity`,
valores fundamentais, permissões ou regras de segurança.

Escala lógica B17:

- **50 ramos × 10 lentes = 500 nós canônicos**;
- contexto(10) × valência(10) × energia(10) × familiaridade(10) × confiança(10) ×
  experiência(10) × adaptação(2) = **2M** por nó;
- **500 × 2M = 1.000.000.000** representações `PERS-B17-*` sob demanda.

O 1B representa estados, relações, experiências e combinações de personalidade
endereçáveis; não significa 1B de experiências fabricadas ou registros físicos.

'''
if "### BLOCO 17 — Modelo Afetivo e Personalidade" not in roadmap:
    marker = "## V2.1"
    pos = roadmap.find(marker)
    if pos == -1:
        raise SystemExit("B17: roadmap V2.1 marker not found")
    roadmap = roadmap[:pos] + section + roadmap[pos:]
roadmap_path.write_text(roadmap, encoding="utf-8")
