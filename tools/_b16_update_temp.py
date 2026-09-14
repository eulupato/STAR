from __future__ import annotations

import json
import re
from pathlib import Path

# --- STAR Core -------------------------------------------------------------
core_path = Path("core/star_core.py")
core = core_path.read_text(encoding="utf-8")
import_marker = "from core.internal_models import IntegratedInternalModels\n"
if "from core.social_cognition import SocialCognition\n" not in core:
    if import_marker not in core:
        raise SystemExit("B16: import marker not found")
    core = core.replace(import_marker, import_marker + "from core.social_cognition import SocialCognition\n", 1)

init_marker = "        self.mind.internal_models = self.internal_models\n\n        self.last_intent = None\n"
init_block = '''        self.mind.internal_models = self.internal_models\n\n        # BLOCO 16: interpretação/perspectiva social especializada sobre B07/B09\n        # e os SOCIAL/SITUATION MODEL do B15. Mantém hipóteses alternativas;\n        # intenção, mentira, confiança e reputação nunca viram certeza automática.\n        self.social_cognition = SocialCognition(\n            self.knowledge,\n            human_psychology=self.human_psychology,\n            society_culture=self.society_culture,\n            internal_models=self.internal_models,\n            memory_continuity=self.memory_continuity,\n            attention_salience=self.attention_salience,\n        )\n        self.mind.social_cognition = self.social_cognition\n\n        self.last_intent = None\n'''
if "self.social_cognition = SocialCognition(" not in core:
    if init_marker not in core:
        raise SystemExit("B16: init marker not found")
    core = core.replace(init_marker, init_block, 1)

route_marker = '''        internal_models_action = self.internal_models.handle(user_input)\n        if internal_models_action:\n            self.last_intent = "internal_models"\n            return internal_models_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
route_block = '''        internal_models_action = self.internal_models.handle(user_input)\n        if internal_models_action:\n            self.last_intent = "internal_models"\n            return internal_models_action\n\n        social_cognition_action = self.social_cognition.handle(user_input)\n        if social_cognition_action:\n            self.last_intent = "social_cognition"\n            return social_cognition_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
if "social_cognition_action = self.social_cognition.handle" not in core:
    if route_marker not in core:
        raise SystemExit("B16: route marker not found")
    core = core.replace(route_marker, route_block, 1)
core_path.write_text(core, encoding="utf-8")

# --- MIND manifest ---------------------------------------------------------
manifest_path = Path("STAR_MIND_MANIFEST.json")
data = json.loads(manifest_path.read_text(encoding="utf-8"))
data["schema"] = max(int(data.get("schema", 0)), 17)
principles = data.setdefault("principles", [])
for item in (
    "social inference remains hypothesis/context and never becomes fact merely from behavior or social signals",
    "intention, deception, lie, secrecy, trust and reputation preserve alternative explanations and uncertainty",
    "functional empathy supports perspective-taking but is not mind reading",
    "trust, reputation, persuasion, urgency or social salience never grant operational permission",
):
    if item not in principles:
        principles.append(item)

data["block_16_social_cognition"] = {
    "status": "experimental-integrated",
    "source_of_truth": "core/social_cognition.py",
    "integration": "core/star_core.py",
    "namespace": "B16",
    "logical_capacity": 1000000000,
    "requested_topics": [
        "theory of mind", "perspective", "expectation", "intention", "deception", "lie", "secret",
        "trust", "reputation", "cooperation", "competition", "negotiation", "persuasion", "manipulation",
        "responsibility", "functional empathy", "relationships"
    ],
    "reuse": {
        "psychology_social_cognition": "BLOCO 7 HumanPsychologyFoundations",
        "society_culture": "BLOCO 9 SocietyCultureFoundations",
        "social_memory": "BLOCO 13 MemoryContinuity",
        "attention_selection": "BLOCO 14 AttentionSalience",
        "social_situation_models": "BLOCO 15 existing SOCIAL/SITUATION MODEL views",
        "knowledge_graph": "existing knowledge_nodes/knowledge_edges",
        "parallel_social_model_created": False,
        "mind_reading_engine_created": False,
        "new_persistence_table_created": False
    },
    "interpretation_policy": {
        "social_inference_is_fact": False,
        "isolated_signal_proves_intention": False,
        "deception_signal_proves_lie": False,
        "lie_requires_belief_and_intent_evidence": True,
        "reputation_is_fact": False,
        "trust_grants_permission": False,
        "empathy_is_mind_reading": False,
        "manipulation_analysis_provides_exploitation_tactics": False,
        "operational_authorization": False
    },
    "social_cognition_catalog": {
        "domains": 10,
        "branches": 50,
        "lenses_per_branch": 10,
        "canonical_nodes": 500,
        "variants_per_node": 2000000,
        "addressable_contents": 1000000000,
        "materialization": "on-demand",
        "prepopulated_social_situations": 0,
        "truthfulness_note": "1B are addressable social interpretations and hypotheses, not 1B proven intentions, lies, reputations or personal profiles"
    },
    "variant_matrix": {
        "perspective": 10,
        "intention_hypothesis": 10,
        "context": 10,
        "evidence": 10,
        "relationship": 10,
        "temporal_scope": 10,
        "interpretation_mode": 2,
        "combinations_per_node": 2000000
    }
}

# Update any existing explicit namespace lists without creating a competing field.
def append_namespace(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "current_namespaces" and isinstance(value, list) and "B16" not in value:
                value.append("B16")
            append_namespace(value)
    elif isinstance(obj, list):
        for value in obj:
            append_namespace(value)
append_namespace(data)
manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# --- Roadmap ---------------------------------------------------------------
roadmap_path = Path("docs/MASTER_ROADMAP.md")
roadmap = roadmap_path.read_text(encoding="utf-8")
section = r'''### BLOCO 16 — Interpretação, Perspectiva e Cognição Social

O BLOCO 16 especializa a cognição social já existente sem criar outro SOCIAL
MODEL. Ele reutiliza B07 (psicologia/teoria da mente), B09 (sociedade/cultura),
B13 (memória social), B14 (atenção/saliência) e os SOCIAL/SITUATION MODEL do B15.

Cobertura central:

- teoria da mente, perspectiva e expectativa;
- intenção como hipótese, nunca leitura mental automática;
- engano, mentira, segredo e assimetria de informação;
- confiança e reputação contextuais e revisáveis;
- cooperação, competição, negociação e coordenação;
- persuasão/influência e detecção protetiva de manipulação;
- responsabilidade, agência e prestação de contas;
- empatia funcional e tomada de perspectiva;
- relações, papéis, limites, consentimento e mudança relacional.

Regras permanentes:

```text
INFERÊNCIA SOCIAL ≠ FATO
INTENÇÃO ≠ CERTEZA
SINAL DE ENGANO ≠ PROVA DE MENTIRA
REPUTAÇÃO ≠ FATO
CONFIANÇA ≠ PERMISSÃO
EMPATIA ≠ LEITURA MENTAL
```

Manipulação é modelada para reconhecimento, contexto, risco, autonomia e proteção;
o BLOCO 16 não transforma esse conhecimento em um catálogo operacional de técnicas
de exploração social.

Escala lógica B16:

- **50 ramos × 10 lentes = 500 nós canônicos**;
- perspectiva(10) × hipótese de intenção(10) × contexto(10) × evidência(10) ×
  relação(10) × tempo(10) × interpretação primária/alternativa(2) = **2M** por nó;
- **500 × 2M = 1.000.000.000** representações `SOC-B16-*` endereçáveis sob demanda.

O 1B representa situações, perspectivas e hipóteses sociais combináveis; não 1B de
intenções privadas conhecidas, mentiras comprovadas, reputações verdadeiras ou
perfis pessoais pré-carregados.

'''
if "### BLOCO 16 — Interpretação, Perspectiva e Cognição Social" not in roadmap:
    marker = "## V2.1"
    pos = roadmap.find(marker)
    if pos == -1:
        raise SystemExit("B16: V2.1 roadmap marker not found")
    roadmap = roadmap[:pos] + section + roadmap[pos:]

# Remove one known stale namespace enumeration left from early B03 documentation.
roadmap = re.sub(
    r"`B01`, `B02`, `B03`,\n`B04`, `B05`, `B06`, `B07`, `B08`, `B09` e `B10` registram cada um capacidade lógica própria de\n\*\*1B\*\*; blocos futuros podem registrar novos namespaces de 1B sem alteração de\nschema ou colisão de IDs\.",
    "`B01` até `B16` usam a mesma arquitetura de namespaces lógicos conforme cada bloco integrado; B15 expõe cinco subespaços de 1B sobre fontes compartilhadas. Novos blocos podem continuar crescendo sem materializar bilhões de linhas ou criar schemas paralelos.",
    roadmap,
)
roadmap_path.write_text(roadmap, encoding="utf-8")
