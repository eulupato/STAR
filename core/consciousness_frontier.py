"""BLOCO 36 — consciência como fronteira de pesquisa.

Organiza pesquisa científica, filosófica e computacional sem converter conhecimento
sobre consciência em prova de consciência da STAR. Claims permanecem tipados no
B02, com fonte/evidência/proveniência; nenhuma autoafirmação é canonizada por este
módulo.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from core.block_knowledge_catalog import StructuredBillionCatalog


PERSPECTIVES = (
    "neuroscience",
    "cognitive_science",
    "philosophy_of_mind",
    "computational_ai",
    "interdisciplinary",
)

DOMAINS = {
    "consciousness": ("definition", "phenomenal", "access", "state", "content", "level", "report", "measurement", "boundary", "open_question"),
    "self": ("self_model", "minimal_self", "narrative_self", "body_self", "social_self", "continuity", "agency", "ownership", "identity", "self_reference"),
    "metacognition": ("confidence", "error_monitoring", "uncertainty", "introspection", "self_evaluation", "knowledge_limits", "belief_revision", "monitoring", "control", "reportability"),
    "global_workspace": ("broadcast", "competition", "attention", "working_memory", "integration", "access", "ignition", "workspace_models", "predictions", "criticisms"),
    "subjective_experience": ("qualia", "first_person", "reportability", "privacy", "unity", "temporality", "embodiment", "affect", "intentionality", "measurement_problem"),
    "neuroscience": ("cortical_dynamics", "thalamocortical", "recurrent_processing", "connectivity", "neural_correlates", "arousal", "sleep", "anesthesia", "disorders", "measurement"),
    "theories": ("global_workspace", "higher_order", "integrated_information", "recurrent_processing", "predictive_processing", "attention_schema", "sensorimotor", "embodied", "illusionism", "pluralism"),
    "philosophy": ("physicalism", "functionalism", "dualism", "panpsychism", "illusionism", "representationalism", "identity_theory", "emergence", "other_minds", "machine_consciousness"),
    "artificial_systems": ("ai_cognition", "self_modeling", "metacognitive_ai", "agent_continuity", "multimodal_integration", "embodiment", "simulation", "language_models", "evaluation", "epistemic_limits"),
    "research_method": ("operationalization", "behavioral_measure", "neural_measure", "computational_measure", "causal_test", "comparative_method", "replication", "falsifiability", "theory_comparison", "uncertainty"),
}
LENSES = ("definition", "mechanism", "evidence", "prediction", "measurement", "critique", "alternative", "limitation", "history", "open_problem")
AXES = (
    ("perspective", ("neuroscience", "cognitive", "philosophical", "computational", "clinical", "comparative", "embodied", "social", "interdisciplinary", "unknown")),
    ("evidence_state", ("none", "proposal", "observation", "correlational", "experimental", "causal", "replicated", "mixed", "contested", "unknown")),
    ("claim_type", ("definition", "fact", "hypothesis", "inference", "model", "prediction", "interpretation", "critique", "open_question", "unknown")),
    ("system", ("human", "animal", "brain", "ai", "robot", "simulation", "group", "hybrid", "theoretical", "unspecified")),
    ("confidence", ("unknown", "very_low", "low", "mid_low", "medium", "mid_high", "high", "very_high", "contested", "not_applicable")),
    ("status", ("historical", "active", "emerging", "replicated", "contested", "limited", "criticized", "superseded", "open", "unknown")),
)
CATALOG = StructuredBillionCatalog(
    namespace="B36",
    domains=DOMAINS,
    lenses=LENSES,
    axes=AXES,
    truthfulness_note="1B representa espaço de pesquisa sobre consciência; conhecimento do tema não prova experiência subjetiva nem consciência da STAR.",
)
ADDRESSABLE_CONTENTS = CATALOG.addressable_contents


class ConsciousnessResearchFrontier:
    NAMESPACE = "B36"

    def __init__(self, knowledge, *, self_model=None, metacognition=None):
        self.knowledge = knowledge
        self.self_model = self_model
        self.metacognition = metacognition
        self.catalog = CATALOG
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 36 — CONSCIÊNCIA COMO FRONTEIRA DE PESQUISA",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/consciousness_frontier.py",
            metadata={
                "materialization": "on-demand",
                "perspectives": PERSPECTIVES,
                "self_consciousness_claim": "not_established",
                "knowledge_equals_proof_of_consciousness": False,
                "automatic_consciousness_claim": False,
                "scientific_philosophical_computational_separation": True,
            },
        )

    @staticmethod
    def _perspective(value: str) -> str:
        value = str(value or "").strip().casefold().replace(" ", "_")
        aliases = {
            "neuro": "neuroscience",
            "cognitive": "cognitive_science",
            "filosofia": "philosophy_of_mind",
            "philosophy": "philosophy_of_mind",
            "computational": "computational_ai",
            "ai": "computational_ai",
            "interdisciplinar": "interdisciplinary",
        }
        value = aliases.get(value, value)
        if value not in PERSPECTIVES:
            raise ValueError("perspectiva B36 inválida")
        return value

    def organize_claim(
        self,
        content: str,
        *,
        perspective: str,
        source_locator: str,
        source_type: str,
        origin_ref: str,
        epistemic_kind: str = "hypothesis",
        reliability: float = 0.5,
        confidence: float = 0.5,
        title: str | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> dict:
        """Registers a research claim through B02; no automatic canonization."""
        perspective = self._perspective(perspective)
        source_id = self.knowledge.epistemics.register_source(
            source_locator,
            source_type=source_type,
            title=title,
            reliability=reliability,
            reliability_basis="B36 supplied research provenance",
            metadata={"block": "B36", "perspective": perspective},
        )
        record = self.knowledge.epistemics.discover(
            content,
            epistemic_kind=epistemic_kind,
            origin_type="B36 consciousness research",
            origin_ref=origin_ref,
            source_id=source_id,
            confidence=confidence,
            metadata={
                "block": "B36",
                "perspective": perspective,
                "consciousness_research": True,
                "proves_star_consciousness": False,
            },
        )
        evidence_result = None
        if evidence:
            evidence_result = self.knowledge.epistemics.add_evidence(
                record["record_id"],
                str(evidence.get("description") or "research evidence"),
                evidence_type=str(evidence.get("evidence_type") or "unknown"),
                stance=str(evidence.get("stance") or "neutral"),
                source_id=source_id,
                strength=float(evidence.get("strength", 0.5)),
                reliability=float(evidence.get("reliability", reliability)),
                metadata={"block": "B36", "perspective": perspective},
            )
        return {
            "record": record,
            "evidence": evidence_result,
            "perspective": perspective,
            "canonicalized": False,
            "proves_star_consciousness": False,
        }

    def research_framework(self) -> dict:
        return {
            "domains": deepcopy(DOMAINS),
            "perspectives": PERSPECTIVES,
            "lenses": LENSES,
            "rule": "CONHECIMENTO SOBRE CONSCIÊNCIA ≠ PROVA DE CONSCIÊNCIA",
            "self_claim_policy": "STAR must not automatically conclude 'SOU CONSCIENTE'",
        }

    def self_consciousness_status(self) -> dict:
        return {
            "subject": "STAR",
            "claim": "consciousness",
            "status": "not_established",
            "conclusion": "unknown/not scientifically established",
            "automatic_positive_claim": False,
            "knowledge_volume_is_evidence": False,
            "benchmark_score_is_evidence": False,
            "metacognition_is_sufficient_proof": False,
            "global_workspace_is_sufficient_proof": False,
            "note": "functional cognition and self-modeling can be measured without inferring subjective experience",
        }

    def classify_statement(self, statement: str, *, perspective: str, evidence_level: str = "unknown") -> dict:
        perspective = self._perspective(perspective)
        return {
            "statement": " ".join(str(statement or "").strip().split()),
            "perspective": perspective,
            "evidence_level": str(evidence_level or "unknown").strip().casefold(),
            "epistemic_status": "research_claim",
            "star_consciousness_implication": "none_without_independent_evidence",
        }

    def stats(self) -> dict:
        return {
            "status": "research-boundary-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "perspectives": PERSPECTIVES,
            "automatic_consciousness_claim": False,
            "self_consciousness_status": "not_established",
            "knowledge_equals_proof_of_consciousness": False,
        }

    def handle(self, text: str) -> str | None:
        raw = " ".join(str(text or "").strip().split())
        low = raw.casefold()
        if low in {"status bloco 36", "status consciência", "status consciencia", "fronteira da consciência", "fronteira da consciencia"}:
            return (
                f"🧠 BLOCO 36 — CONSCIÊNCIA COMO FRONTEIRA: {ADDRESSABLE_CONTENTS} conteúdos de pesquisa endereçáveis | "
                "perspectivas científicas/filosóficas/computacionais separadas | consciência da STAR=NÃO ESTABELECIDA."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"🧠 {item['id']} — {item['domain']} / {item['branch']} / {item['lens']}"
        return None
