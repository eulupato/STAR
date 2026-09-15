"""BLOCO 22 — Knowledge Integration Engine.

Integra conhecimento novo aos cinco modelos cognitivos existentes sem duplicar
seus datasets. Armazenar não basta: itens epistêmicos podem atualizar relações,
expectativas, previsões, interpretações, contexto e julgamentos por referência.

Fato canônico continua sujeito a B02/B03. SELF MODEL não pode ter identidade,
valores fundamentais ou permissões redefinidos por esta camada.
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
    text = unicodedata.normalize("NFKD", _clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


@dataclass(frozen=True)
class IntegrationBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


_DOMAINS = {
    "relations": (
        ("entity_relations", "Relações entre entidades", "relação;entidade;grafo;vínculo;proveniência"),
        ("causal_relations", "Relações causais", "causa;efeito;hipótese;confundidor;revisão"),
        ("temporal_relations", "Relações temporais", "antes;depois;mudança;versão;tempo"),
        ("spatial_relations", "Relações espaciais", "local;proximidade;parte;ambiente;contexto"),
        ("semantic_relations", "Relações semânticas", "is_a;part_of;related_to;equivalência;contradição"),
    ),
    "expectations": (
        ("expected_state", "Estado esperado", "expectativa;estado futuro;base;confiança;horizonte"),
        ("behavior_expectation", "Expectativa comportamental", "expectativa;alternativas;contexto;não determinismo"),
        ("system_expectation", "Expectativa de sistema", "sistema;estado;transição;condição;limite"),
        ("expectation_revision", "Revisão de expectativa", "prediction error;fonte nova;calibração;histórico"),
        ("expectation_uncertainty", "Incerteza da expectativa", "incerteza;intervalo;alternativa;desconhecido"),
    ),
    "predictions": (
        ("prediction_basis", "Base de previsão", "previsão;base;evidência;memória;fonte"),
        ("prediction_update", "Atualização de previsão", "previsão;novo conhecimento;revisão;confiança"),
        ("prediction_horizon", "Horizonte de previsão", "tempo;horizonte;curto;longo;validade"),
        ("prediction_alternatives", "Previsões alternativas", "cenário;alternativa;probabilidade;incerteza"),
        ("prediction_validation", "Validação de previsão", "observação;prediction error;feedback;calibração"),
    ),
    "interpretations": (
        ("meaning_update", "Atualização de significado", "interpretação;significado;contexto;linguagem;fonte"),
        ("social_interpretation", "Interpretação social", "perspectiva;intenção hipotética;contexto;alternativas"),
        ("physical_interpretation", "Interpretação física", "objeto;estado;causa;ambiente;incerteza"),
        ("technical_interpretation", "Interpretação técnica", "sistema;função;falha;estado;uso"),
        ("interpretation_revision", "Revisão de interpretação", "evidência nova;contradição;alternativa;histórico"),
    ),
    "context": (
        ("situation_context", "Contexto situacional", "situação;agora;entidades;objetivo;risco"),
        ("historical_context", "Contexto histórico", "tempo;época;mudança;origem;versão"),
        ("social_context", "Contexto social", "papel;norma;relação;cultura;perspectiva"),
        ("task_context", "Contexto de tarefa", "objetivo;restrição;plano;recurso;prioridade"),
        ("context_revision", "Revisão de contexto", "novo dado;estado;recência;substituição;preservação"),
    ),
    "judgments": (
        ("evidence_judgment", "Julgamento de evidência", "evidência;força;fonte;confiança;limite"),
        ("risk_judgment", "Julgamento de risco", "risco;probabilidade;impacto;reversibilidade;incerteza"),
        ("relevance_judgment", "Julgamento de relevância", "relevância;saliência;objetivo;contexto;atenção"),
        ("plausibility_judgment", "Julgamento de plausibilidade", "plausibilidade;hipótese;alternativa;fonte"),
        ("judgment_revision", "Revisão de julgamento", "feedback;erro;contradição;revisão;histórico"),
    ),
    "world_model": (
        ("world_entities", "WORLD — entidades", "World Model;entidade;objeto;evento;ambiente"),
        ("world_states", "WORLD — estados", "estado;observação;mudança;tempo;incerteza"),
        ("world_relations", "WORLD — relações", "relação;causa;espaço;tempo;sistema"),
        ("world_expectations", "WORLD — expectativas", "expectativa;previsão;simulação;risco"),
        ("world_revision", "WORLD — revisão", "revisão;evidência;contradição;versão;fonte"),
    ),
    "human_social_models": (
        ("human_context", "HUMAN — contexto", "Human Model;pessoa;necessidade;capacidade;contexto"),
        ("human_expectations", "HUMAN — expectativas", "expectativa;comportamento não determinístico;alternativas"),
        ("social_relations", "SOCIAL — relações", "Social Model;relações;papéis;normas;confiança"),
        ("social_expectations", "SOCIAL — expectativas", "cooperação;conflito;norma;perspectiva;incerteza"),
        ("human_social_revision", "HUMAN/SOCIAL — revisão", "fonte nova;diversidade;exceção;não estereótipo"),
    ),
    "self_model": (
        ("self_capability_context", "SELF — capacidades", "Self Model;capacidade;disponibilidade;fonte;estado"),
        ("self_limit_context", "SELF — limitações", "limitação;indisponível;unknown;fonte;revisão"),
        ("self_state_context", "SELF — estado", "estado;runtime;recurso;incerteza;telemetria"),
        ("self_expectation", "SELF — expectativa", "previsão própria;resultado;confiança;feedback"),
        ("self_protected_identity", "SELF — identidade protegida", "identidade;valores;permissões;não redefinir"),
    ),
    "situation_model": (
        ("situation_entities", "SITUATION — entidades ativas", "Situation Model;entidades;atenção;contexto"),
        ("situation_evidence", "SITUATION — evidência", "evidência;memória;fonte;working memory"),
        ("situation_hypotheses", "SITUATION — hipóteses", "hipótese;interpretação;alternativa;confiança"),
        ("situation_judgment", "SITUATION — julgamento", "julgamento;risco;relevância;decisão;limites"),
        ("situation_update", "SITUATION — atualização", "novo conhecimento;contexto;revisão;temporário"),
    ),
}

DOMAIN_LABELS = {key: key.replace("_", " ").title() for key in _DOMAINS}
INTEGRATION_BRANCHES = tuple(
    IntegrationBranch(domain, key, label, _subs(subtopics))
    for domain, branches in _DOMAINS.items() for key, label, subtopics in branches
)
INTEGRATION_LENSES = (
    ("source", "origem", "preservar referência ao conhecimento de origem"),
    ("epistemic", "estado epistêmico", "separar fato, observação, memória, inferência e hipótese"),
    ("relation", "relação", "atualizar arestas sem copiar datasets"),
    ("expectation", "expectativa", "ajustar expectativa de forma revisável"),
    ("prediction", "previsão", "propagar base para previsões sem transformá-las em fatos"),
    ("interpretation", "interpretação", "atualizar leitura contextual com alternativas"),
    ("context", "contexto", "alterar contexto ativo, não identidade fundamental"),
    ("judgment", "julgamento", "recalibrar julgamento com confiança e limites"),
    ("model", "modelo", "integrar ao mesmo frame B15 por referência"),
    ("revision", "revisão", "preservar versões, conflitos e proveniência"),
)

MODEL_AXIS=("world_model","human_model","social_model","self_model","situation_model","cross_models","world_situation","human_social","self_situation","all_models")
EPISTEMIC_AXIS=("fact","observation","declared","memory","inference","hypothesis","prediction","unknown","disputed","superseded")
SOURCE_AXIS=("B02","B03","B13","B18","B20","B21","user","tool","external","mixed")
EFFECT_AXIS=("relation","expectation","prediction","interpretation","context","judgment","memory_reference","hypothesis","revision","cross_link")
CONFIDENCE_AXIS=("none","very_low","low","moderate_low","moderate","moderate_high","high","very_high","calibrated","conflicting")
TIME_AXIS=("current","recent","historical","future","persistent","temporary","event","session","versioned","unknown")
MODE_AXIS=("primary","alternative")
VARIANT_AXES=(("model_scope",MODEL_AXIS),("epistemic_state",EPISTEMIC_AXIS),("source_space",SOURCE_AXIS),("effect",EFFECT_AXIS),("confidence",CONFIDENCE_AXIS),("time_scope",TIME_AXIS),("mode",MODE_AXIS))
CANONICAL_NODES=len(INTEGRATION_BRANCHES)*len(INTEGRATION_LENSES)
VARIANTS_PER_NODE=prod(len(v) for _,v in VARIANT_AXES)
ADDRESSABLE_CONTENTS=CANONICAL_NODES*VARIANTS_PER_NODE
if len(_DOMAINS)!=10 or len(INTEGRATION_BRANCHES)!=50 or len(INTEGRATION_LENSES)!=10: raise RuntimeError("B22 requer 10 domínios, 50 ramos e 10 lentes")
if CANONICAL_NODES!=500 or VARIANTS_PER_NODE!=2_000_000 or ADDRESSABLE_CONTENTS!=1_000_000_000: raise RuntimeError("escala B22 inválida")

INTEGRATION_POLICY={
    "storage_alone_is_integration":False,
    "copies_source_datasets":False,
    "noncanonical_knowledge_becomes_fact":False,
    "human_knowledge_determines_individual_traits":False,
    "self_knowledge_redefines_identity":False,
    "self_knowledge_grants_permissions":False,
    "situation_updates_are_permanent_by_default":False,
    "original_knowledge_mutated":False,
    "shared_knowledge_graph":True,
    "operational_authorization":False,
    "rule":"INTEGRAR ≠ COPIAR; CONHECIMENTO NOVO PODE REVISAR MODELOS, MAS NÃO REDEFINIR IDENTIDADE OU PROMOVER INFERÊNCIA A FATO",
}


def _decode_axes(index:int)->dict[str,str]:
    if not 0<=int(index)<VARIANTS_PER_NODE: raise IndexError(index)
    value=int(index);out={}
    for name,vals in reversed(VARIANT_AXES):value,off=divmod(value,len(vals));out[name]=vals[off]
    return {name:out[name] for name,_ in VARIANT_AXES}


class IntegrationCatalog:
    def stats(self)->dict:
        return {"namespace":"B22","domains":10,"branches":50,"lenses_per_branch":10,"canonical_nodes":CANONICAL_NODES,"variants_per_node":VARIANTS_PER_NODE,"addressable_contents":ADDRESSABLE_CONTENTS,"materialization":"on-demand","preintegrated_items":0,"truthfulness_note":"1B are addressable integration contexts, not duplicated knowledge rows"}
    @staticmethod
    def content_id(node_index:int,variant_index:int)->str:
        if not 0<=int(node_index)<CANONICAL_NODES:raise IndexError(node_index)
        if not 0<=int(variant_index)<VARIANTS_PER_NODE:raise IndexError(variant_index)
        return f"KINT-B22-{int(node_index)*VARIANTS_PER_NODE+int(variant_index)+1:010d}"
    def get_variant(self,identifier:str)->dict|None:
        m=re.fullmatch(r"KINT-B22-(\d{10})",_clean(identifier).upper())
        if not m:return None
        n=int(m.group(1))
        if not 1<=n<=ADDRESSABLE_CONTENTS:return None
        ni,vi=divmod(n-1,VARIANTS_PER_NODE);bi,li=divmod(ni,10);b=INTEGRATION_BRANCHES[bi];lk,ll,ins=INTEGRATION_LENSES[li]
        return {"id":f"KINT-B22-{n:010d}","namespace":"B22","domain":b.domain,"domain_label":DOMAIN_LABELS[b.domain],"branch":b.key,"branch_label":b.label,"subtopics":b.subtopics,"lens":lk,"lens_label":ll,**_decode_axes(vi),"prompt":f"Integrar {b.label} pela lente {ll}: {ins}. Usar referência compartilhada e preservar estado epistêmico."}


class KnowledgeIntegrationEngine:
    NAMESPACE="B22"
    TAXONOMY_ROOT_ID="KNOWLEDGE-INTEGRATION-TAX-ROOT"
    MODEL_KINDS={"fact":"facts","observation":"observations","declared":"declared","memory":"memories","inference":"inferences","hypothesis":"hypotheses","prediction":"predictions","unknown":"unknowns","disputed":"hypotheses","superseded":"memories"}

    def __init__(self,knowledge:UniversalKnowledgeArchitecture,*,internal_models,metacognition=None,learning_evolution=None,reasoning_simulation=None,attention_salience=None):
        self.knowledge=knowledge;self.graph=knowledge.graph;self.internal_models=internal_models;self.metacognition=metacognition;self.learning_evolution=learning_evolution;self.reasoning_simulation=reasoning_simulation;self.attention_salience=attention_salience;self.catalog=IntegrationCatalog()
        self.knowledge.register_namespace(self.NAMESPACE,"BLOCO 22 — KNOWLEDGE INTEGRATION ENGINE",logical_capacity=ADDRESSABLE_CONTENTS,source="core/knowledge_integration.py",metadata={"materialization":"on-demand","shared_models":"B15","shared_graph":True,"copies_source_datasets":False,"parallel_models":False})

    @staticmethod
    def _models(models:Iterable[str]|None)->tuple[str,...]:
        aliases={"world":"world_model","human":"human_model","social":"social_model","self":"self_model","situation":"situation_model"}
        out=[]
        for raw in models or ():
            key=aliases.get(_norm(raw),_norm(raw))
            if key not in {"world_model","human_model","social_model","self_model","situation_model"}:raise KeyError(raw)
            if key not in out:out.append(key)
        return tuple(out)

    def integrate(self,content:str,*,source:str,reference:str,models:Iterable[str],epistemic_kind:str="inference",confidence:float=.5,relations:Iterable[dict]|None=None,expectations:Iterable[str]|None=None,predictions:Iterable[str]|None=None,interpretations:Iterable[str]|None=None,context:dict|None=None,judgments:Iterable[str]|None=None,canonical:bool=False)->dict:
        content=_clean(content);source=_clean(source);reference=_clean(reference);targets=self._models(models)
        if not content or not source or not reference:raise ValueError("integração exige conteúdo, fonte e referência")
        if not targets:raise ValueError("integração exige ao menos um modelo alvo")
        kind=_norm(epistemic_kind)
        if kind not in self.MODEL_KINDS:raise ValueError("estado epistêmico B22 inválido")
        if canonical and kind!="fact":raise ValueError("canonical=True exige epistemic_kind=fact")
        if kind=="fact" and not canonical:
            kind="inference"
        model_kind=self.MODEL_KINDS[kind]
        conf=_clamp(confidence)
        node_id=self.graph.stable_id("knowledge_integration_source",f"{reference}:{content}")
        self.graph.add_entity("knowledge_integration_source",content[:160],node_id=node_id,confidence=conf,data={"block":"B22","source":source,"reference":reference,"epistemic_kind":kind,"canonical":bool(canonical)})
        effects=[]
        for model in targets:
            safe_kind=model_kind
            if model=="self_model" and safe_kind=="facts":
                safe_kind="inferences"
            record=self.internal_models.record(model,safe_kind,{"content":content,"knowledge_ref":node_id,"reference":reference},source=source,confidence=conf)
            model_node=f"MODELS-B15-{model.upper()}"
            self.graph.add_entity("internal_model",model.replace("_"," ").upper(),node_id=model_node,data={"block":"B15"})
            self.graph.relate(node_id,model_node,"informs_model",weight=conf,metadata={"block":"B22","epistemic_kind":kind,"copies_data":False})
            effects.append({"model":model,"frame_kind":safe_kind,"record":record})

        relation_results=[]
        for rel in list(relations or ())[:32]:
            if not isinstance(rel,dict):continue
            target=_clean(rel.get("target")); relation=_clean(rel.get("relation")) or "related_to"
            if not target:continue
            target_id=self.graph.add_entity(_clean(rel.get("target_type")) or "knowledge_relation_target",target,data={"block":"B22"})
            self.graph.relate(node_id,target_id,relation,weight=_clamp(rel.get("weight",1.0)),metadata={"block":"B22","source_reference":reference})
            relation_results.append({"target":target,"relation":relation,"target_id":target_id})

        def bounded(values):return tuple(_clean(x) for x in (values or ()) if _clean(x))[:16]
        exps=bounded(expectations); preds=bounded(predictions); interps=bounded(interpretations); judges=bounded(judgments)
        for model in targets:
            if exps:self.internal_models.record(model,"predictions",{"type":"expectation","items":exps,"knowledge_ref":node_id},source=source,confidence=conf)
            for prediction in preds:self.internal_models.record(model,"predictions",{"prediction":prediction,"knowledge_ref":node_id},source=source,confidence=conf)
            for interpretation in interps:self.internal_models.record(model,"inferences",{"interpretation":interpretation,"knowledge_ref":node_id},source=source,confidence=conf)
            for judgment in judges:self.internal_models.record(model,"inferences",{"judgment":judgment,"knowledge_ref":node_id},source=source,confidence=conf)
            if context:
                safe_context={"knowledge_ref":node_id,"integrated_context":deepcopy(context),"temporary":model=="situation_model","identity_mutation":False,"permission_grant":False}
                self.internal_models.set_context(model,**safe_context)

        return {"knowledge_ref":node_id,"content":content,"source":source,"reference":reference,"epistemic_kind":kind,"canonical":bool(canonical and epistemic_kind=="fact"),"models":targets,"model_effects":effects,"relations":relation_results,"expectations":exps,"predictions":preds,"interpretations":interps,"judgments":judges,"context_updated":bool(context),"copies_source_datasets":False,"original_knowledge_mutated":False,"self_identity_mutation":False,"permission_granted":False,"operational_authorization":False}

    def integrate_situation(self,content:str,*,source:str,reference:str,active_entities=None,evidence=None,goal:str="",risk:float=0.0,urgency:float=0.0)->dict:
        integration=self.integrate(content,source=source,reference=reference,models=["situation_model"],epistemic_kind="observation",confidence=.7,context={"goal":_clean(goal)})
        cooperation=self.internal_models.cooperate(current_input=content,goal=goal,active_entities=active_entities,evidence=evidence,risk=risk,urgency=urgency)
        return {"integration":integration,"situation":cooperation,"temporary":True,"operational_authorization":False}

    def assess_before_integration(self,content:str,*,source:str,confidence:float=.5,contradictions=None)->dict:
        if self.metacognition is None:return {"available":False,"reason":"B20 unavailable"}
        return self.metacognition.assess(content,local_answer=True,confidence=confidence,sources=[source],contradictions=contradictions or ())

    def materialize_taxonomy(self,domain:str|None=None)->dict:
        key=_norm(domain) if domain else None
        if key and key not in _DOMAINS:raise KeyError(domain)
        selected=[b for b in INTEGRATION_BRANCHES if key is None or b.domain==key]
        root=self.graph.add_entity("knowledge_integration_taxonomy","KNOWLEDGE INTEGRATION ENGINE",node_id=self.TAXONOMY_ROOT_ID,data={"block":"B22","copies_source_datasets":False})
        for source_id,label in (("MODELS-B15-ROOT","B15 Models"),("METACOGNITION-TAX-ROOT","B20 Metacognition"),("LEARNING-EVOLUTION-TAX-ROOT","B21 Learning")):
            self.graph.add_entity("integration_source",label,node_id=source_id,data={"block":"B22"});self.graph.relate(root,source_id,"integrates",metadata={"block":"B22"})
        for b in selected:
            d=f"KINT-DOM-{b.domain.upper()}";br=f"KINT-BR-{b.key.upper()}";self.graph.add_entity("integration_domain",DOMAIN_LABELS[b.domain],node_id=d,data={"block":"B22"});self.graph.add_entity("integration_branch",b.label,node_id=br,data={"block":"B22"});self.graph.relate(root,d,"has_part",metadata={"block":"B22"});self.graph.relate(d,br,"has_part",metadata={"block":"B22"})
        return {"domain":key,"branches_materialized":len(selected),"shared_graph":True,"parallel_models_created":False}

    def stats(self)->dict:
        return {"status":"experimental-integrated","namespace":self.knowledge.store.get_namespace("B22"),"catalog":self.catalog.stats(),"policy":deepcopy(INTEGRATION_POLICY)}

    def handle(self,text:str)->str|None:
        raw=_clean(text);low=raw.casefold()
        if not raw:return None
        if low in {"status bloco 22","status knowledge integration","knowledge integration engine","status integracao de conhecimento","status integração de conhecimento"}:
            c=self.catalog.stats();return f"⭐ BLOCO 22 — KNOWLEDGE INTEGRATION: {c['addressable_contents']} representações | modelos B15 compartilhados | integrar ≠ copiar."
        item=self.catalog.get_variant(raw.upper())
        if item:return f"⭐ {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        return None
