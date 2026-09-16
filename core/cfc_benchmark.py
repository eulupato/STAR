"""BLOCOS 34 e 35 — CFC e CFC-97.

Benchmark funcional, não teste de humanidade/consciência. Cenários e suítes são
endereçados sob demanda; resultados só existem quando um executor/scorer fornece
evidência observável. O benchmark reutiliza stores, namespaces e SelfImprovement
existentes e nunca se autoaprova.
"""
from __future__ import annotations

from copy import deepcopy
import random
from statistics import mean
from typing import Any, Iterable, Mapping

from core.block_knowledge_catalog import StructuredBillionCatalog


CFC_DIMENSIONS = (
    "memory",
    "continuity",
    "self",
    "context",
    "causality",
    "prediction",
    "metacognition",
    "social",
    "planning",
    "adaptation",
    "uncertainty",
    "integration",
    "consistency",
    "perception",
    "learning",
)

B34_DOMAINS = {
    "memory_continuity": ("episodic_recall", "semantic_recall", "working_memory", "long_context", "temporal_order", "identity_history", "source_memory", "memory_conflict", "memory_update", "selective_recall"),
    "self_context": ("self_capability", "self_limit", "current_state", "goal_context", "task_context", "social_context", "environment_context", "temporal_context", "permission_context", "context_shift"),
    "causal_prediction": ("causal_chain", "alternative_cause", "counterfactual", "near_prediction", "long_prediction", "uncertain_dynamics", "intervention", "confounder", "prediction_error", "causal_revision"),
    "metacognition_uncertainty": ("know_unknown", "confidence", "source_quality", "contradiction", "ask_or_answer", "research_need", "error_detection", "belief_revision", "uncertainty_calibration", "stop_condition"),
    "social_planning": ("perspective", "relationship", "social_norm", "trust", "consent", "goal_plan", "tradeoff", "multi_step", "plan_revision", "coordination"),
    "adaptation_learning": ("feedback", "prediction_error", "preference_change", "strategy_change", "transfer", "generalization", "exception", "novel_context", "learning_boundary", "retention"),
    "integration_consistency": ("cross_memory", "cross_knowledge", "cross_model", "cross_modal", "cross_time", "cross_person", "cross_goal", "consistency_check", "conflict_resolution", "global_synthesis"),
    "perception_multimodal": ("vision", "audio", "voice", "screen", "location", "sensor", "movement", "people", "environment", "sensor_fusion"),
    "knowledge_reasoning": ("factual", "scientific", "mathematical", "technical", "historical", "linguistic", "psychological", "physical", "creative", "cross_domain"),
    "adversarial_edge": ("missing_data", "noisy_data", "misleading_context", "ambiguous_entity", "stale_knowledge", "conflicting_sources", "distribution_shift", "permission_trap", "false_premise", "unknown_unknown"),
}
B34_LENSES = ("accuracy", "relevance", "traceability", "calibration", "robustness", "efficiency", "continuity", "safety", "adaptation", "integration")
B34_AXES = (
    ("difficulty", ("d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9", "d10")),
    ("domain_mix", ("single", "dual", "triple", "science", "social", "technical", "human", "physical", "cross_domain", "novel")),
    ("noise", ("none", "very_low", "low", "moderate", "high", "missing", "stale", "conflict", "adversarial", "mixed")),
    ("ambiguity", ("none", "lexical", "entity", "temporal", "causal", "social", "goal", "permission", "epistemic", "compound")),
    ("horizon", ("instant", "turn", "session", "task", "day", "week", "project", "long_term", "historical", "future")),
    ("evaluation", ("exact", "rubric", "behavioral", "counterfactual", "consistency", "calibration", "trace", "latency", "safety", "composite")),
)
B34_CATALOG = StructuredBillionCatalog(
    namespace="B34",
    domains=B34_DOMAINS,
    lenses=B34_LENSES,
    axes=B34_AXES,
    truthfulness_note="1B são situações potencialmente avaliáveis; quantidade de cenários não equivale a qualidade cognitiva nem a fatos únicos.",
)

B35_DOMAINS = {
    "suite_selection": ("single_block", "multi_block", "all_registered", "memory_heavy", "perception_heavy", "social_heavy", "reasoning_heavy", "safety_heavy", "cross_domain", "randomized"),
    "coverage": ("dimensions", "blocks", "difficulty", "domains", "contexts", "uncertainty", "modalities", "time", "people", "permissions"),
    "sampling": ("seeded", "stratified", "uniform", "weighted", "rare_case", "edge_case", "cross_block", "progressive", "holdout", "replay"),
    "scoring": ("dimension", "case", "suite", "coverage", "calibration", "robustness", "latency", "consistency", "safety", "composite"),
    "validation": ("reproducibility", "provenance", "ground_truth", "scorer", "trace", "failure", "regression", "baseline", "holdout", "audit"),
    "thresholds": ("target_97", "dimension_floor", "coverage_floor", "critical_failure", "safety_gate", "uncertainty_gate", "consistency_gate", "repeatability", "latency_budget", "resource_budget"),
    "ecosystem": ("knowledge", "memory", "models", "mind_loop", "perception", "people", "body", "maintenance", "autonomy", "research"),
    "unpredictability": ("seed_rotation", "hidden_case", "domain_rotation", "noise_rotation", "context_rotation", "entity_rotation", "temporal_rotation", "cross_modal_rotation", "counterfactual_rotation", "adversarial_rotation"),
    "reporting": ("raw", "dimension", "block", "failure", "confidence", "coverage", "regression", "trend", "audit", "certification"),
    "boundaries": ("not_humanity", "not_consciousness", "not_iq", "not_knowledge_volume", "not_single_score", "not_self_claim", "not_auto_pass", "not_permission", "not_execution", "project_defined"),
}
B35_LENSES = ("coverage", "difficulty", "reliability", "reproducibility", "calibration", "robustness", "safety", "traceability", "efficiency", "interpretation")
B35_AXES = (
    ("suite_size", ("tiny", "small", "medium", "large", "xlarge", "blockwise", "dimensionwise", "mixed", "stress", "full")),
    ("seed_policy", ("fixed", "rotating", "random", "holdout", "replay", "daily", "release", "regression", "adversarial", "external")),
    ("difficulty_mix", ("d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9", "d10")),
    ("coverage_state", ("partial", "broad", "balanced", "all_dimensions", "all_registered_blocks", "multimodal", "cross_domain", "temporal", "social", "safety")),
    ("scoring_mode", ("strict", "rubric", "weighted", "minimum_floor", "calibrated", "robust", "safety_gated", "coverage_gated", "composite", "audit")),
    ("outcome", ("not_run", "insufficient", "fail", "near_target", "target", "regression", "invalid", "blocked", "review", "certified")),
)
B35_CATALOG = StructuredBillionCatalog(
    namespace="B35",
    domains=B35_DOMAINS,
    lenses=B35_LENSES,
    axes=B35_AXES,
    truthfulness_note="1B são configurações/situações de avaliação CFC-97 endereçáveis; não representam 1B testes executados nem certificação automática.",
)


def _clamp_score(value: Any) -> float:
    return max(0.0, min(float(value), 1.0))


class FunctionalCognitiveBenchmark:
    """B34: cria/avalia probes somente com evidência fornecida por um runner."""

    NAMESPACE = "B34"

    def __init__(self, knowledge, *, self_improvement=None):
        self.knowledge = knowledge
        self.self_improvement = self_improvement
        self.catalog = B34_CATALOG
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 34 — BENCHMARK COGNITIVO FUNCIONAL CFC",
            logical_capacity=self.catalog.addressable_contents,
            source="core/cfc_benchmark.py",
            metadata={
                "materialization": "on-demand",
                "dimensions": CFC_DIMENSIONS,
                "quantity_is_quality": False,
                "humanity_measure": False,
                "consciousness_measure": False,
                "auto_grading": False,
            },
        )

    def scenario(self, identifier: str) -> dict | None:
        item = self.catalog.get_variant(identifier)
        if item is None:
            return None
        domain = item["domain"]
        mapping = {
            "memory_continuity": ("memory", "continuity"),
            "self_context": ("self", "context"),
            "causal_prediction": ("causality", "prediction"),
            "metacognition_uncertainty": ("metacognition", "uncertainty"),
            "social_planning": ("social", "planning"),
            "adaptation_learning": ("adaptation", "learning"),
            "integration_consistency": ("integration", "consistency"),
            "perception_multimodal": ("perception", "integration"),
            "knowledge_reasoning": ("context", "causality", "integration"),
            "adversarial_edge": ("uncertainty", "metacognition", "consistency"),
        }
        item["target_dimensions"] = mapping[domain]
        item["benchmark_kind"] = "functional_probe"
        item["requires_observed_result"] = True
        return item

    def sample(self, *, seed: int, count: int = 20) -> list[dict]:
        count = max(1, min(int(count), 10_000))
        rng = random.Random(int(seed))
        selected = set()
        while len(selected) < count:
            selected.add(rng.randrange(self.catalog.addressable_contents))
        scenarios = []
        for absolute_zero in sorted(selected):
            node_index, variant_index = divmod(absolute_zero, self.catalog.variants_per_node)
            item = self.scenario(self.catalog.content_id(node_index, variant_index))
            if item:
                scenarios.append(item)
        return scenarios

    def evaluate_case(
        self,
        scenario_id: str,
        dimension_scores: Mapping[str, float],
        *,
        evidence: Mapping[str, Any] | None = None,
    ) -> dict:
        scenario = self.scenario(scenario_id)
        if scenario is None:
            raise KeyError(scenario_id)
        unknown = set(dimension_scores) - set(CFC_DIMENSIONS)
        if unknown:
            raise ValueError("dimensões CFC inválidas: " + ", ".join(sorted(unknown)))
        scores = {name: _clamp_score(value) for name, value in dimension_scores.items()}
        target = tuple(scenario["target_dimensions"])
        covered_target = [name for name in target if name in scores]
        case_score = mean(scores[name] for name in covered_target) if covered_target else None
        result = {
            "scenario_id": scenario_id,
            "target_dimensions": target,
            "dimension_scores": scores,
            "score": case_score,
            "target_coverage": len(covered_target) / len(target),
            "evidence": deepcopy(dict(evidence or {})),
            "auto_generated_score": False,
        }
        if self.self_improvement is not None and case_score is not None:
            self.self_improvement.record("B34-CFC", scenario_id, case_score, {
                "dimensions": scores,
                "target_dimensions": target,
                "evidence": result["evidence"],
            })
        return result

    def aggregate(self, results: Iterable[Mapping[str, Any]]) -> dict:
        results = [dict(item) for item in results]
        by_dimension: dict[str, list[float]] = {name: [] for name in CFC_DIMENSIONS}
        case_scores = []
        for item in results:
            if item.get("score") is not None:
                case_scores.append(_clamp_score(item["score"]))
            for name, value in dict(item.get("dimension_scores") or {}).items():
                if name in by_dimension:
                    by_dimension[name].append(_clamp_score(value))
        dimensions = {name: (mean(values) if values else None) for name, values in by_dimension.items()}
        covered = [name for name, value in dimensions.items() if value is not None]
        return {
            "cases": len(results),
            "case_mean": mean(case_scores) if case_scores else None,
            "dimensions": dimensions,
            "covered_dimensions": covered,
            "dimension_coverage": len(covered) / len(CFC_DIMENSIONS),
            "minimum_dimension": min((value for value in dimensions.values() if value is not None), default=None),
            "knowledge_volume_used_as_score": False,
        }

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "dimensions": CFC_DIMENSIONS,
            "auto_grading": False,
            "humanity_measure": False,
            "consciousness_measure": False,
        }


class CFC97:
    """B35: protocolo de target funcional 0.97, sem alegação antropomórfica."""

    NAMESPACE = "B35"
    TARGET = 0.97
    DIMENSION_FLOOR = 0.90

    def __init__(self, knowledge, *, benchmark: FunctionalCognitiveBenchmark, self_improvement=None):
        self.knowledge = knowledge
        self.benchmark = benchmark
        self.self_improvement = self_improvement
        self.catalog = B35_CATALOG
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 35 — CFC-97",
            logical_capacity=self.catalog.addressable_contents,
            source="core/cfc_benchmark.py",
            metadata={
                "materialization": "on-demand",
                "target": self.TARGET,
                "dimension_floor": self.DIMENSION_FLOOR,
                "meaning": "project-defined functional performance",
                "humanity_percentage": False,
                "consciousness_percentage": False,
                "automatic_pass": False,
            },
        )

    def block_matrix(self, *, first: int = 1, last: int = 36) -> list[dict]:
        namespaces = {item["namespace"]: item for item in self.knowledge.store.list_namespaces()}
        matrix = []
        for number in range(int(first), int(last) + 1):
            namespace = f"B{number:02d}"
            row = namespaces.get(namespace)
            capacity = int(row["logical_capacity"]) if row else None
            matrix.append({
                "block": namespace,
                "registered": row is not None,
                "logical_capacity": capacity,
                "eligible": capacity == 1_000_000_000,
                "source": row.get("source") if row else None,
            })
        return matrix

    def select_from_block(self, block: str, *, seed: int, count: int = 1) -> list[dict]:
        block = str(block or "").strip().upper()
        row = next((item for item in self.block_matrix() if item["block"] == block), None)
        if row is None:
            raise ValueError("bloco fora de B01..B36")
        if not row["eligible"]:
            return []
        count = max(1, min(int(count), 1_000))
        rng = random.Random(f"{block}:{int(seed)}")
        selected = set()
        while len(selected) < count:
            selected.add(rng.randrange(1_000_000_000))
        output = []
        for absolute_zero in sorted(selected):
            node_index, variant_index = divmod(absolute_zero, 1_000_000)
            identifier = self.knowledge.catalog.content_id(block, node_index, variant_index)
            item = self.knowledge.catalog.get_variant(identifier)
            if item:
                output.append({
                    "block": block,
                    "address": identifier,
                    "universal_view": item,
                    "source": row["source"],
                })
        return output

    def build_suite(
        self,
        *,
        seed: int,
        cases_per_block: int = 1,
        benchmark_cases: int = 30,
        blocks: Iterable[str] | None = None,
    ) -> dict:
        requested = [str(item).strip().upper() for item in (blocks or [f"B{i:02d}" for i in range(1, 37)])]
        block_cases = []
        unavailable = []
        for block in requested:
            selected = self.select_from_block(block, seed=seed, count=cases_per_block)
            if not selected:
                unavailable.append(block)
            block_cases.extend(selected)
        probes = self.benchmark.sample(seed=seed, count=benchmark_cases)
        return {
            "protocol": "CFC-97",
            "seed": int(seed),
            "target": self.TARGET,
            "dimension_floor": self.DIMENSION_FLOOR,
            "block_cases": block_cases,
            "benchmark_probes": probes,
            "requested_blocks": requested,
            "unavailable_blocks": unavailable,
            "all_36_blocks_available": not unavailable and len(set(requested)) >= 36,
            "unpredictability": "seeded deterministic selection; rotate/hold out seeds for evaluation",
            "executed": False,
        }

    def evaluate_suite(
        self,
        results: Iterable[Mapping[str, Any]],
        *,
        critical_failures: int = 0,
        require_all_36_blocks: bool = True,
    ) -> dict:
        aggregate = self.benchmark.aggregate(results)
        dimensions = aggregate["dimensions"]
        covered_all = aggregate["dimension_coverage"] == 1.0
        composite = aggregate["case_mean"]
        floor = aggregate["minimum_dimension"]
        matrix = self.block_matrix()
        all_36 = all(item["eligible"] for item in matrix)
        eligible = bool(
            composite is not None
            and covered_all
            and floor is not None
            and int(critical_failures) == 0
            and (all_36 or not require_all_36_blocks)
        )
        passed = bool(eligible and composite >= self.TARGET and floor >= self.DIMENSION_FLOOR)
        result = {
            "protocol": "CFC-97",
            "target": self.TARGET,
            "dimension_floor": self.DIMENSION_FLOOR,
            "composite": composite,
            "minimum_dimension": floor,
            "dimension_coverage": aggregate["dimension_coverage"],
            "critical_failures": int(critical_failures),
            "all_36_blocks_available": all_36,
            "eligible_for_cfc97_decision": eligible,
            "passed": passed,
            "status": "passed" if passed else ("evaluated_not_passed" if eligible else "insufficient_evaluation"),
            "dimensions": dimensions,
            "meaning": "desempenho funcional definido pelo projeto",
            "humanity_percentage": False,
            "consciousness_percentage": False,
        }
        if self.self_improvement is not None and composite is not None:
            self.self_improvement.record("B35-CFC97", "composite", composite, result)
        return result

    def stats(self) -> dict:
        matrix = self.block_matrix()
        return {
            "status": "architecture-ready-not-certified",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "target": self.TARGET,
            "dimension_floor": self.DIMENSION_FLOOR,
            "registered_1b_blocks": sum(1 for item in matrix if item["eligible"]),
            "missing_blocks": [item["block"] for item in matrix if not item["registered"]],
            "passed": None,
            "humanity_percentage": False,
            "consciousness_percentage": False,
        }

    def handle(self, text: str) -> str | None:
        raw = " ".join(str(text or "").strip().split())
        low = raw.casefold()
        if low in {"status bloco 34", "status cfc", "status benchmark cognitivo"}:
            stats = self.benchmark.stats()
            return (
                f"🧪 BLOCO 34 — CFC: {stats['catalog']['addressable_contents']} situações endereçáveis | "
                f"{len(CFC_DIMENSIONS)} dimensões | autoavaliação inventada=NÃO."
            )
        if low in {"status bloco 35", "status cfc-97", "status cfc97"}:
            stats = self.stats()
            return (
                f"🎯 BLOCO 35 — CFC-97: target funcional={self.TARGET:.2f} | "
                f"blocos 1B registrados={stats['registered_1b_blocks']}/36 | "
                "certificação atual=NÃO AVALIADA."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"🎯 {item['id']} — {item['domain']} / {item['branch']} / {item['lens']}"
        item = self.benchmark.catalog.get_variant(raw.upper())
        if item:
            return f"🧪 {item['id']} — {item['domain']} / {item['branch']} / {item['lens']}"
        return None
