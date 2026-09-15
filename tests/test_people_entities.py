from core.mind import CognitiveSuite
from core.memory_continuity import MemoryContinuity
from core.people_entities import ADDRESSABLE_CONTENTS, PeopleEntities
from core.universal_knowledge import UniversalKnowledgeArchitecture

def _stack():
 m=CognitiveSuite();k=UniversalKnowledgeArchitecture(m.epistemics,m.graph);mem=MemoryContinuity(k,memory=m.memory,graph=m.graph,projects=m.projects);return PeopleEntities(k,memory_continuity=mem),mem

def test_b26_exact_1b_and_shared_memory_graph():
 people,mem=_stack();assert ADDRESSABLE_CONTENTS==1_000_000_000;assert people.memory is mem;assert people.stats()["shared_graph"] is True

def test_person_is_persistent_entity_with_people_memory():
 people,mem=_stack();p=people.create_person("Ana",aliases=("Aninha",),source="declared",reference="turn-1")
 assert p["person_id"].startswith("PERSON-");assert p["authentication_status"]=="not_authenticated"
 rec=mem.memory_record(p["memory_id"]);assert rec is not None;assert rec["kind"]=="people"

def test_recognition_never_authenticates_or_grants_permission():
 people,_=_stack();r=people.recognition_hypothesis([{"person_id":"PERSON-X","confidence":.99}],signals=[{"modality":"face"}])
 assert r["authenticated"] is False;assert r["grants_permission"] is False
 a=people.authenticate("PERSON-X");assert a["authenticated"] is False;assert a["recognition_used_as_authentication"] is False

def test_trust_relation_is_not_permission():
 people,_=_stack();a=people.create_person("A",source="test");b=people.create_person("B",source="test")
 r=people.set_relation(a["person_id"],b["person_id"],"friend",confidence=.9,source="declared")
 assert r["confidence"]==.9;assert r["permission"] is False
