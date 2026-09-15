from core.body_proprioception import ADDRESSABLE_CONTENTS, BodyProprioception
from core.mind import CognitiveSuite
from core.multimodal_perception import MultimodalPerception
from core.universal_knowledge import UniversalKnowledgeArchitecture

def _stack():
 m=CognitiveSuite();k=UniversalKnowledgeArchitecture(m.epistemics,m.graph);p=MultimodalPerception(k);return BodyProprioception(k,perception=p),p

def test_b27_exact_1b_and_body_is_endpoint():
 body,_=_stack();assert ADDRESSABLE_CONTENTS==1_000_000_000;assert body.stats()["body_is_endpoint"] is True;assert body.stats()["direct_actuation"] is False

def test_proprioception_feeds_b25_without_fabrication():
 body,p=_stack();body.configure(body_id="STAR-BODY-1",joints=[{"id":"j1"}],sensors=[{"id":"imu"}])
 s=body.update_proprioception({"position":[1,2,3],"orientation":[0,0,1],"movement":{"speed":.2},"confidence":.9},source="imu")
 assert s["fabricated"] is False;obs=p.workspace_observations(limit=4);assert obs;assert obs[0]["fabricated"] is False

def test_body_motion_is_boundary_only_never_direct_actuation():
 body,_=_stack();r=body.request_motion({"joint":"j1","target":10},permission=True,capability=True,safety_ok=True,authorization_source="test")
 assert r["executed"] is False;assert r["body_module_actuates_hardware"] is False

def test_missing_endpoint_fails_closed():
 body,_=_stack();r=body.poll_endpoint();assert r=={"available":False,"state":None,"fabricated":False}

def test_configuration_is_bounded():
 body,_=_stack();cfg=body.configure(body_id="B",joints=[{"id":i} for i in range(1000)],sensors=[{"id":i} for i in range(1000)])
 assert len(cfg["joints"])==body.MAX_JOINTS;assert len(cfg["sensors"])==body.MAX_SENSORS
