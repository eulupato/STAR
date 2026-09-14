"""BLOCO 2 — Fundação Epistêmica da STAR.

Centraliza como a STAR representa o que sabe, como sabe, de onde veio, quando
foi aprendido, quais evidências sustentam ou contestam uma afirmação, qual a
confiança, incerteza e validade temporal, e como revisões e contradições alteram
o estado do conhecimento.

A persistência usa exclusivamente o ``CognitiveStore``/``star.db`` oficial por
meio de ``EpistemicStore``. O catálogo de 1B é um espaço lógico materializado
sob demanda; não representa 1B de fatos pré-carregados nem 1B de linhas no banco.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from typing import Any

from core.cognitive_catalog import CONTEXTS, FAMILIES, LENSES, STYLES
from database.cognitive_store import CognitiveStore
from database.epistemic_store import EpistemicStore


EPISTEMIC_KINDS = (
    "fact",
    "hypothesis",
    "inference",
    "opinion",
    "fiction",
    "simulation",
    "unknown",
    "observation",
    "declared_information",
    "memory",
)

LIFECYCLE_STATES = (
    "DISCOVERED",
    "QUARANTINED",
    "VERIFIED",
    "CANONICAL",
    "SUPERSEDED",
    "RETRACTED",
)

STATE_TRANSITIONS = {
    "DISCOVERED": {"QUARANTINED", "VERIFIED", "RETRACTED"},
    "QUARANTINED": {"VERIFIED", "RETRACTED"},
    "VERIFIED": {"CANONICAL", "QUARANTINED", "SUPERSEDED", "RETRACTED"},
    "CANONICAL": {"QUARANTINED", "SUPERSEDED", "RETRACTED"},
    "SUPERSEDED": {"RETRACTED"},
    "RETRACTED": set(),
}

EVIDENCE_STANCES = ("support", "refute", "neutral")
EVIDENCE_TYPES = (
    "primary_source",
    "secondary_source",
    "observation",
    "measurement",
    "experiment",
    "replication",
    "review",
    "testimony",
    "derived_result",
    "unknown",
)

RELATION_TYPES = (
    "supports",
    "contradicts",
    "derived_from",
    "depends_on",
    "corroborates",
    "same_as",
    "refines",
    "supersedes",
    "superseded_by",
    "contextualizes",
)

TEMPORAL_STATES = (
    "current",
    "not_yet_valid",
    "expired",
    "stale",
    "undated",
)

SOURCE_RELIABILITY_BANDS = tuple(f"reliability_{i}" for i in range(10))
UNCERTAINTY_BANDS = tuple(f"uncertainty_{i}" for i in range(10))

EPISTEMIC_AREAS = (
    ("provenance", "proveniência e origem"),
    ("evidence", "evidências e suporte"),
    ("confidence", "confiança e calibração"),
    ("uncertainty", "incerteza e limites"),
    ("temporal_validity", "validade temporal e frescor"),
    ("source_reliability", "confiabilidade de fontes"),
    ("contradictions", "contradições e versões conflitantes"),
    ("revision", "revisão e histórico"),
    ("epistemic_status", "tipo e estado epistêmico"),
    ("lifecycle", "ciclo de vida do conhecimento"),
    ("discovery", "descoberta"),
    ("quarantine", "quarentena epistêmica"),
    ("verification", "verificação"),
    ("canonization", "canonização"),
    ("supersession", "substituição por conhecimento posterior"),
    ("retraction", "retração"),
    ("conflict_resolution", "resolução de conflitos"),
    ("traceability", "rastreabilidade ponta a ponta"),
    ("relationships", "relações entre conhecimentos"),
    ("audit", "auditoria epistêmica"),
)

EPISTEMIC_CANONICAL_NODES = len(EPISTEMIC_AREAS) * len(LENSES)
EPISTEMIC_VARIANTS_PER_NODE = (
    len(FAMILIES)
    * len(STYLES)
    * len(CONTEXTS)
    * len(EPISTEMIC_KINDS)
    * len(SOURCE_RELIABILITY_BANDS)
    * len(UNCERTAINTY_BANDS)
)
EPISTEMIC_ADDRESSABLE_CONTENTS = EPISTEMIC_CANONICAL_NODES * EPISTEMIC_VARIANTS_PER_NODE

if EPISTEMIC_CANONICAL_NODES != 1_000:
    raise RuntimeError("BLOCO 2 deve manter exatamente 1.000 nós canônicos")
if EPISTEMIC_VARIANTS_PER_NODE != 1_000_000:
    raise RuntimeError("BLOCO 2 deve manter exatamente 1.000.000 combinações por nó")
if EPISTEMIC_ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("BLOCO 2 deve manter exatamente 1B de representações endereçáveis")


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


def _clean(text: str) -> str:
    return " ".join(str(text or "").strip().split())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class EpistemicContentCatalog:
    """Espaço virtual de 1B de representações epistêmicas, sob demanda."""

    PREFIX = "EPI"

    def stats(self) -> dict:
        return {
            "areas": len(EPISTEMIC_AREAS),
            "lenses_per_area": len(LENSES),
            "canonical_nodes": EPISTEMIC_CANONICAL_NODES,
            "variants_per_node": EPISTEMIC_VARIANTS_PER_NODE,
            "addressable_contents": EPISTEMIC_ADDRESSABLE_CONTENTS,
            "materialization": "on-demand",
            "prepopulated_knowledge_rows": 0,
            "truthfulness_note": (
                "1B é espaço operacional para rastreabilidade epistêmica; "
                "não significa 1B de fatos independentes pesquisados"
            ),
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        node_index = int(node_index)
        variant_index = int(variant_index)
        if not 0 <= node_index < EPISTEMIC_CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= variant_index < EPISTEMIC_VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = node_index * EPISTEMIC_VARIANTS_PER_NODE + variant_index + 1
        return f"EPI-{absolute:010d}"

    @staticmethod
    def _indexes(identifier: str) -> tuple[int, int] | None:
        match = re.fullmatch(r"EPI-(\d{10})", str(identifier or "").upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= EPISTEMIC_ADDRESSABLE_CONTENTS:
            return None
        return divmod(absolute - 1, EPISTEMIC_VARIANTS_PER_NODE)

    def get_variant(self, identifier: str) -> dict | None:
        indexes = self._indexes(identifier)
        if indexes is None:
            return None
        node_index, variant_index = indexes
        area_index, lens_index = divmod(node_index, len(LENSES))
        area_key, area_label = EPISTEMIC_AREAS[area_index]
        lens_key, lens_label = LENSES[lens_index]

        remainder = variant_index
        dimensions = []
        for size in (10, 10, 10, 10, 10, 10):
            remainder, index = divmod(remainder, size)
            dimensions.append(index)
        uncertainty_i, reliability_i, kind_i, context_i, style_i, family_i = dimensions

        return {
            "id": identifier.upper(),
            "node_index": node_index,
            "variant_index": variant_index,
            "area": area_key,
            "area_label": area_label,
            "lens": lens_key,
            "lens_label": lens_label,
            "family": FAMILIES[family_i],
            "style": STYLES[style_i],
            "context": CONTEXTS[context_i],
            "epistemic_kind": EPISTEMIC_KINDS[kind_i],
            "source_reliability_band": SOURCE_RELIABILITY_BANDS[reliability_i],
            "uncertainty_band": UNCERTAINTY_BANDS[uncertainty_i],
            "prompt": (
                f"Aplicar {lens_label} a {area_label}, tratando o conteúdo como "
                f"{EPISTEMIC_KINDS[kind_i]}, com proveniência explícita, evidência "
                "auditável, confiança calibrada, incerteza preservada e validade temporal."
            ),
        }


class EpistemicFoundation:
    """Ledger e regras epistêmicas usando o mesmo armazenamento cognitivo oficial."""

    def __init__(self, store: CognitiveStore | EpistemicStore | None = None):
        self.store = store if isinstance(store, EpistemicStore) else EpistemicStore(store)
        self.catalog = EpistemicContentCatalog()

    @staticmethod
    def stable_record_id(content: str) -> str:
        normalized = _clean(content).casefold()
        if not normalized:
            raise ValueError("conteúdo epistêmico vazio")
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:20].upper()
        return f"KNOW-{digest}"

    def register_source(
        self,
        locator: str,
        *,
        source_type: str,
        title: str | None = None,
        reliability: float = 0.5,
        reliability_basis: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        locator = _clean(locator)
        source_type = _clean(source_type)
        if not locator or not source_type:
            raise ValueError("fonte exige locator e source_type")
        return self.store.upsert_epistemic_source(
            locator,
            source_type=source_type,
            title=title,
            reliability=_clamp(reliability),
            reliability_basis=reliability_basis,
            metadata=metadata,
        )

    def discover(
        self,
        content: str,
        *,
        epistemic_kind: str,
        origin_type: str,
        origin_ref: str,
        source_id: str | None = None,
        confidence: float = 0.5,
        uncertainty: float | None = None,
        learned_at: str | None = None,
        valid_from: str | None = None,
        valid_until: str | None = None,
        stale_after: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        content = _clean(content)
        if epistemic_kind not in EPISTEMIC_KINDS:
            raise ValueError(f"tipo epistêmico inválido: {epistemic_kind}")
        origin_type = _clean(origin_type)
        origin_ref = _clean(origin_ref)
        if not origin_type or not origin_ref:
            raise ValueError("todo conhecimento descoberto exige origem explícita")
        if source_id and self.store.get_epistemic_source(source_id) is None:
            raise ValueError("source_id não registrado")
        confidence = _clamp(confidence)
        uncertainty = _clamp(1.0 - confidence if uncertainty is None else uncertainty)
        return self.store.create_epistemic_record(
            self.stable_record_id(content),
            content,
            epistemic_kind=epistemic_kind,
            lifecycle_state="DISCOVERED",
            origin_type=origin_type,
            origin_ref=origin_ref,
            origin_source_id=source_id,
            confidence=confidence,
            uncertainty=uncertainty,
            learned_at=learned_at or _now(),
            valid_from=valid_from,
            valid_until=valid_until,
            stale_after=stale_after,
            metadata=metadata,
        )

    def add_evidence(
        self,
        record_id: str,
        description: str,
        *,
        evidence_type: str,
        stance: str = "support",
        source_id: str | None = None,
        strength: float = 0.5,
        reliability: float | None = None,
        observed_at: str | None = None,
        metadata: dict | None = None,
        recalculate: bool = True,
    ) -> dict:
        if evidence_type not in EVIDENCE_TYPES:
            raise ValueError(f"tipo de evidência inválido: {evidence_type}")
        if stance not in EVIDENCE_STANCES:
            raise ValueError(f"stance inválido: {stance}")
        record = self.store.get_epistemic_record(record_id)
        if record is None:
            raise KeyError(record_id)
        if reliability is None and source_id:
            source = self.store.get_epistemic_source(source_id)
            reliability = source["reliability"] if source else 0.5
        evidence = self.store.add_epistemic_evidence(
            record_id,
            description=_clean(description),
            evidence_type=evidence_type,
            stance=stance,
            source_id=source_id,
            strength=_clamp(strength),
            reliability=_clamp(0.5 if reliability is None else reliability),
            observed_at=observed_at or _now(),
            metadata=metadata,
        )
        if recalculate:
            self.recalculate_confidence(record_id)
        if stance == "refute" and record["lifecycle_state"] in {"VERIFIED", "CANONICAL"}:
            self.transition(
                record_id,
                "QUARANTINED",
                reason="nova evidência refutadora exige revisão",
                actor="epistemic-engine",
            )
        return evidence

    def recalculate_confidence(self, record_id: str) -> dict:
        record = self.store.get_epistemic_record(record_id)
        if record is None:
            raise KeyError(record_id)
        evidence = self.store.epistemic_evidence(record_id)
        support = refute = neutral = 0.0
        for item in evidence:
            weight = _clamp(item["strength"]) * _clamp(item["reliability"])
            if item["stance"] == "support":
                support += weight
            elif item["stance"] == "refute":
                refute += weight
            else:
                neutral += weight

        contested = support + refute
        if contested <= 0:
            confidence = _clamp(record["confidence"])
        else:
            balance = (support - refute) / contested
            coverage = min(1.0, contested / 2.0)
            confidence = _clamp(0.5 + 0.5 * balance * coverage)
        uncertainty = _clamp(1.0 - abs(confidence - 0.5) * 2.0)
        if neutral:
            uncertainty = _clamp(max(uncertainty, min(0.5, neutral / (neutral + contested + 1.0))))

        self.store.update_epistemic_record(
            record_id,
            {"confidence": confidence, "uncertainty": uncertainty},
            event_type="confidence_recalculated",
            reason="recalculated from weighted evidence",
            actor="epistemic-engine",
        )
        return {
            "record_id": record_id,
            "confidence": confidence,
            "uncertainty": uncertainty,
            "support_weight": support,
            "refute_weight": refute,
            "neutral_weight": neutral,
            "note": "confidence is a calibrated score, not proof of truth",
        }

    def relate(
        self,
        source_record_id: str,
        target_record_id: str,
        relation: str,
        *,
        weight: float = 1.0,
        metadata: dict | None = None,
    ) -> dict:
        if relation not in RELATION_TYPES:
            raise ValueError(f"relação epistêmica inválida: {relation}")
        if source_record_id == target_record_id:
            raise ValueError("um registro não pode ter relação epistêmica consigo mesmo")
        for record_id in (source_record_id, target_record_id):
            if self.store.get_epistemic_record(record_id) is None:
                raise KeyError(record_id)
        return self.store.add_epistemic_relation(
            source_record_id,
            target_record_id,
            relation,
            weight=_clamp(weight),
            metadata=metadata,
        )

    def contradict(
        self,
        first_record_id: str,
        second_record_id: str,
        *,
        reason: str,
        weight: float = 1.0,
    ) -> dict:
        relation = self.relate(
            first_record_id,
            second_record_id,
            "contradicts",
            weight=weight,
            metadata={"reason": _clean(reason), "resolution": "open"},
        )
        for record_id in (first_record_id, second_record_id):
            record = self.store.get_epistemic_record(record_id)
            if record and record["lifecycle_state"] in {"VERIFIED", "CANONICAL"}:
                self.transition(
                    record_id,
                    "QUARANTINED",
                    reason="contradição aberta detectada",
                    actor="epistemic-engine",
                )
        return relation

    def resolve_contradiction(
        self,
        first_record_id: str,
        second_record_id: str,
        *,
        resolution: str,
        actor: str = "system",
    ) -> dict:
        relation = self.relate(
            first_record_id,
            second_record_id,
            "contradicts",
            metadata={
                "resolution": "resolved",
                "resolution_note": _clean(resolution),
                "resolved_by": actor,
                "resolved_at": _now(),
            },
        )
        return relation

    def _open_contradictions(self, record_id: str) -> list[dict]:
        return [
            item
            for item in self.store.epistemic_relations(record_id)
            if item["relation"] == "contradicts"
            and item["metadata"].get("resolution", "open") != "resolved"
        ]

    def temporal_status(self, record_or_id: str | dict, *, as_of: str | None = None) -> dict:
        record = self.store.get_epistemic_record(record_or_id) if isinstance(record_or_id, str) else record_or_id
        if record is None:
            raise KeyError(record_or_id)
        moment = _parse_time(as_of) or datetime.now(timezone.utc)
        valid_from = _parse_time(record.get("valid_from"))
        valid_until = _parse_time(record.get("valid_until"))
        stale_after = _parse_time(record.get("stale_after"))

        if valid_from and moment < valid_from:
            state = "not_yet_valid"
        elif valid_until and moment > valid_until:
            state = "expired"
        elif stale_after and moment > stale_after:
            state = "stale"
        elif not any((valid_from, valid_until, stale_after)):
            state = "undated"
        else:
            state = "current"
        return {
            "state": state,
            "as_of": moment.isoformat(),
            "valid_from": record.get("valid_from"),
            "valid_until": record.get("valid_until"),
            "stale_after": record.get("stale_after"),
            "is_outdated": state in {"expired", "stale"},
        }

    def canonical_readiness(self, record_id: str) -> dict:
        record = self.store.get_epistemic_record(record_id)
        if record is None:
            raise KeyError(record_id)
        evidence = self.store.epistemic_evidence(record_id)
        temporal = self.temporal_status(record)
        reasons = []
        if record["lifecycle_state"] != "VERIFIED":
            reasons.append("estado atual precisa ser VERIFIED")
        if record["epistemic_kind"] != "fact":
            reasons.append("somente conhecimento classificado como fact pode ser CANONICAL")
        if not record.get("origin_ref"):
            reasons.append("proveniência ausente")
        if not evidence:
            reasons.append("nenhuma evidência registrada")
        if not any(item["stance"] == "support" for item in evidence):
            reasons.append("nenhuma evidência de suporte registrada")
        if float(record["confidence"]) < 0.70:
            reasons.append("confiança abaixo de 0.70")
        if float(record["uncertainty"]) > 0.60:
            reasons.append("incerteza acima de 0.60")
        if temporal["state"] in {"expired", "stale", "not_yet_valid"}:
            reasons.append(f"validade temporal incompatível: {temporal['state']}")
        if self._open_contradictions(record_id):
            reasons.append("contradição aberta")
        return {"record_id": record_id, "ready": not reasons, "reasons": reasons}

    def transition(
        self,
        record_id: str,
        new_state: str,
        *,
        reason: str,
        actor: str = "system",
    ) -> dict:
        record = self.store.get_epistemic_record(record_id)
        if record is None:
            raise KeyError(record_id)
        old_state = record["lifecycle_state"]
        new_state = str(new_state or "").upper()
        if new_state not in LIFECYCLE_STATES:
            raise ValueError(f"estado epistêmico inválido: {new_state}")
        if new_state == old_state:
            return record
        if new_state not in STATE_TRANSITIONS[old_state]:
            raise ValueError(f"transição epistêmica inválida: {old_state} -> {new_state}")
        if new_state == "VERIFIED":
            if not self.store.epistemic_evidence(record_id):
                raise ValueError("VERIFIED exige ao menos uma evidência rastreável")
            if self._open_contradictions(record_id):
                raise ValueError("VERIFIED bloqueado enquanto houver contradição aberta")
        if new_state == "CANONICAL":
            readiness = self.canonical_readiness(record_id)
            if not readiness["ready"]:
                raise ValueError("CANONICAL bloqueado: " + "; ".join(readiness["reasons"]))
        changes: dict[str, Any] = {"lifecycle_state": new_state}
        if new_state in {"VERIFIED", "CANONICAL"}:
            changes["last_verified_at"] = _now()
        return self.store.update_epistemic_record(
            record_id,
            changes,
            event_type="state_transition",
            reason=_clean(reason),
            actor=actor,
        )

    def revise(self, record_id: str, changes: dict, *, reason: str, actor: str = "system") -> dict:
        allowed = {
            "epistemic_kind",
            "origin_type",
            "origin_ref",
            "origin_source_id",
            "confidence",
            "uncertainty",
            "valid_from",
            "valid_until",
            "stale_after",
            "last_verified_at",
            "metadata_json",
        }
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError("campos de revisão inválidos: " + ", ".join(sorted(unknown)))
        record = self.store.get_epistemic_record(record_id)
        if record is None:
            raise KeyError(record_id)
        normalized = dict(changes)
        if "epistemic_kind" in normalized and normalized["epistemic_kind"] not in EPISTEMIC_KINDS:
            raise ValueError("tipo epistêmico inválido")
        for field in ("confidence", "uncertainty"):
            if field in normalized:
                normalized[field] = _clamp(normalized[field])
        material_fields = {
            "epistemic_kind",
            "origin_type",
            "origin_ref",
            "origin_source_id",
            "confidence",
            "uncertainty",
            "valid_from",
            "valid_until",
            "stale_after",
        }
        if record["lifecycle_state"] == "CANONICAL" and material_fields.intersection(normalized):
            self.transition(
                record_id,
                "QUARANTINED",
                reason="revisão material de conhecimento canônico",
                actor=actor,
            )
        return self.store.update_epistemic_record(
            record_id,
            normalized,
            event_type="revision",
            reason=_clean(reason),
            actor=actor,
        )

    def supersede(self, old_record_id: str, new_record_id: str, *, reason: str, actor: str = "system") -> dict:
        self.relate(old_record_id, new_record_id, "superseded_by", metadata={"reason": _clean(reason)})
        self.relate(new_record_id, old_record_id, "supersedes", metadata={"reason": _clean(reason)})
        return self.transition(old_record_id, "SUPERSEDED", reason=reason, actor=actor)

    def retract(self, record_id: str, *, reason: str, actor: str = "system") -> dict:
        return self.transition(record_id, "RETRACTED", reason=reason, actor=actor)

    def trace(self, record_id: str) -> dict:
        record = self.store.get_epistemic_record(record_id)
        if record is None:
            raise KeyError(record_id)
        source = self.store.get_epistemic_source(record.get("origin_source_id")) if record.get("origin_source_id") else None
        evidence = self.store.epistemic_evidence(record_id)
        relations = self.store.epistemic_relations(record_id)
        revisions = self.store.epistemic_revisions(record_id)
        temporal = self.temporal_status(record)
        contradictions = [item for item in relations if item["relation"] == "contradicts"]
        could_be_wrong = (
            record["epistemic_kind"] != "fact"
            or float(record["confidence"]) < 0.99
            or float(record["uncertainty"]) > 0.01
            or bool(self._open_contradictions(record_id))
            or record["lifecycle_state"] not in {"VERIFIED", "CANONICAL"}
            or temporal["is_outdated"]
        )
        return {
            "record": record,
            "origin_source": source,
            "evidence": evidence,
            "relations": relations,
            "contradictions": contradictions,
            "revisions": revisions,
            "temporal_validity": temporal,
            "could_be_wrong": could_be_wrong,
            "epistemic_summary": {
                "what_is_known": record["content"],
                "how_known": record["origin_type"],
                "where_from": record["origin_ref"],
                "when_learned": record["learned_at"],
                "status": record["lifecycle_state"],
                "kind": record["epistemic_kind"],
                "confidence": record["confidence"],
                "uncertainty": record["uncertainty"],
            },
        }

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "lifecycle_states": list(LIFECYCLE_STATES),
            "epistemic_kinds": list(EPISTEMIC_KINDS),
            "catalog": self.catalog.stats(),
            "persisted": self.store.epistemic_stats(),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if low in {"status bloco 2", "status epistemico", "status epistêmico", "fundacao epistemica", "fundação epistêmica"}:
            stats = self.stats()
            return (
                "🔎 BLOCO 2 — FUNDAÇÃO EPISTÊMICA: "
                f"{stats['catalog']['addressable_contents']} representações endereçáveis | "
                f"{len(LIFECYCLE_STATES)} estados de ciclo | "
                f"{stats['persisted']['records']} conhecimentos persistidos | "
                "proveniência, evidência, confiança, incerteza, temporalidade, contradições e revisão ativas."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"🔎 {item['id']} — {item['area_label']} / {item['lens_label']}\n{item['prompt']}"
        match = re.fullmatch(
            r"(?:rastreie|rastrear|trace|epistemic status|status epistemico de|status epistêmico de)\s+(KNOW-[A-F0-9]{20})",
            raw,
            re.I,
        )
        if match:
            try:
                trace = self.trace(match.group(1).upper())
            except KeyError:
                return "Registro epistêmico não encontrado."
            summary = trace["epistemic_summary"]
            temporal = trace["temporal_validity"]["state"]
            return (
                f"🔎 {trace['record']['record_id']} | {summary['kind']} | {summary['status']} | "
                f"confiança={summary['confidence']:.3f} | incerteza={summary['uncertainty']:.3f} | "
                f"temporal={temporal} | evidências={len(trace['evidence'])} | "
                f"contradições={len(trace['contradictions'])}."
            )
        return None
