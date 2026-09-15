from __future__ import annotations
import json
from pathlib import Path
p=Path('core/star_core.py');s=p.read_text(encoding='utf-8')
m='from core.foundations import FoundationSuite\n'
if 'from core.global_workspace import GlobalCognitiveWorkspace\n' not in s:s=s.replace(m,m+'from core.global_workspace import GlobalCognitiveWorkspace\n',1)
im='''        self.mind.knowledge_integration = self.knowledge_integration\n\n        self.last_intent = None\n'''
ib='''        self.mind.knowledge_integration = self.knowledge_integration\n\n        # BLOCO 23: Global Cognitive Workspace bounded. Não é memória persistente;\n        # reúne apenas candidatos ativos de atenção/memória/conhecimento/linguagem/\n        # planejamento/executive/self/situation. Perception será acoplada no B25.\n        self.global_workspace = GlobalCognitiveWorkspace(\n            self.knowledge,\n            attention_salience=self.attention_salience,\n            memory_continuity=self.memory_continuity,\n            language=self.language_communication,\n            planning=self.planning_decision,\n            executive=self.executive,\n            self_model=self.self_model,\n            internal_models=self.internal_models,\n            knowledge_integration=self.knowledge_integration,\n            perception_provider=None,\n        )\n        self.mind.global_workspace = self.global_workspace\n\n        self.last_intent = None\n'''
if 'self.global_workspace = GlobalCognitiveWorkspace(' not in s:
    if im not in s:raise SystemExit('init marker')
    s=s.replace(im,ib,1)
rm='''        integration_action = self.knowledge_integration.handle(user_input)\n        if integration_action:\n            self.last_intent = "knowledge_integration"\n            return integration_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
rb='''        integration_action = self.knowledge_integration.handle(user_input)\n        if integration_action:\n            self.last_intent = "knowledge_integration"\n            return integration_action\n\n        workspace_action = self.global_workspace.handle(user_input)\n        if workspace_action:\n            self.last_intent = "global_workspace"\n            return workspace_action\n\n        knowledge_action = self.knowledge.handle(user_input)\n'''
if 'workspace_action = self.global_workspace.handle' not in s:
    if rm not in s:raise SystemExit('route marker')
    s=s.replace(rm,rb,1)
p.write_text(s,encoding='utf-8')
mp=Path('STAR_MIND_MANIFEST.json');d=json.loads(mp.read_text(encoding='utf-8'));d['schema']=max(int(d.get('schema',0)),24)
for x in ('Global Cognitive Workspace keeps a bounded active set rather than loading the logical knowledge space','B23 integrates Perception/Salience/Attention/Memory/Knowledge/Language/Planning/Executive/Self/Situation by reference','workspace activation and broadcast never execute actions or grant permissions','perception remains explicitly unavailable until a real provider is attached'):
    if x not in d.setdefault('principles',[]):d['principles'].append(x)
d['block_23_global_cognitive_workspace']={'status':'experimental-integrated','source_of_truth':'core/global_workspace.py','integration':'core/star_core.py','namespace':'B23','logical_capacity':1000000000,'components':['Perception','Salience','Attention','Memory','Knowledge','Language','Planning','Executive','Self','Situation Model'],'active_window':{'bounded':True,'default_max':32,'hard_max':64,'persistent':False},'retrieval':{'memory':'B13 bounded recall','knowledge':'B03 indexed query/cache','selection':'B14 top-k salience','active_index':'workspace-only'},'perception_status_before_B25':'provider optional/unavailable; no fabricated sensing','catalog':{'domains':10,'branches':50,'lenses_per_branch':10,'canonical_nodes':500,'variants_per_node':2000000,'addressable_contents':1000000000,'materialization':'on-demand'}}
def add(o):
    if isinstance(o,dict):
        for k,v in o.items():
            if k=='current_namespaces' and isinstance(v,list) and 'B23' not in v:v.append('B23')
            add(v)
    elif isinstance(o,list):
        for v in o:add(v)
add(d);mp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
rp=Path('docs/MASTER_ROADMAP.md');r=rp.read_text(encoding='utf-8');sec='''### BLOCO 23 — Global Cognitive Workspace\n\nB23 cria uma janela cognitiva **bounded**, não outro banco. Perception, Salience,\nAttention, Memory, Knowledge, Language, Planning, Executive, Self e Situation Model\ncompetem por um conjunto ativo pequeno selecionado pelo B14. B03/B13 são consultados\ncom top-k limitado e o índice do workspace cobre somente os itens ativos.\n\nAntes do B25, Perception fica explicitamente `unavailable` salvo quando observações\nsão fornecidas por um provider real/externo; nenhum sensor é inventado.\n\n```text\nWORKSPACE ATIVO ≠ CONHECIMENTO TOTAL\nSELECIONAR ≠ EXECUTAR\nSALIÊNCIA/PRIORIDADE ≠ PERMISSÃO\n```\n\nEscala lógica: 500 nós × 2M = **1B** `GWS-B23-*` sob demanda, enquanto a janela\nde runtime mantém no máximo 64 itens (32 por padrão).\n\n'''
if '### BLOCO 23 — Global Cognitive Workspace' not in r:
    i=r.find('## V2.1');
    if i<0:raise SystemExit('roadmap marker')
    r=r[:i]+sec+r[i:]
rp.write_text(r,encoding='utf-8')