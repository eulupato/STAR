"""BLOCO 21 — aprendizagem e evolução cognitiva.

Aprende por experiência, erro de previsão, revisão, consolidação e adaptação usando
os stores e motores já existentes. O bloco produz memória/conhecimento derivado
rastreável; nunca recebe autoridade irrestrita para editar o código central.
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
class LearningBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


_DOMAINS = {
    "experience_learning": (
        ("experience_capture", "Captura de experiência", "experiência;evento;fonte;referência;contexto"),
        ("experience_outcome", "Resultado da experiência", "resultado;sucesso;falha;observação;efeito"),
        ("experience_meaning", "Significado da experiência", "significado;interpretação;memória;relevância"),
        ("experience_recurrence", "Recorrência", "repetição;padrão;frequência;contexto;variação"),
        ("experience_limits", "Limites da experiência", "caso único;viés;exceção;escopo;incerteza"),
    ),
    "generalization": (
        ("pattern_generalization", "Generalização de padrões", "generalização;padrão;casos;escopo;inferência"),
        ("transfer", "Transferência", "transferência;novo contexto;similaridade;adaptação;teste"),
        ("counterexample", "Contraexemplo", "contraexemplo;exceção;limite;revisão;regra"),
        ("overgeneralization", "Sobregeneralização", "viés;amostra pequena;extrapolação;erro;correção"),
        ("generalization_validation", "Validação da generalização", "novos casos;teste;replicação;confiança"),
    ),
    "prediction_error": (
        ("prediction_record", "Registro da previsão", "previsão;baseline;confiança;horizonte;fonte"),
        ("outcome_observation", "Observação do resultado", "observado;resultado;medição;fonte;tempo"),
        ("prediction_error", "Prediction error", "prediction error;erro;previsto;observado;diferença"),
        ("calibration", "Calibração", "calibração;confiança;erro;histórico;ajuste"),
        ("error_learning", "Aprendizado pelo erro", "erro;feedback;revisão;estratégia;hipótese"),
    ),
    "revision": (
        ("revision_trigger", "Gatilho de revisão", "revisão;contradição;erro;fonte nova;baixa confiança"),
        ("revision_compare", "Comparação antes/depois", "versão;antes;depois;mudança;proveniência"),
        ("revision_scope", "Escopo da revisão", "memória;hipótese;modelo;previsão;conhecimento"),
        ("revision_preservation", "Preservação histórica", "não apagar;origem;histórico;superseded;auditoria"),
        ("revision_confidence", "Confiança revisada", "confiança;evidência;contradição;limite;calibração"),
    ),
    "consolidation": (
        ("memory_consolidation", "Consolidação de memória", "consolidação;memórias;semanticização;origem"),
        ("evidence_consolidation", "Consolidação de evidência", "evidência;fontes;corroboração;conflito"),
        ("pattern_consolidation", "Consolidação de padrão", "padrão;recorrência;regra provisória;exceções"),
        ("relation_consolidation", "Consolidação de relações", "relações;grafo;entidades;causas;contexto"),
        ("consolidation_limits", "Limites da consolidação", "resumo não substitui fontes;perda;incerteza"),
    ),
    "adaptation": (
        ("strategy_adaptation", "Adaptação de estratégia", "adaptação;estratégia;feedback;resultado;limite"),
        ("personality_adaptation", "Adaptação de personalidade", "personalidade adaptativa;experiência;bounded;histórico"),
        ("context_adaptation", "Adaptação ao contexto", "contexto;regra;situação;ajuste;reversão"),
        ("confidence_adaptation", "Adaptação de confiança", "confiança;calibração;erro;domínio;histórico"),
        ("adaptation_guardrails", "Guardrails de adaptação", "limite;taxa;identidade;permissão;segurança"),
    ),
    "cognitive_evolution": (
        ("evolution_trace", "Traço de evolução", "evolução;versão;histórico;mudança;fonte"),
        ("capability_growth", "Crescimento de capacidade", "capacidade;aprendizado;disponibilidade;teste;registro"),
        ("knowledge_growth", "Crescimento de conhecimento", "conhecimento;origem;integração;confiança;consistência"),
        ("model_growth", "Evolução dos modelos", "World Model;Human Model;Social Model;Self Model;Situation Model"),
        ("evolution_limits", "Limites da evolução", "não autoeditar código;permissão;validação;rollback"),
    ),
    "development": (
        ("cognitive_development", "Desenvolvimento cognitivo", "desenvolvimento cognitivo;estágio;competência;histórico"),
        ("skill_acquisition", "Aquisição de habilidade", "habilidade;prática;feedback;teste;competência"),
        ("learning_curve", "Curva de aprendizagem", "progresso;erro;tempo;repetição;platô"),
        ("retention", "Retenção", "retenção;memória;recall;esquecimento;reforço"),
        ("development_review", "Revisão do desenvolvimento", "avaliação;métrica;comparação;limites;próximo passo"),
    ),
    "consistency": (
        ("consistency_check", "Consistência", "consistência;contradição;regra;evidência;revisão"),
        ("source_consistency", "Consistência de fontes", "fonte;conflito;independência;proveniência"),
        ("memory_consistency", "Consistência de memória", "memória;versão;tempo;conflito;reconsolidação"),
        ("model_consistency", "Consistência de modelos", "modelos;estado;relação;incompatibilidade;revisão"),
        ("consistency_preservation", "Preservação da consistência", "origem;confiança;histórico;sem sobrescrita silenciosa"),
    ),
    "learning_governance": (
        ("learning_permission", "Permissão de aprendizagem", "aprendizado;permissão;escopo;dados;restrição"),
        ("code_boundary", "Fronteira de código", "código central;autoedição;patch;proibição;validação"),
        ("safe_experiment", "Experimento seguro", "sandbox;teste;reversibilidade;isolamento;resultado"),
        ("evaluation", "Avaliação", "métrica;score;benchmark;falha;recomendação"),
        ("rollback", "Rollback cognitivo", "rollback;versão;reversão;histórico;segurança"),
    ),
}

DOMAIN_LABELS = {key: key.replace("_", " ").title() for key in _DOMAINS}
LEARNING_BRANCHES = tuple(
    LearningBranch(domain, key, label, _subs(subtopics))
    for domain, branches in _DOMAINS.items()
    for key, label, subtopics in branches
)
LEARNING_LENSES = (
    ("experience", "experiência", "preservar evento e contexto de origem"),
    ("evidence", "evidência", "separar observação, memória e inferência"),
    ("pattern", "padrão", "identificar regularidade sem universalizar cedo"),
    ("error", "erro", "usar prediction error e falhas como feedback"),
    ("revision", "revisão", "versionar mudanças e preservar estado anterior"),
    ("consolidation", "consolidação", "relacionar sem apagar fontes"),
    ("adaptation", "adaptação", "aplicar mudança bounded e reversível quando possível"),
    ("confidence", "confiança", "propagar confiança e incerteza"),
    ("consistency", "consistência", "detectar contradições e manter rastreabilidade"),
    ("governance", "governança", "bloquear autoedição irrestrita do código central"),
)

CONTEXT_AXIS=("conversation","project","technical","scientific","social","personal","physical","digital","historical","mixed")
EXPERIENCE_AXIS=("none","single","repeated","successful","failed","mixed","surprising","expected","novel","revised")
CONFIDENCE_AXIS=("none","very_low","low","moderate_low","moderate","moderate_high","high","very_high","calibrated","conflicting")
SOURCE_AXIS=("B13","B17","B18","B20","user","tool","observation","canonical","external","mixed")
REVISION_AXIS=("none","candidate","review","refine","supersede","retract","consolidate","adapt","rollback","monitor")
CONSISTENCY_AXIS=("unknown","consistent","mostly_consistent","mixed","possible_conflict","conflicting","temporal_change","source_conflict","resolved_provisionally","validated")
MODE_AXIS=("primary","alternative")
VARIANT_AXES=(("context",CONTEXT_AXIS),("experience_state",EXPERIENCE_AXIS),("confidence_band",CONFIDENCE_AXIS),("source_space",SOURCE_AXIS),("revision_state",REVISION_AXIS),("consistency_state",CONSISTENCY_AXIS),("mode",MODE_AXIS))
CANONICAL_NODES=len(LEARNING_BRANCHES)*len(LEARNING_LENSES)
VARIANTS_PER_NODE=prod(len(v) for _,v in VARIANT_AXES)
ADDRESSABLE_CONTENTS=CANONICAL_NODES*VARIANTS_PER_NODE
if len(_DOMAINS)!=10 or len(LEARNING_BRANCHES)!=50 or len(LEARNING_LENSES)!=10: raise RuntimeError("B21 requer 10 domínios, 50 ramos e 10 lentes")
if CANONICAL_NODES!=500 or VARIANTS_PER_NODE!=2_000_000 or ADDRESSABLE_CONTENTS!=1_000_000_000: raise RuntimeError("escala B21 inválida")

LEARNING_POLICY={
    "experience_is_universal_rule":False,
    "generalization_is_fact":False,
    "prediction_error_rewrites_history":False,
    "revision_erases_source":False,
    "consolidation_erases_sources":False,
    "automatic_code_modification":False,
    "unrestricted_self_modification":False,
    "central_code_write_authority":False,
    "canonical_promotion_without_b2_b3":False,
    "bounded_context_selection":True,
    "rule":"APRENDER ≠ REESCREVER A HISTÓRIA; EVOLUIR ≠ AUTOEDITAR IRRESTRITAMENTE O CÓDIGO CENTRAL",
}


def _decode_axes(index:int)->dict[str,str]:
    if not 0<=int(index)<VARIANTS_PER_NODE: raise IndexError(index)
    value=int(index); out={}
    for name,values in reversed(VARIANT_AXES): value,off=divmod(value,len(values)); out[name]=values[off]
    return {name:out[name] for name,_ in VARIANT_AXES}


class LearningCatalog:
    NAMESPACE="B21"
    def stats(self)->dict:
        return {"namespace":"B21","domains":10,"branches":50,"lenses_per_branch":10,"canonical_nodes":CANONICAL_NODES,"variants_per_node":VARIANTS_PER_NODE,"addressable_contents":ADDRESSABLE_CONTENTS,"materialization":"on-demand","prepopulated_learning_events":0,"truthfulness_note":"1B are addressable learning contexts, not 1B fabricated experiences or learned facts"}
    @staticmethod
    def content_id(node_index:int,variant_index:int)->str:
        if not 0<=int(node_index)<CANONICAL_NODES: raise IndexError(node_index)
        if not 0<=int(variant_index)<VARIANTS_PER_NODE: raise IndexError(variant_index)
        return f"LEARN-B21-{int(node_index)*VARIANTS_PER_NODE+int(variant_index)+1:010d}"
    def get_variant(self,identifier:str)->dict|None:
        m=re.fullmatch(r"LEARN-B21-(\d{10})",_clean(identifier).upper())
        if not m:return None
        n=int(m.group(1))
        if not 1<=n<=ADDRESSABLE_CONTENTS:return None
        node_i,var_i=divmod(n-1,VARIANTS_PER_NODE); branch_i,lens_i=divmod(node_i,10)
        branch=LEARNING_BRANCHES[branch_i]; lens_key,lens_label,instruction=LEARNING_LENSES[lens_i]
        return {"id":f"LEARN-B21-{n:010d}","namespace":"B21","domain":branch.domain,"domain_label":DOMAIN_LABELS[branch.domain],"branch":branch.key,"branch_label":branch.label,"subtopics":branch.subtopics,"lens":lens_key,"lens_label":lens_label,**_decode_axes(var_i),"prompt":f"{branch.label} / {lens_label}: {instruction}. Preservar origem, confiança, consistência e histórico."}


class LearningEvolution:
    NAMESPACE="B21"
    TAXONOMY_ROOT_ID="LEARNING-EVOLUTION-TAX-ROOT"

    def __init__(self,knowledge:UniversalKnowledgeArchitecture,*,memory_continuity,reasoning_simulation,metacognition,affective_personality=None,self_improvement=None,attention_salience=None):
        self.knowledge=knowledge; self.graph=knowledge.graph
        self.memory_continuity=memory_continuity; self.reasoning_simulation=reasoning_simulation
        self.metacognition=metacognition; self.affective_personality=affective_personality
        self.self_improvement=self_improvement; self.attention_salience=attention_salience
        self.catalog=LearningCatalog()
        self.knowledge.register_namespace(self.NAMESPACE,"BLOCO 21 — APRENDIZAGEM E EVOLUÇÃO COGNITIVA",logical_capacity=ADDRESSABLE_CONTENTS,source="core/learning_evolution.py",metadata={"materialization":"on-demand","memory_store":"existing cognitive_memory","shared_knowledge_graph":True,"automatic_code_modification":False,"parallel_learning_database":False})

    def record_experience(self,content:str,*,source:str,reference:str,importance:float=.6,context:dict|None=None,meaning:str="")->dict:
        return self.memory_continuity.remember("autobiographical",content,source=source,reference=reference,importance=importance,context=context,experience=True,meaning=meaning,metadata={"block":"B21","learning_candidate":True})

    def prediction_feedback(self,predicted:float,observed:float,*,source:str,reference:str,context:str="")->dict:
        if not _clean(source) or not _clean(reference): raise ValueError("prediction error exige fonte e referência")
        error=self.reasoning_simulation.prediction_error(predicted,observed,context=context)
        metadata={"block":"B21","source":_clean(source),"reference":_clean(reference),"prediction_error":deepcopy(error),"history_rewritten":False,"canonical_knowledge":False}
        memory_id=self.memory_continuity.memory.remember("error",f"Prediction error: previsto={predicted}, observado={observed}",key=f"b21:error:{_norm(context) or 'general'}",metadata=metadata,importance=min(1.0,error["relative_error"]))
        return {"memory_id":memory_id,"prediction_error":error,"review_recommended":error["relative_error"]>=.2,"history_rewritten":False}

    def generalize(self,observations:Iterable[Any],*,scope:str,exceptions=None,source:str,reference:str,confidence:float=.5)->dict:
        artifact=self.reasoning_simulation.generalize(observations,scope=scope,exceptions=exceptions)
        conclusion=f"Generalização provisória em {_clean(scope)}"
        wm=self.memory_continuity.working.add(conclusion,source="B21 generalization",importance=_clamp(confidence),context={"artifact":deepcopy(artifact),"source":_clean(source),"reference":_clean(reference)},metadata={"block":"B21","epistemic_kind":"inference","canonical_fact":False})
        return {"artifact":artifact,"working_memory_id":wm["working_id"],"epistemic_kind":"inference","canonical_fact":False,"source":_clean(source),"reference":_clean(reference)}

    def revise_memory(self,memory_id:int,revised_content:str,*,source:str,reference:str,confidence:float=.7,reason:str="")->dict:
        original=self.memory_continuity.memory_record(int(memory_id))
        if original is None: raise KeyError(memory_id)
        result=self.memory_continuity.remember("semantic",revised_content,source=source,reference=reference,importance=confidence,confidence=confidence,meaning=reason,context={"revises_memory_id":int(memory_id)},metadata={"block":"B21","revision":True,"original_preserved":True})
        self.memory_continuity.relate_memories(result["memory_id"],int(memory_id),"revises",metadata={"block":"B21","original_preserved":True})
        return {**result,"original_memory_id":int(memory_id),"original_preserved":True,"canonical_promotion_performed":False}

    def consolidate(self,memory_ids:Iterable[int],summary:str,*,source:str,reference:str,meaning:str="")->dict:
        result=self.memory_continuity.consolidate(memory_ids,summary,source=source,reference=reference,meaning=meaning)
        return {**result,"block":"B21","canonical_promotion_performed":False}

    def assess_consistency(self,statement:str,*,sources=None,contradictions=None,confidence:float=.5)->dict:
        return self.metacognition.assess(statement,local_answer=True,confidence=confidence,sources=sources,contradictions=contradictions)

    def adapt_personality(self,experience_memory_id:int,adjustments:dict[str,float],*,source:str,reference:str,learning_rate:float=.05,reason:str="")->dict:
        if self.affective_personality is None: raise RuntimeError("B17 AffectivePersonality indisponível")
        result=self.affective_personality.adapt_from_experience(experience_memory_id,adjustments,source=source,reference=reference,learning_rate=learning_rate,reason=reason)
        return {**result,"block":"B21","code_mutation":False}

    def evaluate_learning(self,component:str,metric:str,score:float,details=None)->dict:
        if self.self_improvement is None: return {"recorded":False,"reason":"self_improvement_unavailable","code_mutation":False}
        value=self.self_improvement.record(component,metric,score,details)
        return {"recorded":True,"score":value,"code_mutation":False,"automatic_patch":False}

    def learning_cycle(self,experience_content:str,*,source:str,reference:str,predicted:float|None=None,observed:float|None=None,scope:str="local",observations=None,contradictions=None)->dict:
        exp=self.record_experience(experience_content,source=source,reference=reference,meaning="B21 audited learning experience")
        error=None
        if predicted is not None and observed is not None: error=self.prediction_feedback(predicted,observed,source=source,reference=reference,context=scope)
        general=None
        if observations: general=self.generalize(observations,scope=scope,source=source,reference=reference)
        meta=self.metacognition.assess(experience_content,local_answer=True,confidence=.6,sources=[source],contradictions=contradictions or ())
        return {"experience":exp,"prediction_feedback":error,"generalization":general,"metacognition":meta,"code_mutation":False,"automatic_code_modification":False,"canonical_promotion_performed":False}

    def code_change_request(self,*_args,**_kwargs)->dict:
        return {"allowed":False,"automatic":False,"reason":"B21 não possui autoridade para modificar irrestritamente o código central; mudanças exigem fluxo externo autorizado, testes e validação"}

    def materialize_taxonomy(self,domain:str|None=None)->dict:
        key=_norm(domain) if domain else None
        if key and key not in _DOMAINS: raise KeyError(domain)
        selected=[b for b in LEARNING_BRANCHES if key is None or b.domain==key]
        root=self.graph.add_entity("learning_evolution_taxonomy","APRENDIZAGEM E EVOLUÇÃO COGNITIVA",node_id=self.TAXONOMY_ROOT_ID,data={"block":"B21","automatic_code_modification":False})
        for source_id,label in (("MEMORY-TAX-ROOT","B13 Memory"),("AFFECTIVE-PERSONALITY-TAX-ROOT","B17 Personality"),("REASONING-SIMULATION-TAX-ROOT","B18 Reasoning"),("METACOGNITION-TAX-ROOT","B20 Metacognition")):
            self.graph.add_entity("learning_source",label,node_id=source_id,data={"block":"B21"}); self.graph.relate(root,source_id,"integrates",metadata={"block":"B21"})
        for b in selected:
            d=f"LEARN-DOM-{b.domain.upper()}"; br=f"LEARN-BR-{b.key.upper()}"
            self.graph.add_entity("learning_domain",DOMAIN_LABELS[b.domain],node_id=d,data={"block":"B21"}); self.graph.add_entity("learning_branch",b.label,node_id=br,data={"block":"B21"}); self.graph.relate(root,d,"has_part",metadata={"block":"B21"}); self.graph.relate(d,br,"has_part",metadata={"block":"B21"})
        return {"domain":key,"branches_materialized":len(selected),"knowledge_graph":"shared","parallel_learning_database":False}

    def stats(self)->dict:
        return {"status":"experimental-integrated","namespace":self.knowledge.store.get_namespace("B21"),"catalog":self.catalog.stats(),"policy":deepcopy(LEARNING_POLICY)}

    def handle(self,text:str)->str|None:
        raw=_clean(text); low=raw.casefold()
        if not raw:return None
        if low in {"status bloco 21","status aprendizagem","aprendizagem e evolucao cognitiva","aprendizagem e evolução cognitiva"}:
            c=self.catalog.stats(); return f"⭐ BLOCO 21 — APRENDIZAGEM: {c['addressable_contents']} representações | experiência/revisão/consolidação auditáveis | autoedição irrestrita de código = NÃO."
        item=self.catalog.get_variant(raw.upper())
        if item:return f"⭐ {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        return None
