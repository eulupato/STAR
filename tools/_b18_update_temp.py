from __future__ import annotations
import json
from pathlib import Path

core_path=Path('core/star_core.py'); core=core_path.read_text(encoding='utf-8')
marker='from core.affective_personality import AffectivePersonality\n'
if 'from core.reasoning_simulation import ReasoningSimulation\n' not in core:
    if marker not in core: raise SystemExit('B18 import marker missing')
    core=core.replace(marker, marker+'from core.reasoning_simulation import ReasoningSimulation\n',1)

init_marker='''        self.mind.affective_personality = self.affective_personality\n\n        self.last_intent = None\n'''
init_block='''        self.mind.affective_personality = self.affective_personality\n\n        # BLOCO 18: coordenação causal/raciocínio/simulação sobre os componentes\n        # já existentes do MIND. Conclusões derivadas permanecem inferências e\n        # fatos/evidências originais nunca são reescritos por simulação.\n        self.reasoning_simulation = ReasoningSimulation(\n            self.knowledge,\n            reasoning=self.mind.reasoning,\n            simulation=self.mind.simulation,\n            verifier=self.mind.verifier,\n            memory_continuity=self.memory_continuity,\n            attention_salience=self.attention_salience,\n            internal_models=self.internal_models,\n            social_cognition=self.social_cognition,\n            affective_personality=self.affective_personality,\n        )\n        self.mind.reasoning_simulation = self.reasoning_simulation\n\n        self.last_intent = None\n'''
if 'self.reasoning_simulation = ReasoningSimulation(' not in core:
    if init_marker not in core: raise SystemExit('B18 init marker missing')
    core=core.replace(init_marker,init_block,1)

route_marker='''        personality_action = self.affective_personality.handle(user_input)\n        if personality_action:\n            self.last_intent = "affective_personality"\n            return personality_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
route_block='''        personality_action = self.affective_personality.handle(user_input)\n        if personality_action:\n            self.last_intent = "affective_personality"\n            return personality_action\n\n        reasoning_simulation_action = self.reasoning_simulation.handle(user_input)\n        if reasoning_simulation_action:\n            self.last_intent = "reasoning_simulation"\n            return reasoning_simulation_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
if 'reasoning_simulation_action = self.reasoning_simulation.handle' not in core:
    if route_marker not in core: raise SystemExit('B18 route marker missing')
    core=core.replace(route_marker,route_block,1)
core_path.write_text(core,encoding='utf-8')

manifest_path=Path('STAR_MIND_MANIFEST.json'); data=json.loads(manifest_path.read_text(encoding='utf-8'))
data['schema']=max(int(data.get('schema',0)),19)
principles=data.setdefault('principles',[])
for item in (
    'derived conclusions remain inference/hypothesis until independently verified and never rewrite source facts',
    'simulation and counterfactual worlds remain separate from observations and historical memory',
    'prediction preserves uncertainty and prediction error preserves both predicted and observed values',
    'reasoning over large knowledge spaces uses bounded attention/context selection rather than loading all addressable contents',
):
    if item not in principles: principles.append(item)
data['block_18_reasoning_simulation']={
    'status':'experimental-integrated','source_of_truth':'core/reasoning_simulation.py','integration':'core/star_core.py','namespace':'B18','logical_capacity':1000000000,
    'requested_components':['causality','analogy','abstraction','generalization','exceptions','counterfactuals','simulation','prediction','prediction error','risk','consequences','reversibility'],
    'reuse':{'reasoning_engine':'existing CognitiveSuite.reasoning','simulation_lab':'existing CognitiveSuite.simulation','truth_verifier':'existing CognitiveSuite.verifier','memory':'B13 working memory','attention':'B14 bounded selection','models':'B15 internal models','social':'B16 social cognition','personality':'B17 affective personality','new_reasoning_engine_created':False,'new_simulation_lab_created':False,'new_table_created':False},
    'epistemic_policy':{'inference_is_fact':False,'simulation_is_observation':False,'prediction_is_certainty':False,'counterfactual_is_history':False,'derived_conclusion_mutates_original_facts':False,'canonical_promotion_without_b2_gate':False,'operational_authorization':False},
    'catalog':{'domains':10,'branches':50,'lenses_per_branch':10,'canonical_nodes':500,'variants_per_node':2000000,'addressable_contents':1000000000,'materialization':'on-demand','prepopulated_conclusions':0,'truthfulness_note':'1B are addressable reasoning contexts and representations, not 1B independently proven conclusions'},
    'variant_matrix':{'context':10,'evidence_mode':10,'scale':10,'uncertainty':10,'time_horizon':10,'source_block':10,'reasoning_mode':2,'combinations_per_node':2000000}
}
def append_ns(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k=='current_namespaces' and isinstance(v,list) and 'B18' not in v: v.append('B18')
            append_ns(v)
    elif isinstance(obj,list):
        for v in obj: append_ns(v)
append_ns(data)
manifest_path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

road=Path('docs/MASTER_ROADMAP.md'); text=road.read_text(encoding='utf-8')
section=r'''### BLOCO 18 — Raciocínio, Causalidade e Simulação

O BLOCO 18 coordena o `ReasoningEngine`, `SimulationLab` e `TruthVerifier` já
existentes no MIND; não cria motores paralelos. Ele cruza conhecimento de vários
blocos por seleção bounded do B14 e usa working memory B13 para conclusões derivadas.

Inclui causalidade, analogia, abstração, generalização, exceções, contrafactuais,
simulação, previsão, prediction error, risco, consequências e reversibilidade.

```text
INFERÊNCIA ≠ FATO
SIMULAÇÃO ≠ OBSERVAÇÃO
PREVISÃO ≠ CERTEZA
CONTRAFACTUAL ≠ HISTÓRIA REAL
CONCLUSÃO DERIVADA NÃO REESCREVE PREMISSAS
```

Contrafactuais e simulações recebem cópias dos estados/premissas e mantêm o mundo
hipotético separado do baseline. Conclusões novas entram por padrão na working
memory como `inference`; promoção canônica continua exigindo o gate B02/B03.

A consulta de grandes espaços usa B14: **1B disponível ≠ 1B carregado**.

Escala lógica B18:
- **50 ramos × 10 lentes = 500 nós canônicos**;
- contexto(10) × evidência(10) × escala(10) × incerteza(10) × tempo(10) × fonte(10) × modo(2) = **2M** por nó;
- **500 × 2M = 1.000.000.000** representações `RSN-B18-*` sob demanda.

O 1B representa contextos de raciocínio/simulação combináveis, não conclusões
independentes já comprovadas ou materializadas.

'''
if '### BLOCO 18 — Raciocínio, Causalidade e Simulação' not in text:
    pos=text.find('## V2.1')
    if pos<0: raise SystemExit('B18 roadmap marker missing')
    text=text[:pos]+section+text[pos:]
road.write_text(text,encoding='utf-8')
