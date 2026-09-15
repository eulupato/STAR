"""BLOCO 26 — pessoas como entidades persistentes.

Especializa B13/B16/B25 usando o Knowledge Graph e a memória oficiais. Não cria
um banco de pessoas paralelo. Reconhecimento produz hipótese de identidade;
autenticação é uma fronteira separada e nunca é concedida por reconhecimento,
confiança social, nome, voz ou rosto isoladamente.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from math import prod
import hashlib, re, unicodedata
from typing import Any, Iterable
from core.universal_knowledge import UniversalKnowledgeArchitecture

def _clean(v: Any)->str:return " ".join(str(v or "").strip().split())
def _norm(v: Any)->str:
    t=unicodedata.normalize("NFKD",_clean(v));t="".join(c for c in t if not unicodedata.combining(c)).casefold()
    return re.sub(r"[^a-z0-9]+","_",t).strip("_")
def _clamp(v:Any,d=.5)->float:
    try:return max(0.,min(float(v),1.))
    except (TypeError,ValueError):return d
def _now()->str:return datetime.now(timezone.utc).isoformat()

DOMAINS={
"identity":("identity_reference","name","alias","declared_attribute","identity_evidence","identity_conflict","identity_change","unknown_identity","merge_candidate","provenance"),
"relationship":("relation_type","role","history","boundary","reciprocity","distance","change","shared_context","relationship_event","uncertainty"),
"preferences":("declared_preference","observed_choice","dislike","constraint","contextual_preference","revision","confidence","source","exception","unknown"),
"interactions":("conversation","meeting","request","response","commitment","conflict","cooperation","shared_task","outcome","followup"),
"events":("shared_event","personal_event_reference","time","place","participants","outcome","meaning","source","uncertainty","continuity"),
"context":("social","family","friendship","work","school","public","digital","home","project","situational"),
"permissions":("consent","scope","purpose","duration","revocation","privacy","data_access","device_access","action_boundary","default_deny"),
"trust":("evidence","reliability","competence","consistency","context","risk","revision","conflict","uncertainty","trust_not_permission"),
"memories":("people_memory","social_memory","episodic_link","conversation_link","preference_link","event_link","relationship_link","source_link","recall","forgetting_boundary"),
"recognition_auth":("recognition_hypothesis","face_signal","voice_signal","context_signal","multimodal_match","ambiguity","authentication_challenge","auth_result","credential_boundary","recognition_not_auth"),
}
LENSES=("concept","evidence","temporal","context","relation","confidence","privacy","uncertainty","revision","boundary")
AXES=(("source",tuple(str(i) for i in range(10))),("time",tuple(str(i) for i in range(10))),("context",tuple(str(i) for i in range(10))),("confidence",tuple(str(i) for i in range(10))),("relation",tuple(str(i) for i in range(10))),("permission",tuple(str(i) for i in range(10))))
CANONICAL_NODES=len(DOMAINS)*10*len(LENSES);VARIANTS_PER_NODE=prod(len(x) for _,x in AXES);ADDRESSABLE_CONTENTS=CANONICAL_NODES*VARIANTS_PER_NODE
if CANONICAL_NODES!=1000 or VARIANTS_PER_NODE!=1_000_000 or ADDRESSABLE_CONTENTS!=1_000_000_000:raise RuntimeError("escala B26 inválida")

class PeopleEntities:
    NAMESPACE="B26"
    def __init__(self,knowledge:UniversalKnowledgeArchitecture,*,memory_continuity,social_cognition=None,perception=None):
        self.knowledge=knowledge;self.graph=knowledge.graph;self.memory=memory_continuity;self.social=social_cognition;self.perception=perception
        knowledge.register_namespace("B26","BLOCO 26 — PESSOAS COMO ENTIDADES PERSISTENTES",logical_capacity=ADDRESSABLE_CONTENTS,source="core/people_entities.py",metadata={"materialization":"on-demand","shared_graph":True,"shared_memory":"B13","recognition_is_authentication":False,"trust_is_permission":False,"default_deny":True})

    def create_person(self,name:str,*,aliases:Iterable[str]=(),source:str,reference:str="",metadata:dict|None=None)->dict:
        name=_clean(name);source=_clean(source)
        if not name or not source:raise ValueError("pessoa requer nome/referência e fonte")
        aliases=tuple(dict.fromkeys(_clean(x) for x in aliases if _clean(x)))[:32]
        stable=_norm(name+"|"+source+"|"+_clean(reference))
        pid="PERSON-"+hashlib.sha256(stable.encode()).hexdigest()[:24].upper()
        node=self.graph.add_entity("person",name,node_id=pid,data={"block":"B26","aliases":aliases,"source":source,"reference":_clean(reference),"metadata":deepcopy(metadata or {}),"authentication_status":"not_authenticated"})
        mem=self.memory.remember("people",f"Pessoa: {name}",source=source,reference=reference,entities=[pid],metadata={"person_id":pid,"aliases":list(aliases),"recognition_not_authentication":True})
        self.graph.relate(node,mem["memory_node_id"],"has_memory",metadata={"block":"B26"})
        return {"person_id":pid,"name":name,"aliases":aliases,"memory_id":mem["memory_id"],"authentication_status":"not_authenticated"}

    def remember_interaction(self,person_id:str,content:str,*,source:str,reference:str="",context:dict|None=None,importance:float=.6)->dict:
        mem=self.memory.remember("people",content,source=source,reference=reference,entities=[person_id],context=context,importance=importance,metadata={"person_id":person_id,"interaction":True})
        self.graph.relate(person_id,mem["memory_node_id"],"has_interaction",metadata={"block":"B26"})
        return mem

    def set_relation(self,source_person_id:str,target_person_id:str,relation:str,*,confidence:float=.5,source:str)->dict:
        relation=_clean(relation)
        if not relation:raise ValueError("relação vazia")
        self.graph.relate(source_person_id,target_person_id,"person_relation",weight=_clamp(confidence),metadata={"block":"B26","relation":relation,"source":_clean(source),"permission":False})
        return {"source":source_person_id,"target":target_person_id,"relation":relation,"confidence":_clamp(confidence),"permission":False}

    def recognition_hypothesis(self,candidates:Iterable[dict],*,signals:Iterable[dict]=())->dict:
        ranked=sorted((deepcopy(x) for x in candidates if isinstance(x,dict)),key=lambda x:_clamp(x.get("confidence"),0),reverse=True)[:8]
        return {"status":"hypothesis","candidates":ranked,"signals":deepcopy(list(signals or ()))[:16],"authenticated":False,"grants_permission":False,"requires_authentication_for_privileged_actions":True}

    def authenticate(self,person_id:str,*,verifier=None,challenge:Any=None)->dict:
        if verifier is None:return {"person_id":person_id,"authenticated":False,"reason":"authentication_verifier_unavailable","recognition_used_as_authentication":False}
        try:result=verifier.verify(person_id,challenge)
        except (AttributeError,RuntimeError,ValueError,OSError):return {"person_id":person_id,"authenticated":False,"reason":"authentication_failed_closed","recognition_used_as_authentication":False}
        ok=bool(result.get("authenticated")) if isinstance(result,dict) else bool(result)
        return {"person_id":person_id,"authenticated":ok,"result":deepcopy(result),"recognition_used_as_authentication":False,"operational_permission":False}

    def person_context(self,person_id:str,*,limit:int=16)->dict:
        memories=[x for x in self.memory.recall(person_id,kinds=("people","social","episodic","conversation"),limit=min(max(int(limit),1),32)) if person_id in str(x.get("metadata") or {}) or person_id in _clean(x.get("content"))]
        return {"person_id":person_id,"memories":memories[:limit],"relations":self.graph.neighbors(person_id,limit=min(limit,32)),"bounded":True}

    def stats(self)->dict:return {"status":"experimental-integrated","namespace":self.knowledge.store.get_namespace("B26"),"addressable_contents":ADDRESSABLE_CONTENTS,"shared_graph":True,"shared_memory":True,"recognition_is_authentication":False}
    def handle(self,text:str)->str|None:
        if _clean(text).casefold() in {"status bloco 26","status pessoas","status entidades pessoais"}:return f"👥 BLOCO 26 — PESSOAS: {ADDRESSABLE_CONTENTS} relações/conhecimentos endereçáveis | memória=B13 | reconhecimento ≠ autenticação."
        return None
