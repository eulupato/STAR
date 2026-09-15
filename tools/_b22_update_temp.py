from __future__ import annotations
import json
from pathlib import Path

core_path=Path("core/star_core.py"); core=core_path.read_text(encoding="utf-8")
marker="from core.language_manager import LanguageManager\n"
if "from core.knowledge_integration import KnowledgeIntegrationEngine\n" not in core:
    if marker not in core: raise SystemExit("B22 import marker missing")
    core=core.replace(marker,"from core.knowledge_integration import KnowledgeIntegrationEngine\n"+marker,1)
init_marker='''        self.mind.learning_evolution = self.learning_evolution\n\n        self.last_intent = None\n'''
init_block='''        self.mind.learning_evolution = self.learning_evolution\n\n        # BLOCO 22: integração ativa do conhecimento nos mesmos cinco modelos B15.\n        # Relações, expectativas, previsões, interpretações, contexto e julgamentos\n        # são atualizados por referência, sem copiar datasets ou redefinir identidade.\n        self.knowledge_integration = KnowledgeIntegrationEngine(\n            self.knowledge,\n            internal_models=self.internal_models,\n            metacognition=self.metacognition,\n            learning_evolution=self.learning_evolution,\n            reasoning_simulation=self.reasoning_simulation,\n            attention_salience=self.attention_salience,\n        )\n        self.mind.knowledge_integration = self.knowledge_integration\n\n        self.last_intent = None\n'''
if "self.knowledge_integration = KnowledgeIntegrationEngine(" not in core:
    if init_marker not in core: raise SystemExit("B22 init marker missing")
    core=core.replace(init_marker,init_block,1)
route_marker='''        learning_action = self.learning_evolution.handle(user_input)\n        if learning_action:\n            self.last_intent = "learning_evolution"\n            return learning_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
route_block='''        learning_action = self.learning_evolution.handle(user_input)\n        if learning_action:\n            self.last_intent = "learning_evolution"\n            return learning_action\n\n        integration_action = self.knowledge_integration.handle(user_input)\n        if integration_action:\n            self.last_intent = "knowledge_integration"\n            return integration_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
if "integration_action = self.knowledge_integration.handle" not in core:
    if route_marker not in core: raise SystemExit("B22 route marker missing")
    core=core.replace(route_marker,route_block,1)
core_path.write_text(core,encoding="utf-8")

manifest_path=Path("STAR_MIND_MANIFEST.json"); data=json.loads(manifest_path.read_text(encoding="utf-8")); data["schema"]=max(int(data.get("schema",0)),23)
principles=data.setdefault("principles",[])
for item in (
    "knowledge integration means updating model relations and active representations, not merely storing or copying data",
    "B22 reuses the five B15 model frames and shared knowledge graph; no parallel world/human/social/self/situation models",
    "noncanonical knowledge never becomes a model fact silently and SELF integration cannot redefine identity or permissions",
    "Situation Model integration remains temporary/revisable and preserves the original knowledge item and provenance",
):
    if item not in principles:principles.append(item)
data["block_22_knowledge_integration"]={
    "status":"experimental-integrated","source_of_truth":"core/knowledge_integration.py","integration":"core/star_core.py","namespace":"B22","logical_capacity":1000000000,
    "effects":["relations","expectations","predictions","interpretations","context","judgments","World Model","Human Model","Social Model","Self Model","Situation Model"],
    "reuse":{"knowledge":"B03","models":"B15 same frames","metacognition":"B20","learning":"B21","reasoning":"B18","graph":"shared","new_models":False,"new_database":False},
    "policy":{"storage_alone_is_integration":False,"copies_source_datasets":False,"noncanonical_becomes_fact":False,"self_redefines_identity":False,"self_grants_permissions":False,"situation_temporary":True},
    "catalog":{"domains":10,"branches":50,"lenses_per_branch":10,"canonical_nodes":500,"variants_per_node":2000000,"addressable_contents":1000000000,"materialization":"on-demand"},
}
def add_ns(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k=="current_namespaces" and isinstance(v,list) and "B22" not in v:v.append("B22")
            add_ns(v)
    elif isinstance(obj,list):
        for v in obj:add_ns(v)
add_ns(data); manifest_path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

roadmap_path=Path("docs/MASTER_ROADMAP.md"); roadmap=roadmap_path.read_text(encoding="utf-8")
section=r'''### BLOCO 22 — Knowledge Integration Engine

B22 fecha a diferença entre **armazenar** e **integrar** conhecimento. Ele reutiliza
o B03/Knowledge Graph e os mesmos cinco frames B15 para atualizar por referência:
relações, expectativas, previsões, interpretações, contexto e julgamentos.

Conhecimento não canônico permanece observação/inferência/hipótese. `facts` só
recebe material explicitamente canônico com proveniência; o SELF MODEL não aceita
este bloco como autoridade para redefinir identidade, valores ou permissões.
SITUATION MODEL recebe atualizações temporárias e revisáveis.

```text
INTEGRAR ≠ COPIAR
ARMAZENAR ≠ INTEGRAR
CONHECIMENTO NOVO PODE REVISAR MODELOS ≠ REDEFINIR A STAR
```

Escala: 50 ramos × 10 lentes = 500 nós; 2M de contextos por nó =
**1.000.000.000** representações `KINT-B22-*` sob demanda.

'''
if "### BLOCO 22 — Knowledge Integration Engine" not in roadmap:
    pos=roadmap.find("## V2.1")
    if pos<0:raise SystemExit("B22 roadmap marker missing")
    roadmap=roadmap[:pos]+section+roadmap[pos:]
roadmap_path.write_text(roadmap,encoding="utf-8")
