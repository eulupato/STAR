"""BLOCO 27 — corpo e propriocepção.

Modelo corporal integrado ao B04/B25. O corpo é um endpoint: este módulo mantém
configuração, limites, calibração e estado proprioceptivo; não vira a identidade
da STAR e não envia comandos a servos/hardware diretamente.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from math import prod
import re, unicodedata
from typing import Any, Iterable
from core.universal_knowledge import UniversalKnowledgeArchitecture

def _clean(v:Any)->str:return " ".join(str(v or "").strip().split())
def _norm(v:Any)->str:
 t=unicodedata.normalize("NFKD",_clean(v));t="".join(c for c in t if not unicodedata.combining(c)).casefold();return re.sub(r"[^a-z0-9]+","_",t).strip("_")
def _clamp(v:Any,d=.5)->float:
 try:return max(0.,min(float(v),1.))
 except (TypeError,ValueError):return d

DOMAINS={
"kinematics":("position","velocity","acceleration","trajectory","frame","transform","forward_kinematics","inverse_kinematics","constraint","uncertainty"),
"orientation":("roll","pitch","yaw","quaternion","gravity_reference","heading","pose","frame_alignment","drift","uncertainty"),
"movement":("commanded_motion","observed_motion","motion_state","direction","speed","stability","collision_candidate","reach","locomotion","stop"),
"energy":("battery","voltage","current","power","consumption","thermal","reserve","charging","energy_limit","unknown"),
"sensors":("encoder","imu","force","torque","proximity","temperature","current_sensor","camera_reference","sensor_health","fusion"),
"joints":("joint","angle","velocity","torque","range","limit","backlash","load","joint_state","fault"),
"servos":("servo","target","feedback","load","temperature","limit","health","latency","controller_reference","fault"),
"dimensions":("length","width","height","mass","center_of_mass","reach_envelope","clearance","geometry","payload","uncertainty"),
"calibration":("zero","offset","scale","alignment","bias","drift","reference","timestamp","quality","recalibration"),
"hardware":("endpoint","device","bus","controller","driver_reference","capability","availability","health","boundary","disconnect"),
}
LENSES=("concept","state","measurement","relation","limit","risk","calibration","prediction","uncertainty","interaction")
AXES=(("body",tuple(str(i) for i in range(10))),("state",tuple(str(i) for i in range(10))),("context",tuple(str(i) for i in range(10))),("confidence",tuple(str(i) for i in range(10))),("temporal",tuple(str(i) for i in range(10))),("interaction",tuple(str(i) for i in range(10))))
CANONICAL_NODES=len(DOMAINS)*10*len(LENSES);VARIANTS_PER_NODE=prod(len(x) for _,x in AXES);ADDRESSABLE_CONTENTS=CANONICAL_NODES*VARIANTS_PER_NODE
if CANONICAL_NODES!=1000 or VARIANTS_PER_NODE!=1_000_000 or ADDRESSABLE_CONTENTS!=1_000_000_000:raise RuntimeError("escala B27 inválida")

class BodyProprioception:
 NAMESPACE="B27";MAX_JOINTS=256;MAX_SENSORS=256
 def __init__(self,knowledge:UniversalKnowledgeArchitecture,*,physical_world=None,perception=None,operational_boundary=None):
  self.knowledge=knowledge;self.graph=knowledge.graph;self.physical_world=physical_world;self.perception=perception;self.operational_boundary=operational_boundary
  self._config={};self._state={};self._calibration={};self._endpoint=None
  knowledge.register_namespace("B27","BLOCO 27 — CORPO E PROPRIOCEPÇÃO",logical_capacity=ADDRESSABLE_CONTENTS,source="core/body_proprioception.py",metadata={"materialization":"on-demand","body_is_endpoint":True,"body_is_star_identity":False,"direct_actuation":False,"sensor_fusion":"B25","default_deny":True})

 def configure(self,*,body_id:str,dimensions:dict|None=None,joints:Iterable[dict]=(),servos:Iterable[dict]=(),sensors:Iterable[dict]=(),limits:dict|None=None,hardware:dict|None=None)->dict:
  body_id=_clean(body_id)
  if not body_id:raise ValueError("body_id obrigatório")
  js=[deepcopy(x) for x in joints if isinstance(x,dict)][:self.MAX_JOINTS];ss=[deepcopy(x) for x in servos if isinstance(x,dict)][:self.MAX_JOINTS];sns=[deepcopy(x) for x in sensors if isinstance(x,dict)][:self.MAX_SENSORS]
  self._config={"body_id":body_id,"dimensions":deepcopy(dimensions or {}),"joints":js,"servos":ss,"sensors":sns,"limits":deepcopy(limits or {}),"hardware":deepcopy(hardware or {}),"body_is_endpoint":True}
  return deepcopy(self._config)

 def attach_endpoint(self,endpoint:Any)->None:self._endpoint=endpoint
 def detach_endpoint(self)->None:self._endpoint=None

 def update_proprioception(self,observation:dict,*,source:str="body_endpoint")->dict:
  if not isinstance(observation,dict):raise TypeError("observation deve ser dict")
  state={"timestamp":_clean(observation.get("timestamp")) or datetime.now(timezone.utc).isoformat(),"position":deepcopy(observation.get("position")),"orientation":deepcopy(observation.get("orientation")),"movement":deepcopy(observation.get("movement")),"energy":deepcopy(observation.get("energy")),"joints":deepcopy(list(observation.get("joints") or ()))[:self.MAX_JOINTS],"servos":deepcopy(list(observation.get("servos") or ()))[:self.MAX_JOINTS],"sensors":deepcopy(list(observation.get("sensors") or ()))[:self.MAX_SENSORS],"confidence":_clamp(observation.get("confidence"),.5),"source":_clean(source),"fabricated":False,"operational_authorization":False}
  self._state=state
  if self.perception is not None:
   summary=f"body pose/state update: position={state['position']} orientation={state['orientation']} movement={state['movement']}"
   self.perception.ingest("sensor",{"content":summary,"confidence":state["confidence"],"entities":[self._config.get("body_id","body")],"event_key":"body-proprioception"} ,source=source)
  return deepcopy(state)

 def calibrate(self,calibration:dict,*,source:str,reference:str="")->dict:
  if not isinstance(calibration,dict) or not calibration:raise ValueError("calibração vazia")
  self._calibration={"values":deepcopy(calibration),"source":_clean(source),"reference":_clean(reference),"timestamp":datetime.now(timezone.utc).isoformat(),"applied_to_hardware":False}
  return deepcopy(self._calibration)

 def poll_endpoint(self)->dict:
  if self._endpoint is None or not hasattr(self._endpoint,"read_proprioception"):return {"available":False,"state":None,"fabricated":False}
  try:raw=self._endpoint.read_proprioception()
  except (AttributeError,OSError,RuntimeError,ValueError):return {"available":False,"state":None,"fabricated":False}
  return {"available":True,"state":self.update_proprioception(raw,source="body_endpoint"),"fabricated":False}

 def request_motion(self,command:dict,*,permission:bool=False,capability:bool=False,safety_ok:bool=False,authorization_source:str|None=None)->dict:
  if self.operational_boundary is not None:
   boundary=self.operational_boundary.evaluate(f"body motion: {_clean(command)}",permission=permission,capability=capability,safety_ok=safety_ok,authorization_source=authorization_source)
  else:boundary={"can_act":bool(permission and capability and safety_ok)}
  return {"command":deepcopy(command),"boundary":boundary,"eligible_for_separate_endpoint_execution":bool(boundary.get("can_act")),"executed":False,"body_module_actuates_hardware":False}

 def state(self)->dict:return {"configuration":deepcopy(self._config),"proprioception":deepcopy(self._state),"calibration":deepcopy(self._calibration),"endpoint_available":self._endpoint is not None}
 def stats(self)->dict:return {"status":"experimental-integrated","namespace":self.knowledge.store.get_namespace("B27"),"addressable_contents":ADDRESSABLE_CONTENTS,"body_is_endpoint":True,"direct_actuation":False,"endpoint_available":self._endpoint is not None}
 def handle(self,text:str)->str|None:
  if _clean(text).casefold() in {"status bloco 27","status corpo","status propriocepção","status propriocepcao"}:return f"🤖 BLOCO 27 — CORPO/PROPRIOCEPÇÃO: {ADDRESSABLE_CONTENTS} conhecimentos endereçáveis | corpo=ENDPOINT | atuação direta=NÃO."
  return None
