from __future__ import annotations
import json
from pathlib import Path

core_path=Path("core/star_core.py"); core=core_path.read_text(encoding="utf-8")
marker="from core.language_manager import LanguageManager\n"
if "from core.learning_evolution import LearningEvolution\n" not in core:
    if marker not in core: raise SystemExit("B21 import marker missing")
    core=core.replace(marker,marker+"from core.learning_evolution import LearningEvolution\n",1)
init_marker='''        self.mind.metacognition_layer = self.metacognition\n\n        self.last_intent = None\n'''
init_block='''        self.mind.metacognition_layer = self.metacognition\n\n        # BLOCO 21: aprendizagem/evolução sobre memória, personalidade,\n        # prediction error e metacognição existentes. Nunca autoedita o core.\n        self.learning_evolution = LearningEvolution(\n            self.knowledge,\n            memory_continuity=self.memory_continuity,\n            reasoning_simulation=self.reasoning_simulation,\n            metacognition=self.metacognition,\n            affective_personality=self.affective_personality,\n            self_improvement=self.mind.self_improvement,\n            attention_salience=self.attention_salience,\n        )\n        self.mind.learning_evolution = self.learning_evolution\n\n        self.last_intent = None\n'''
if "self.learning_evolution = LearningEvolution(" not in core:
    if init_marker not in core: raise SystemExit("B21 init marker missing")
    core=core.replace(init_marker,init_block,1)
route_marker='''        metacognition_action = self.metacognition.handle(user_input)\n        if metacognition_action:\n            self.last_intent = "metacognition"\n            return metacognition_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
route_block='''        metacognition_action = self.metacognition.handle(user_input)\n        if metacognition_action:\n            self.last_intent = "metacognition"\n            return metacognition_action\n\n        learning_action = self.learning_evolution.handle(user_input)\n        if learning_action:\n            self.last_intent = "learning_evolution"\n            return learning_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
if "learning_action = self.learning_evolution.handle" not in core:
    if route_marker not in core: raise SystemExit("B21 route marker missing")
    core=core.replace(route_marker,route_block,1)
core_path.write_text(core,encoding="utf-8")

manifest_path=Path("STAR_MIND_MANIFEST.json"); data=json.loads(manifest_path.read_text(encoding="utf-8")); data["schema"]=max(int(data.get("schema",0)),22)
principles=data.setdefault("principles",[])
for item in (
    "continuous learning preserves source, reference, confidence, consistency and previous versions",
    "experience and generalization remain revisable and do not become canonical facts automatically",
    "B21 may adapt memory, strategy and bounded personality state but has no unrestricted authority to modify central code",
    "prediction error drives review without rewriting predicted or observed history",
):
    if item not in principles: principles.append(item)
data["block_21_learning_evolution"]={
    "status":"experimental-integrated","source_of_truth":"core/learning_evolution.py","integration":"core/star_core.py","namespace":"B21","logical_capacity":1000000000,
    "capabilities":["experience_learning","generalization","prediction_error","revision","consolidation","adaptation","evolution","cognitive_development"],
    "reuse":{"memory":"B13","personality":"B17","reasoning_prediction_error":"B18","metacognition":"B20","self_improvement":"existing evaluator","new_database":False},
    "policy":{"automatic_code_modification":False,"unrestricted_self_modification":False,"revision_erases_source":False,"canonical_promotion_without_b2_b3":False},
    "catalog":{"domains":10,"branches":50,"lenses_per_branch":10,"canonical_nodes":500,"variants_per_node":2000000,"addressable_contents":1000000000,"materialization":"on-demand"},
}
def add_ns(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k=="current_namespaces" and isinstance(v,list) and "B21" not in v:v.append("B21")
            add_ns(v)
    elif isinstance(obj,list):
        for v in obj:add_ns(v)
add_ns(data); manifest_path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

roadmap_path=Path("docs/MASTER_ROADMAP.md"); roadmap=roadmap_path.read_text(encoding="utf-8")
section=r'''### BLOCO 21 — Aprendizagem e Evolução Cognitiva

B21 integra aprendizado por experiência, generalização, prediction error, revisão,
consolidação, adaptação, evolução e desenvolvimento cognitivo sobre B13/B17/B18/B20.
O `SelfImprovementEvaluator` existente mede e recomenda; não aplica patches.

Toda aprendizagem preserva origem, referência, confiança, consistência e histórico.
Revisões criam novas versões/relações e não apagam silenciosamente registros antigos.
Generalizações permanecem inferências até passarem pelos gates epistêmicos B02/B03.

```text
APRENDER ≠ REESCREVER A HISTÓRIA
EVOLUIR ≠ AUTOEDITAR IRRESTRITAMENTE O CÓDIGO CENTRAL
```

Escala: 50 ramos × 10 lentes = 500 nós; 2M de combinações por nó =
**1.000.000.000** representações `LEARN-B21-*` sob demanda.

'''
if "### BLOCO 21 — Aprendizagem e Evolução Cognitiva" not in roadmap:
    pos=roadmap.find("## V2.1")
    if pos<0: raise SystemExit("B21 roadmap marker missing")
    roadmap=roadmap[:pos]+section+roadmap[pos:]
roadmap_path.write_text(roadmap,encoding="utf-8")
