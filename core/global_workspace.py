"""BLOCO 23 — Global Cognitive Workspace.

O workspace não é outro banco ou memória. Ele mantém apenas um conjunto cognitivo
ativo e bounded, reunindo candidatos de percepção, saliência/atenção, memória,
conhecimento, linguagem, planejamento, executive, self e Situation Model.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import prod
import re
import unicodedata
from typing import Any, Iterable

from core.universal_knowledge import UniversalKnowledgeArchitecture


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    text=unicodedata.normalize("NFKD",_clean(value)); text="".join(c for c in text if not unicodedata.combining(c)).casefold()
    return re.sub(r"[^a-z0-9]+","_",text).strip("_")


def _clamp(value:float)->float:return max(0.0,min(float(value),1.0))


@dataclass(frozen=True)
class WorkspaceBranch:
    domain:str;key:str;label:str;subtopics:tuple[str,...]


def _subs(raw:str)->tuple[str,...]:return tuple(x.strip() for x in raw.split(";") if x.strip())

_DOMAINS={
 "perception":(("perceptual_input","Perception input","perception;sinal;modalidade;fonte;tempo"),("perceptual_confidence","Confiança perceptiva","confiança;incerteza;fonte;fusão"),("perceptual_events","Eventos perceptivos","evento;mudança;objeto;pessoa;ambiente"),("perceptual_unknown","Percepção indisponível","unknown;unavailable;sensor ausente;sem invenção"),("perceptual_priority","Prioridade perceptiva","novidade;risco;urgência;saliência")),
 "salience_attention":(("salience","Salience","saliência;relevância;novidade;risco"),("attention","Attention","atenção;foco;seleção;top-k"),("active_goals","Objetivos ativos","goal;prioridade;alinhamento;contexto"),("active_entities","Entidades ativas","entidade;recência;relação;contexto"),("attention_limits","Limites de atenção","bounded;janela;capacidade;truncamento")),
 "memory":(("working_memory","Working Memory","working memory;recente;temporário;ativo"),("episodic_recall","Recall episódico","episódio;evento;recall;relevância"),("semantic_recall","Recall semântico","semantic;conceito;memória;contexto"),("project_recall","Recall de projeto","projeto;objetivo;estado;histórico"),("memory_limits","Limites de memória ativa","recall bounded;não carregar tudo;fonte")),
 "knowledge":(("knowledge_retrieval","Knowledge retrieval","conhecimento;query;índice;cache;B03"),("canonical_reference","Referência canônica","canonical;claim;fonte;proveniência"),("knowledge_relation","Relações de conhecimento","grafo;relação;cross-link;contexto"),("knowledge_integration","Conhecimento integrado","B22;modelo;expectativa;interpretação"),("knowledge_limits","Limites de recuperação","top-k;bounded;consulta;cache")),
 "language":(("language_input","Language input","linguagem;texto;fala;meaning;contexto"),("language_intent","Intenção linguística","intenção aparente;alternativas;pragmática"),("language_context","Contexto linguístico","discurso;turno;referência;idioma"),("language_output","Saída linguística","resposta;formulação;registro;clareza"),("language_limits","Limites linguísticos","ambiguidade;tradução;incerteza;contexto")),
 "planning":(("planning_goal","Objetivo de planejamento","objetivo;estado desejado;prioridade"),("planning_options","Opções","opção;simulação;comparação;risco"),("planning_decision","Decisão cognitiva","decisão;justificativa;verificação;sem execução"),("planning_risk","Risco do plano","risco;reversibilidade;consequência"),("planning_limits","Limites do planejamento","plano ≠ ação;permissão;segurança")),
 "executive":(("executive_reference","Executive","executive;coordenação;roteamento;referência"),("executive_priority","Prioridade executiva","prioridade;objetivo;restrição;ordem"),("executive_gate","Gate executivo","capacidade;permissão;segurança;boundary"),("executive_status","Estado executivo","disponível;indisponível;erro;contexto"),("executive_limits","Limites executivos","workspace não executa;separação;controle")),
 "self":(("self_state","Self state","Self;estado;recursos;incerteza"),("self_capability","Self capability","capacidade;limitação;availability;fonte"),("self_permission","Self permission","permission;default deny;boundary;segurança"),("self_goal","Self objectives","objetivo;valor;prioridade;contexto"),("self_limits","Self protegido","identidade;valores;permissões;não redefinir")),
 "situation":(("situation_context","Situation context","Situation Model;agora;contexto;entidades"),("situation_evidence","Situation evidence","evidência;working memory;fonte;incerteza"),("situation_hypotheses","Situation hypotheses","hipótese;interpretação;alternativas"),("situation_risk","Situation risk","risco;urgência;atenção;consequência"),("situation_revision","Situation revision","temporário;revisável;novo sinal;atualização")),
 "workspace_control":(("activation","Ativação","ativação;candidato;score;top-k"),("broadcast","Broadcast","broadcast;compartilhamento;componentes;referência"),("active_index","Índice ativo","índice;token;lookup;janela"),("eviction","Eviction","remoção;capacidade;recência;prioridade"),("workspace_audit","Auditoria do workspace","fonte;score;seleção;truncamento;sem execução")),
}
DOMAIN_LABELS={k:k.replace("_"," ").title() for k in _DOMAINS}
WORKSPACE_BRANCHES=tuple(WorkspaceBranch(d,k,l,_subs(s)) for d,bs in _DOMAINS.items() for k,l,s in bs)
WORKSPACE_LENSES=(("source","fonte","preservar origem"),("relevance","relevância","medir alinhamento ao momento"),("salience","saliência","priorizar novidade/risco sem autorizar"),("recency","recência","considerar tempo"),("confidence","confiança","preservar incerteza"),("goal","objetivo","alinhar ao objetivo ativo"),("context","contexto","situar o item"),("relation","relação","ligar referências ativas"),("capacity","capacidade","respeitar janela bounded"),("audit","auditoria","registrar por que entrou no workspace"))
COMPONENT_AXIS=("perception","salience","attention","memory","knowledge","language","planning","executive","self","situation")
CONTEXT_AXIS=("conversation","project","technical","scientific","social","physical","digital","emergency","personal","mixed")
PRIORITY_AXIS=("none","very_low","low","moderate_low","moderate","moderate_high","high","very_high","critical","mixed")
CONFIDENCE_AXIS=("unknown","very_low","low","moderate_low","moderate","moderate_high","high","very_high","calibrated","conflicting")
TIME_AXIS=("instant","recent","session","day","week","long_term","historical","future","unknown","mixed")
ACTIVATION_AXIS=("candidate","selected","active","suppressed","evicted","recalled","retrieved","broadcast","revised","unknown")
MODE_AXIS=("primary","alternative")
VARIANT_AXES=(("component",COMPONENT_AXIS),("context",CONTEXT_AXIS),("priority",PRIORITY_AXIS),("confidence",CONFIDENCE_AXIS),("time_scope",TIME_AXIS),("activation_state",ACTIVATION_AXIS),("mode",MODE_AXIS))
CANONICAL_NODES=len(WORKSPACE_BRANCHES)*len(WORKSPACE_LENSES);VARIANTS_PER_NODE=prod(len(v) for _,v in VARIANT_AXES);ADDRESSABLE_CONTENTS=CANONICAL_NODES*VARIANTS_PER_NODE
if len(_DOMAINS)!=10 or len(WORKSPACE_BRANCHES)!=50 or len(WORKSPACE_LENSES)!=10:raise RuntimeError("B23 requer 10 domínios, 50 ramos e 10 lentes")
if CANONICAL_NODES!=500 or VARIANTS_PER_NODE!=2_000_000 or ADDRESSABLE_CONTENTS!=1_000_000_000:raise RuntimeError("escala B23 inválida")
WORKSPACE_POLICY={"loads_full_logical_space":False,"active_window_bounded":True,"workspace_is_persistent_memory":False,"workspace_executes_actions":False,"salience_is_truth":False,"priority_is_permission":False,"perception_unavailable_is_invented":False,"operational_authorization":False,"rule":"WORKSPACE ATIVO ≠ CONHECIMENTO TOTAL; SELECIONAR ≠ EXECUTAR"}

def _decode(i:int)->dict[str,str]:
    if not 0<=int(i)<VARIANTS_PER_NODE:raise IndexError(i)
    n=int(i);o={}
    for k,v in reversed(VARIANT_AXES):n,r=divmod(n,len(v));o[k]=v[r]
    return {k:o[k] for k,_ in VARIANT_AXES}

class WorkspaceCatalog:
    def stats(self):return {"namespace":"B23","domains":10,"branches":50,"lenses_per_branch":10,"canonical_nodes":500,"variants_per_node":2_000_000,"addressable_contents":1_000_000_000,"materialization":"on-demand","active_materialization":"bounded runtime window","preloaded_active_items":0}
    @staticmethod
    def content_id(n:int,v:int)->str:
        if not 0<=n<500 or not 0<=v<2_000_000:raise IndexError((n,v))
        return f"GWS-B23-{n*2_000_000+v+1:010d}"
    def get_variant(self,x:str):
        m=re.fullmatch(r"GWS-B23-(\d{10})",_clean(x).upper())
        if not m:return None
        a=int(m.group(1))
        if not 1<=a<=1_000_000_000:return None
        ni,vi=divmod(a-1,2_000_000);bi,li=divmod(ni,10);b=WORKSPACE_BRANCHES[bi];lk,ll,ins=WORKSPACE_LENSES[li]
        return {"id":f"GWS-B23-{a:010d}","namespace":"B23","domain":b.domain,"domain_label":DOMAIN_LABELS[b.domain],"branch":b.key,"branch_label":b.label,"lens":lk,"lens_label":ll,**_decode(vi),"prompt":f"{b.label} / {ll}: {ins}. Manter somente conteúdo cognitivamente ativo e bounded."}

class GlobalCognitiveWorkspace:
    NAMESPACE="B23";TAXONOMY_ROOT_ID="GLOBAL-WORKSPACE-TAX-ROOT"
    def __init__(self,knowledge:UniversalKnowledgeArchitecture,*,attention_salience,memory_continuity,language=None,planning=None,executive=None,self_model=None,internal_models=None,knowledge_integration=None,perception_provider=None,max_active:int=32):
        self.knowledge=knowledge;self.graph=knowledge.graph;self.attention_salience=attention_salience;self.memory_continuity=memory_continuity;self.language=language;self.planning=planning;self.executive=executive;self.self_model=self_model;self.internal_models=internal_models;self.knowledge_integration=knowledge_integration;self.perception_provider=perception_provider;self.max_active=max(4,min(int(max_active),64));self._active=[];self._index={};self.catalog=WorkspaceCatalog()
        self.knowledge.register_namespace("B23","BLOCO 23 — GLOBAL COGNITIVE WORKSPACE",logical_capacity=ADDRESSABLE_CONTENTS,source="core/global_workspace.py",metadata={"materialization":"on-demand","active_window":self.max_active,"bounded":True,"persistent_store":False,"shared_memory":"B13","shared_attention":"B14"})
    def attach_perception(self,provider):self.perception_provider=provider
    @staticmethod
    def _candidate(content,source,**kw):
        return {"content":_clean(content),"source":_clean(source),"importance":_clamp(kw.get("importance",.5)),"risk":_clamp(kw.get("risk",0)),"urgency":_clamp(kw.get("urgency",0)),"confidence":_clamp(kw.get("confidence",.5)),"entities":tuple(kw.get("entities") or ()),"metadata":deepcopy(kw.get("metadata") or {})}
    def _perception_status(self):
        provider=self.perception_provider
        if provider is None:return "unavailable"
        checker=getattr(provider,"workspace_available",None)
        if callable(checker):
            try:return "available" if bool(checker()) else "idle"
            except (RuntimeError,TypeError,AttributeError):return "unknown"
        return "available"
    def component_status(self):
        return {"perception":self._perception_status(),"salience":"available","attention":"available","memory":"available","knowledge":"available","language":"available" if self.language else "unavailable","planning":"available" if self.planning else "unavailable","executive":"available" if self.executive else "unavailable","self":"available" if self.self_model else "unavailable","situation":"available" if self.internal_models else "unavailable"}
    def retrieve(self,query:str,*,memory_limit:int=8,knowledge_limit:int=8)->list[dict]:
        query=_clean(query);out=[]
        if query:
            for m in self.memory_continuity.recall(query,limit=max(1,min(memory_limit,16))):out.append(self._candidate(m.get("content"),"memory",importance=m.get("importance",.5),confidence=(m.get("metadata") or {}).get("confidence",.5),metadata={"memory_id":m.get("id"),"kind":m.get("kind")}))
            for k in self.knowledge.query(query,limit=max(1,min(knowledge_limit,16))):out.append(self._candidate(k.get("canonical_label") or k.get("summary"),"knowledge",importance=.65,confidence=.8,metadata={"knowledge_id":k.get("knowledge_id"),"namespace":k.get("namespace")}))
        return out[:32]
    def activate(self,*,query:str="",perception:Iterable[dict]|None=None,candidates:Iterable[dict]|None=None,goal:str="",language_input:str="",plan_artifact:dict|None=None,limit:int|None=None)->dict:
        limit=max(1,min(int(limit or self.max_active),self.max_active));pool=[]
        for raw in list(perception or ())[:16]:
            if isinstance(raw,dict):pool.append(self._candidate(raw.get("content") or raw.get("label") or raw.get("event"),"perception",importance=raw.get("importance",.6),risk=raw.get("risk",0),urgency=raw.get("urgency",0),confidence=raw.get("confidence",.5),entities=raw.get("entities"),metadata=raw))
        pool.extend(self.retrieve(query,memory_limit=8,knowledge_limit=8))
        if language_input:pool.append(self._candidate(language_input,"language",importance=.65,metadata={"input":True}))
        if goal:pool.append(self._candidate(goal,"planning",importance=.8,metadata={"role":"active_goal"}))
        if plan_artifact:pool.append(self._candidate(plan_artifact.get("goal") or "active plan","planning",importance=.75,metadata={"plan":deepcopy(plan_artifact),"execution_performed":False}))
        if self.self_model is not None:
            snap=self.self_model.snapshot();pool.append(self._candidate("STAR self state","self",importance=.55,confidence=.9,metadata={"state":deepcopy(snap.get("state")),"permissions":deepcopy(snap.get("permissions"))}))
        if self.internal_models is not None:
            sit=self.internal_models.model_view("situation_model");pool.append(self._candidate("Situation Model","situation",importance=.7,metadata={"view":sit}))
        for raw in candidates or ():
            if len(pool)>=self.attention_salience.max_candidates:break
            if isinstance(raw,dict):pool.append(self._candidate(raw.get("content") or raw.get("label"),raw.get("source") or "candidate",importance=raw.get("importance",.5),risk=raw.get("risk",0),urgency=raw.get("urgency",0),confidence=raw.get("confidence",.5),entities=raw.get("entities"),metadata=raw.get("metadata")))
        selected=self.attention_salience.select_relevant(iter(pool),limit=limit)
        active=[]
        for scored in selected.get("selected") or []:
            candidate=deepcopy(scored.get("candidate") or {})
            if not candidate:
                continue
            candidate["attention_score"]=scored.get("score")
            candidate["attention_components"]=deepcopy(scored.get("components") or {})
            candidate["selection_is_inference"]=True
            active.append(candidate)
        self._active=active[:limit];self._reindex()
        return {"active":deepcopy(self._active),"active_count":len(self._active),"max_active":self.max_active,"bounded":True,"candidate_pool_count":len(pool),"truncated":selected.get("input_truncated",False),"component_status":self.component_status(),"workspace_is_persistent_memory":False,"execution_performed":False,"operational_authorization":False}
    def _reindex(self):
        idx={}
        for i,item in enumerate(self._active):
            text=f"{item.get('content','')} {item.get('source','')} {' '.join(item.get('entities') or ())}".casefold()
            for token in set(re.findall(r"[\wÀ-ÿ]+",text)):
                if len(token)>1:idx.setdefault(token,[]).append(i)
        self._index=idx
    def lookup_active(self,query:str,limit:int=8):
        tokens=[x.casefold() for x in re.findall(r"[\wÀ-ÿ]+",_clean(query)) if len(x)>1];ids=[]
        for t in tokens:
            for i in self._index.get(t,[]):
                if i not in ids:ids.append(i)
        return deepcopy([self._active[i] for i in ids[:max(1,min(limit,self.max_active))]])
    def broadcast(self):return {"active":deepcopy(self._active),"index_terms":len(self._index),"recipients":tuple(k for k,v in self.component_status().items() if v=="available"),"bounded":True,"execution_performed":False}
    def snapshot(self):return {"active":deepcopy(self._active),"active_count":len(self._active),"max_active":self.max_active,"index_terms":len(self._index),"components":self.component_status(),"policy":deepcopy(WORKSPACE_POLICY)}
    def materialize_taxonomy(self,domain:str|None=None):
        key=_norm(domain) if domain else None
        if key and key not in _DOMAINS:raise KeyError(domain)
        bs=[b for b in WORKSPACE_BRANCHES if key is None or b.domain==key];root=self.graph.add_entity("global_workspace_taxonomy","GLOBAL COGNITIVE WORKSPACE",node_id=self.TAXONOMY_ROOT_ID,data={"block":"B23","bounded":True})
        for sid,label in (("ATTENTION-TAX-ROOT","B14 Attention"),("MEMORY-TAX-ROOT","B13 Memory"),("MODELS-B15-ROOT","B15 Models"),("KNOWLEDGE-INTEGRATION-TAX-ROOT","B22 Integration")):
            self.graph.add_entity("workspace_source",label,node_id=sid,data={"block":"B23"});self.graph.relate(root,sid,"integrates",metadata={"block":"B23"})
        for b in bs:
            d=f"GWS-DOM-{b.domain.upper()}";r=f"GWS-BR-{b.key.upper()}";self.graph.add_entity("workspace_domain",DOMAIN_LABELS[b.domain],node_id=d,data={"block":"B23"});self.graph.add_entity("workspace_branch",b.label,node_id=r,data={"block":"B23"});self.graph.relate(root,d,"has_part",metadata={"block":"B23"});self.graph.relate(d,r,"has_part",metadata={"block":"B23"})
        return {"domain":key,"branches_materialized":len(bs),"shared_graph":True,"persistent_workspace_created":False}
    def stats(self):return {"status":"experimental-integrated","namespace":self.knowledge.store.get_namespace("B23"),"catalog":self.catalog.stats(),"active_window":self.max_active,"policy":deepcopy(WORKSPACE_POLICY)}
    def handle(self,text:str):
        raw=_clean(text);low=raw.casefold()
        if not raw:return None
        if low in {"status bloco 23","status global workspace","global cognitive workspace","workspace cognitivo global"}:
            return f"⭐ BLOCO 23 — GLOBAL WORKSPACE: {ADDRESSABLE_CONTENTS} representações lógicas | janela ativa máx. {self.max_active} | carrega 1B simultaneamente=NÃO."
        item=self.catalog.get_variant(raw.upper())
        if item:return f"⭐ {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        return None
