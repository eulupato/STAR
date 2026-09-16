"""BLOCO 26 — pessoas como entidades persistentes.

Usa B13/B16/B25, o Knowledge Graph e o banco oficiais. Não cria um banco de
pessoas paralelo. Reconhecimento é hipótese; autenticação e permissão permanecem
fronteiras separadas. Perfis declarados e referências perceptivas podem ser
associados sem persistir biometria bruta automaticamente.
"""
from __future__ import annotations

from copy import deepcopy
from math import prod
import hashlib
import json
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


def _clamp(value: Any, default: float = 0.5) -> float:
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        return default


DOMAINS = {
    "identity": ("identity_reference", "name", "alias", "declared_attribute", "identity_evidence", "identity_conflict", "identity_change", "unknown_identity", "merge_candidate", "provenance"),
    "relationship": ("relation_type", "role", "history", "boundary", "reciprocity", "distance", "change", "shared_context", "relationship_event", "uncertainty"),
    "preferences": ("declared_preference", "observed_choice", "dislike", "constraint", "contextual_preference", "revision", "confidence", "source", "exception", "unknown"),
    "interactions": ("conversation", "meeting", "request", "response", "commitment", "conflict", "cooperation", "shared_task", "outcome", "followup"),
    "events": ("shared_event", "personal_event_reference", "time", "place", "participants", "outcome", "meaning", "source", "uncertainty", "continuity"),
    "context": ("social", "family", "friendship", "work", "school", "public", "digital", "home", "project", "situational"),
    "permissions": ("consent", "scope", "purpose", "duration", "revocation", "privacy", "data_access", "device_access", "action_boundary", "default_deny"),
    "trust": ("evidence", "reliability", "competence", "consistency", "context", "risk", "revision", "conflict", "uncertainty", "trust_not_permission"),
    "memories": ("people_memory", "social_memory", "episodic_link", "conversation_link", "preference_link", "event_link", "relationship_link", "source_link", "recall", "forgetting_boundary"),
    "recognition_auth": ("recognition_hypothesis", "face_signal", "voice_signal", "context_signal", "multimodal_match", "ambiguity", "authentication_challenge", "auth_result", "credential_boundary", "recognition_not_auth"),
}
LENSES = ("concept", "evidence", "temporal", "context", "relation", "confidence", "privacy", "uncertainty", "revision", "boundary")
AXES = tuple((name, tuple(str(i) for i in range(10))) for name in ("source", "time", "context", "confidence", "relation", "permission"))
CANONICAL_NODES = len(DOMAINS) * 10 * len(LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE
if CANONICAL_NODES != 1_000 or VARIANTS_PER_NODE != 1_000_000 or ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("escala B26 inválida")


class PeopleEntities:
    NAMESPACE = "B26"
    MAX_PROFILE_FIELDS = 64

    def __init__(self, knowledge: UniversalKnowledgeArchitecture, *, memory_continuity, social_cognition=None, perception=None):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.memory = memory_continuity
        self.social = social_cognition
        self.perception = perception
        self.active_person_id: str | None = None
        self.active_person_name: str | None = None
        self.on_active_person = None
        knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 26 — PESSOAS COMO ENTIDADES PERSISTENTES",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/people_entities.py",
            metadata={
                "materialization": "on-demand",
                "shared_graph": True,
                "shared_memory": "B13",
                "recognition_is_authentication": False,
                "trust_is_permission": False,
                "raw_biometric_storage_by_default": False,
                "sensitive_attribute_inference": False,
                "default_deny": True,
            },
        )

    def _activate(self, person: dict) -> dict:
        self.active_person_id = person.get("person_id")
        self.active_person_name = _clean(person.get("name")) or self.active_person_name
        if callable(self.on_active_person):
            try:
                self.on_active_person(deepcopy(person))
            except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
                pass
        return person

    @staticmethod
    def _safe_profile(profile: dict | None) -> dict:
        output = {}
        for key, value in list(dict(profile or {}).items())[: PeopleEntities.MAX_PROFILE_FIELDS]:
            name = _clean(key)[:80]
            if not name:
                continue
            if isinstance(value, str):
                output[name] = _clean(value)[:500]
            elif isinstance(value, (int, float, bool)) or value is None:
                output[name] = value
            elif isinstance(value, (list, tuple)):
                output[name] = [_clean(item)[:200] for item in value[:32] if _clean(item)]
        return output

    def create_person(self, name: str, *, aliases: Iterable[str] = (), source: str, reference: str = "", metadata: dict | None = None) -> dict:
        name, source, reference = _clean(name), _clean(source), _clean(reference)
        if not name or not source:
            raise ValueError("pessoa requer nome/referência e fonte")
        aliases = tuple(dict.fromkeys(_clean(x) for x in aliases if _clean(x)))[:32]
        stable = _norm(f"{name}|{source}|{reference}")
        pid = "PERSON-" + hashlib.sha256(stable.encode()).hexdigest()[:24].upper()
        safe_metadata = deepcopy(metadata or {})
        safe_metadata.pop("inferred_sensitive_attributes", None)
        node = self.graph.add_entity(
            "person",
            name,
            node_id=pid,
            data={
                "block": "B26", "aliases": aliases, "source": source, "reference": reference,
                "metadata": safe_metadata, "authentication_status": "not_authenticated",
                "sensitive_attribute_inference": False,
            },
        )
        mem = self.memory.remember(
            "people", f"Pessoa: {name}", source=source, reference=reference, entities=[pid],
            metadata={
                "person_id": pid, "person_name": name, "aliases": list(aliases),
                "recognition_not_authentication": True, "authentication_status": "not_authenticated",
                "sensitive_attribute_inference": False,
            },
        )
        self.graph.relate(node, mem["memory_node_id"], "has_memory", metadata={"block": "B26"})
        return {"person_id": pid, "name": name, "aliases": aliases, "memory_id": mem["memory_id"], "authentication_status": "not_authenticated"}

    def find_people(self, name_or_alias: str, *, limit: int = 8) -> list[dict]:
        query = _clean(name_or_alias)
        if not query:
            return []
        wanted = _norm(query)
        recalled = self.memory.recall(query, kinds=("people",), limit=min(max(int(limit) * 4, 8), 64), include_working=False)
        found = {}
        for item in recalled:
            metadata = item.get("metadata") or {}
            person_id = metadata.get("person_id")
            if not person_id:
                continue
            name = _clean(metadata.get("person_name"))
            aliases = tuple(_clean(x) for x in metadata.get("aliases", ()) if _clean(x))
            labels = {_norm(name), *(_norm(x) for x in aliases)}
            if wanted not in labels and wanted not in _norm(item.get("content")):
                continue
            entry = found.setdefault(person_id, {"person_id": person_id, "name": name or query, "aliases": aliases, "memory_ids": [], "authenticated": False})
            if item.get("id") is not None:
                entry["memory_ids"].append(int(item["id"]))
        return list(found.values())[: max(1, min(int(limit), 32))]

    def upsert_declared_person(self, name: str, *, aliases: Iterable[str] = (), source: str, reference: str, profile: dict | None = None) -> dict:
        """Só reutiliza uma correspondência nominal inequívoca; nunca faz face-merge."""
        candidates = self.find_people(name, limit=8)
        if len(candidates) == 1:
            person = {**candidates[0], "reused": True, "authentication_status": "not_authenticated"}
        else:
            person = self.create_person(name, aliases=aliases, source=source, reference=reference, metadata={"declared_by_user": True})
            person["reused"] = False
            if len(candidates) > 1:
                person["identity_merge_deferred"] = True
                person["ambiguous_candidates"] = [item["person_id"] for item in candidates]
        if profile:
            self.remember_profile(person["person_id"], profile, source=source, reference=reference, declared=True)
        return self._activate(person)

    def remember_profile(self, person_id: str, profile: dict, *, source: str, reference: str, declared: bool = True, importance: float = 0.7) -> dict:
        safe = self._safe_profile(profile)
        if not safe:
            raise ValueError("perfil vazio")
        compact = json.dumps(safe, ensure_ascii=False, sort_keys=True)
        mem = self.memory.remember(
            "people", f"Perfil {'declarado' if declared else 'observado'}: {compact}",
            source=source, reference=reference, entities=[person_id], importance=importance,
            metadata={
                "person_id": person_id, "profile": safe, "declared_profile": bool(declared),
                "sensitive_attribute_inference": False, "recognition_not_authentication": True,
            },
        )
        self.graph.relate(person_id, mem["memory_node_id"], "has_profile_memory", metadata={"block": "B26"})
        return {**mem, "person_id": person_id, "profile": safe, "declared": bool(declared)}

    def attach_identity_evidence(self, person_id: str, *, modality: str, source: str, reference: str, descriptor: str = "", confidence: float = 0.5) -> dict:
        """Associa evidência referenciada; não autentica e não persiste biometria bruta."""
        modality, source, reference = _norm(modality), _clean(source), _clean(reference)
        if modality not in {"vision", "face", "voice", "audio", "context", "multimodal"}:
            raise ValueError("modalidade de identidade não suportada")
        if not source or not reference:
            raise ValueError("evidência de identidade exige fonte e referência")
        mem = self.memory.remember(
            "people", f"Evidência de identidade ({modality}): {_clean(descriptor) or reference}",
            source=source, reference=reference, entities=[person_id], importance=0.65, confidence=_clamp(confidence),
            metadata={
                "person_id": person_id, "identity_evidence": True, "modality": modality,
                "confidence": _clamp(confidence), "raw_biometric_stored": False,
                "authenticated": False, "grants_permission": False,
            },
        )
        self.graph.relate(person_id, mem["memory_node_id"], "has_identity_evidence", metadata={"block": "B26", "modality": modality})
        return {**mem, "person_id": person_id, "modality": modality, "authenticated": False, "grants_permission": False, "raw_biometric_stored": False}

    def ingest_profile(self, name: str, profile: dict, *, aliases: Iterable[str] = (), source: str, reference: str, identity_evidence: Iterable[dict] = ()) -> dict:
        person = self.upsert_declared_person(name, aliases=aliases, source=source, reference=reference, profile=profile)
        evidence_records = []
        for evidence in list(identity_evidence or ())[:16]:
            if isinstance(evidence, dict):
                evidence_records.append(self.attach_identity_evidence(
                    person["person_id"],
                    modality=evidence.get("modality") or "context",
                    source=evidence.get("source") or source,
                    reference=evidence.get("reference") or reference,
                    descriptor=evidence.get("descriptor") or evidence.get("content") or "",
                    confidence=evidence.get("confidence", 0.5),
                ))
        return {
            "person": person,
            "profile": self.person_context(person["person_id"], limit=16),
            "identity_evidence": evidence_records,
            "authenticated": False,
            "grants_permission": False,
        }

    def remember_interaction(self, person_id: str, content: str, *, source: str, reference: str = "", context: dict | None = None, importance: float = 0.6) -> dict:
        mem = self.memory.remember(
            "people", content, source=source, reference=reference, entities=[person_id], context=context,
            importance=importance, metadata={"person_id": person_id, "interaction": True},
        )
        self.graph.relate(person_id, mem["memory_node_id"], "has_interaction", metadata={"block": "B26"})
        return mem

    def set_relation(self, source_person_id: str, target_person_id: str, relation: str, *, confidence: float = 0.5, source: str) -> dict:
        relation = _clean(relation)
        if not relation:
            raise ValueError("relação vazia")
        self.graph.relate(
            source_person_id, target_person_id, "person_relation", weight=_clamp(confidence),
            metadata={"block": "B26", "relation": relation, "source": _clean(source), "permission": False},
        )
        return {"source": source_person_id, "target": target_person_id, "relation": relation, "confidence": _clamp(confidence), "permission": False}

    def recognition_hypothesis(self, candidates: Iterable[dict], *, signals: Iterable[dict] = ()) -> dict:
        ranked = sorted((deepcopy(x) for x in candidates if isinstance(x, dict)), key=lambda x: _clamp(x.get("confidence"), 0), reverse=True)[:8]
        return {
            "status": "hypothesis", "candidates": ranked, "signals": deepcopy(list(signals or ()))[:16],
            "authenticated": False, "grants_permission": False,
            "requires_authentication_for_privileged_actions": True,
        }

    def authenticate(self, person_id: str, *, verifier=None, challenge: Any = None) -> dict:
        if verifier is None:
            return {"person_id": person_id, "authenticated": False, "reason": "authentication_verifier_unavailable", "recognition_used_as_authentication": False}
        try:
            result = verifier.verify(person_id, challenge)
        except (AttributeError, RuntimeError, ValueError, OSError):
            return {"person_id": person_id, "authenticated": False, "reason": "authentication_failed_closed", "recognition_used_as_authentication": False}
        ok = bool(result.get("authenticated")) if isinstance(result, dict) else bool(result)
        return {"person_id": person_id, "authenticated": ok, "result": deepcopy(result), "recognition_used_as_authentication": False, "operational_permission": False}

    def person_context(self, person_id: str, *, limit: int = 16) -> dict:
        """Recupera contexto pelo grafo pessoa→memory_entry, não por busca textual."""
        bounded = min(max(int(limit), 1), 32)
        relations = self.graph.neighbors(person_id, limit=min(bounded * 4, 128))
        memories = []
        seen = set()
        for relation in relations:
            node_data = relation.get("node_data") or {}
            memory_id = node_data.get("memory_id")
            if memory_id is None or int(memory_id) in seen:
                continue
            record = self.memory.memory_record(int(memory_id))
            if record is None:
                continue
            metadata = record.get("metadata") or {}
            if metadata.get("person_id") != person_id and person_id not in metadata.get("entities", ()):
                continue
            seen.add(int(memory_id))
            memories.append(record)
            if len(memories) >= bounded:
                break
        memories.sort(key=lambda item: (float(item.get("importance", 0.0)), str(item.get("updated_at", ""))), reverse=True)
        return {"person_id": person_id, "memories": memories[:bounded], "relations": relations[:bounded], "bounded": True}

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated", "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "addressable_contents": ADDRESSABLE_CONTENTS, "shared_graph": True, "shared_memory": True,
            "recognition_is_authentication": False, "profile_ingestion": True,
            "identity_evidence_without_authentication": True, "raw_biometric_storage_by_default": False,
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if low in {"status bloco 26", "status pessoas", "status entidades pessoais"}:
            return f"👥 BLOCO 26 — PESSOAS: {ADDRESSABLE_CONTENTS} relações/conhecimentos endereçáveis | memória=B13 | reconhecimento ≠ autenticação."
        match = re.search(r"\bmeu nome (?:e|é)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]{0,40})", raw, re.I)
        if match:
            name = _clean(match.group(1)).split()[0]
            self.upsert_declared_person(name, source="user-self-declaration", reference=f"declared:{_norm(name)}")
            return None
        return None
