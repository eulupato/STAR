"""STAR Curriculum Knowledge: expansão granular, deduplicada e on-demand.

Cada um dos 56 temas recebe 1.000.000 de variações de síntese. Cada conceito
/subtema único recebe 1.000.000 de variações próprias. Repetições no texto
não criam cópias: um conceito canônico mantém múltiplos vínculos temáticos.

As variações são perspectivas determinísticas de estudo/pesquisa; não são
1M de fatos independentes. Nenhum milhão de objetos é materializado em RAM.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from core.curriculum_taxonomy import (
    CANONICAL_ALIAS_TARGETS,
    CONCEPT_ALIASES,
    INVENTION_CYCLE,
    LEARNING_CORE_VIEW,
    OWNER_SOURCES,
    PRIORITY_VIEW,
    THEMES,
    CurriculumTheme,
)

VARIATIONS_PER_ITEM = 1_000_000
THEME_COUNT = len(THEMES)
THEME_ADDRESSABLE = THEME_COUNT * VARIATIONS_PER_ITEM

MODES = (
    "fundamentos", "derivacao", "problema", "experimento", "simulacao",
    "projeto", "evidencia", "comparacao", "falhas_limites", "fronteira",
)
DEPTHS = (
    "basico", "intermediario", "avancado", "graduacao", "pos_graduacao",
    "profissional", "pesquisa", "matematico", "computacional", "revisao",
)
EVIDENCE_LENSES = (
    "consenso", "padroes", "fonte_primaria", "medicao", "benchmark",
    "incerteza", "reprodutibilidade", "controversia", "historico", "fronteira",
)
CONTEXTS = (
    "teoria", "laboratorio", "engenharia", "industria", "espaco",
    "energia", "materiais", "computacao", "sistemas", "interdisciplinar",
)
REPRESENTATIONS = (
    "explicacao", "equacoes", "algoritmo", "workflow", "tabela",
    "checklist", "estudo_de_caso", "simulacao", "experimento", "design_review",
)
VERIFICATIONS = (
    "unidades", "dimensional", "numerica", "incerteza", "fontes",
    "confirmacao_independente", "casos_limite", "seguranca", "replicacao", "falseabilidade",
)

assert len(MODES) * len(DEPTHS) * len(EVIDENCE_LENSES) * len(CONTEXTS) * len(REPRESENTATIONS) * len(VERIFICATIONS) == VARIATIONS_PER_ITEM


@dataclass(frozen=True)
class CanonicalConcept:
    index: int
    label: str
    key: str
    primary_owner: str
    owners: tuple[str, ...]
    theme_ids: tuple[int, ...]
    theme_labels: tuple[str, ...]
    aliases: tuple[str, ...]
    sources: tuple[str, ...]
    evidence_class: str


@dataclass(frozen=True)
class CurriculumResolution:
    kind: str
    item_id: int
    label: str
    score: float


def _norm(text: str) -> str:
    value = str(text or "").strip().lower()
    replacements = {
        "c++": " cpp ", "i²c": " i2c ", "λcdm": " lcdm ", "×": " x ",
        "–": "-", "—": "-", "→": " ", "↔": " ",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = "".join(
        ch for ch in unicodedata.normalize("NFD", value)
        if unicodedata.category(ch) != "Mn"
    )
    value = re.sub(r"[^a-z0-9+#]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _tokens(text: str) -> set[str]:
    stop = {
        "a", "o", "e", "de", "da", "do", "das", "dos", "em", "para", "por",
        "com", "um", "uma", "ao", "na", "no", "as", "os", "the", "of", "and",
    }
    return {x for x in _norm(text).split() if len(x) > 1 and x not in stop}


_ALIAS_KEYS = {_norm(k): _norm(v) for k, v in CONCEPT_ALIASES.items()}
_ALIAS_LABELS = {_norm(v): v for v in CONCEPT_ALIASES.values()}

EVIDENCE_OVERRIDES = {
    _norm("buracos de minhoca"): "theoretical",
    _norm("métricas de warp"): "theoretical",
    _norm("curvas temporais fechadas"): "theoretical",
    _norm("engenharia conceitual do espaço-tempo"): "speculative-engineering",
    _norm("limites físicos de viagem temporal"): "theoretical-limit",
    _norm("limites físicos de atalhos espaciais"): "theoretical-limit",
    _norm("energia negativa"): "theoretical-quantum-limited",
    _norm("viagem interestelar"): "frontier-engineering",
    _norm("propulsão espacial avançada"): "frontier-engineering",
    _norm("fusão nuclear"): "experimental-engineering",
    _norm("teletransporte quântico"): "established-quantum-state-protocol",
    _norm("comunicação quântica"): "existing-and-experimental",
}


def _canonical_key(label: str) -> str:
    key = _norm(label)
    return _ALIAS_KEYS.get(key, key)


def _canonical_label(raw_label: str, key: str) -> str:
    if key in _ALIAS_LABELS:
        return _ALIAS_LABELS[key]
    return str(raw_label).strip()


def _theme_sources(theme: CurriculumTheme) -> tuple[str, ...]:
    return tuple(theme.source_families or OWNER_SOURCES.get(theme.owner, ()))


def _build_concepts() -> tuple[CanonicalConcept, ...]:
    records: dict[str, dict] = {}
    order: list[str] = []

    for theme in THEMES:
        for raw in theme.topics:
            key = _canonical_key(raw)
            if key not in records:
                order.append(key)
                records[key] = {
                    "label": _canonical_label(raw, key),
                    "owners": [],
                    "themes": [],
                    "aliases": [],
                    "sources": [],
                    "evidence": EVIDENCE_OVERRIDES.get(key, theme.evidence_class),
                }
            rec = records[key]
            if theme.owner not in rec["owners"]:
                rec["owners"].append(theme.owner)
            if theme.id not in rec["themes"]:
                rec["themes"].append(theme.id)
            if raw not in rec["aliases"]:
                rec["aliases"].append(raw)
            for source in _theme_sources(theme):
                if source not in rec["sources"]:
                    rec["sources"].append(source)
            # Uma ocorrência estabelecida em domínio regular prevalece sobre a
            # etiqueta genérica mixed-frontier do índice de fronteira.
            override = EVIDENCE_OVERRIDES.get(key)
            if override:
                rec["evidence"] = override
            elif theme.evidence_class == "established":
                rec["evidence"] = "established"

    # Acrescenta aliases reversos úteis sem criar conceitos novos.
    for target, aliases in CANONICAL_ALIAS_TARGETS.items():
        key = _canonical_key(target)
        if key not in records:
            continue
        for alias in aliases:
            if alias not in records[key]["aliases"]:
                records[key]["aliases"].append(alias)

    theme_by_id = {theme.id: theme for theme in THEMES}
    concepts: list[CanonicalConcept] = []
    for index, key in enumerate(order, 1):
        rec = records[key]
        theme_ids = tuple(rec["themes"])
        concepts.append(CanonicalConcept(
            index=index,
            label=rec["label"],
            key=key,
            primary_owner=rec["owners"][0],
            owners=tuple(rec["owners"]),
            theme_ids=theme_ids,
            theme_labels=tuple(theme_by_id[i].label for i in theme_ids),
            aliases=tuple(rec["aliases"]),
            sources=tuple(rec["sources"]),
            evidence_class=rec["evidence"],
        ))
    return tuple(concepts)


CONCEPTS = _build_concepts()
CONCEPT_COUNT = len(CONCEPTS)
RAW_TOPIC_MENTIONS = sum(len(theme.topics) for theme in THEMES)
DEDUPLICATED_MENTIONS = RAW_TOPIC_MENTIONS - CONCEPT_COUNT
CONCEPT_ADDRESSABLE = CONCEPT_COUNT * VARIATIONS_PER_ITEM
TOTAL_NEW_ADDRESSABLE = THEME_ADDRESSABLE + CONCEPT_ADDRESSABLE

_CONCEPT_BY_INDEX = {concept.index: concept for concept in CONCEPTS}
_THEME_BY_ID = {theme.id: theme for theme in THEMES}


def _decode_variation(variation_id: int) -> dict[str, str]:
    n = int(variation_id)
    if n < 1 or n > VARIATIONS_PER_ITEM:
        raise ValueError(f"variation_id deve estar entre 1 e {VARIATIONS_PER_ITEM}")
    value = n - 1
    indexes = []
    for _ in range(6):
        value, digit = divmod(value, 10)
        indexes.append(digit)
    return {
        "mode": MODES[indexes[0]],
        "depth": DEPTHS[indexes[1]],
        "evidence_lens": EVIDENCE_LENSES[indexes[2]],
        "context": CONTEXTS[indexes[3]],
        "representation": REPRESENTATIONS[indexes[4]],
        "verification": VERIFICATIONS[indexes[5]],
    }


def _evidence_guidance(evidence_class: str) -> str:
    if evidence_class in {"theoretical", "theoretical-limit", "theoretical-quantum-limited"}:
        return "Trate como física teórica: separe solução/modelo matemático, condição física necessária e evidência experimental disponível."
    if evidence_class in {"speculative-engineering", "frontier-engineering"}:
        return "Trate como fronteira/especulação de engenharia: não apresente como capacidade tecnológica demonstrada."
    if evidence_class == "experimental-engineering":
        return "Separe demonstração experimental, protótipo, escala de laboratório e implantação tecnológica/comercial."
    if evidence_class == "established-quantum-state-protocol":
        return "Deixe explícito que teletransporte quântico transfere estado/informação quântica, não matéria macroscópica."
    if evidence_class == "existing-and-experimental":
        return "Separe tecnologia já demonstrada, limitações práticas e linhas ainda experimentais."
    return "Diferencie consenso, modelo, hipótese, incerteza, controvérsia e limite de validade quando aplicável."


class CurriculumKnowledgeEngine:
    """Índice curricular granular com deduplicação semântica e materialização lazy."""

    def __init__(self):
        self.themes = THEMES
        self.concepts = CONCEPTS
        self._concept_catalog = []
        for concept in self.concepts:
            search_terms = {concept.label, *concept.aliases}
            for term in search_terms:
                self._concept_catalog.append((concept.index, term, _norm(term), _tokens(term)))
        self._theme_catalog = [
            (theme.id, theme.label, _norm(theme.label), _tokens(theme.label))
            for theme in self.themes
        ]

    def stats(self) -> dict:
        linked = sum(1 for c in self.concepts if len(c.theme_ids) > 1)
        cross_owner = sum(1 for c in self.concepts if len(c.owners) > 1)
        return {
            "themes": THEME_COUNT,
            "raw_topic_mentions": RAW_TOPIC_MENTIONS,
            "unique_concepts": CONCEPT_COUNT,
            "deduplicated_mentions": DEDUPLICATED_MENTIONS,
            "cross_theme_concepts": linked,
            "cross_owner_concepts": cross_owner,
            "variations_per_theme": VARIATIONS_PER_ITEM,
            "variations_per_concept": VARIATIONS_PER_ITEM,
            "theme_addressable_contents": THEME_ADDRESSABLE,
            "concept_addressable_contents": CONCEPT_ADDRESSABLE,
            "total_new_addressable_contents": TOTAL_NEW_ADDRESSABLE,
            "materialization": "on-demand",
            "priority_view_items": len(PRIORITY_VIEW),
            "learning_core_items": len(LEARNING_CORE_VIEW),
            "invention_cycle_steps": len(INVENTION_CYCLE),
        }

    def get_theme(self, theme_id: int) -> CurriculumTheme:
        try:
            return _THEME_BY_ID[int(theme_id)]
        except (KeyError, ValueError, TypeError) as exc:
            raise KeyError(f"tema curricular inválido: {theme_id}") from exc

    def get_concept(self, concept_index: int) -> CanonicalConcept:
        try:
            return _CONCEPT_BY_INDEX[int(concept_index)]
        except (KeyError, ValueError, TypeError) as exc:
            raise KeyError(f"conceito curricular inválido: {concept_index}") from exc

    def materialize_theme(self, theme_id: int, variation_id: int) -> dict:
        theme = self.get_theme(theme_id)
        axes = _decode_variation(variation_id)
        return {
            "id": f"CURRT-{theme.id:03d}-{int(variation_id):07d}",
            "kind": "theme",
            "theme_id": theme.id,
            "theme": theme.label,
            "owner": theme.owner,
            "topics": theme.topics,
            "sources": _theme_sources(theme),
            "evidence_class": theme.evidence_class,
            **axes,
            "answer": self._render_theme(theme, axes),
        }

    def materialize_concept(self, concept_index: int, variation_id: int) -> dict:
        concept = self.get_concept(concept_index)
        axes = _decode_variation(variation_id)
        return {
            "id": f"CURRC-{concept.index:04d}-{int(variation_id):07d}",
            "kind": "concept",
            "concept_index": concept.index,
            "concept": concept.label,
            "owner": concept.primary_owner,
            "owners": concept.owners,
            "themes": concept.theme_labels,
            "aliases": concept.aliases,
            "sources": concept.sources,
            "evidence_class": concept.evidence_class,
            **axes,
            "answer": self._render_concept(concept, axes),
        }

    def resolve(self, text: str) -> CurriculumResolution | None:
        q = _norm(text)
        if not q:
            return None
        q_tokens = _tokens(q)

        best: tuple[float, int, str, int, str] | None = None
        for concept_index, display, phrase, tokens in self._concept_catalog:
            if not phrase:
                continue
            overlap = len(q_tokens & tokens) / max(1, len(tokens))
            score = overlap
            if q == phrase:
                score += 3.0
            elif f" {phrase} " in f" {q} ":
                score += 2.0
            elif phrase in q and len(phrase) >= 5:
                score += 1.2
            if len(tokens) >= 2 and len(q_tokens & tokens) >= 2:
                score += 0.35
            candidate = (score, len(tokens), "concept", concept_index, display)
            if best is None or candidate > best:
                best = candidate

        for theme_id, display, phrase, tokens in self._theme_catalog:
            overlap = len(q_tokens & tokens) / max(1, len(tokens))
            score = overlap
            if q == phrase:
                score += 2.5
            elif f" {phrase} " in f" {q} ":
                score += 1.4
            candidate = (score, len(tokens), "theme", theme_id, display)
            if best is None or candidate > best:
                best = candidate

        if best is None:
            return None
        score, _, kind, item_id, label = best
        threshold = 1.15 if kind == "concept" else 1.35
        if score < threshold:
            return None
        return CurriculumResolution(kind=kind, item_id=item_id, label=label, score=score)

    def prefers(self, text: str) -> bool:
        resolved = self.resolve(text)
        if resolved is None:
            return False
        # Só antecipa os engines legados quando a correspondência é específica.
        # Isso evita que termos genéricos como "energia" ou "sistemas" engulam
        # rotas estáveis de Física/Química/Multidisciplinar.
        q = _norm(text)
        label = _norm(resolved.label)
        return resolved.score >= 2.0 or q == label or f" {label} " in f" {q} "

    def answer(self, text: str) -> str | None:
        resolved = self.resolve(text)
        if resolved is None:
            return None
        variation = self._variation_from_query(text)
        if resolved.kind == "concept":
            return self.materialize_concept(resolved.item_id, variation)["answer"]
        return self.materialize_theme(resolved.item_id, variation)["answer"]

    @staticmethod
    def _variation_from_query(text: str) -> int:
        q = _norm(text)
        mode = 0
        for i, hints in enumerate((
            ("conceito", "fundamento", "explique"), ("derive", "derivacao", "deduza"),
            ("problema", "calcule", "resolva"), ("experimento", "medicao", "laboratorio"),
            ("simule", "simulacao", "modelo numerico"), ("projeto", "dimensione", "engenharia"),
            ("evidencia", "fonte", "paper"), ("compare", "versus", "diferenca"),
            ("falha", "limite", "erro"), ("fronteira", "estado da arte", "futuro"),
        )):
            if any(_norm(h) in q for h in hints):
                mode = i
                break
        depth = 6 if any(x in q for x in ("pesquisa", "estado da arte", "paper")) else 2
        evidence = 5 if any(x in q for x in ("incerteza", "erro", "confianca")) else 0
        context = 9 if any(x in q for x in ("interdisciplin", "conecte", "relacione")) else 0
        representation = 1 if any(x in q for x in ("equacao", "equações", "formula")) else 0
        verification = 4 if any(x in q for x in ("fonte", "referencia", "evidencia")) else 0
        # Base 10, seis eixos; +1 porque IDs são 1-based.
        return 1 + mode + depth * 10 + evidence * 100 + context * 1_000 + representation * 10_000 + verification * 100_000

    @staticmethod
    def _render_theme(theme: CurriculumTheme, axes: dict[str, str]) -> str:
        source_text = ", ".join(_theme_sources(theme)) or "fontes técnicas da área"
        topics = ", ".join(theme.topics[:8])
        more = len(theme.topics) - min(8, len(theme.topics))
        suffix = f" (+{more} conceitos ligados)" if more else ""
        return (
            f"📚 CURRÍCULO — {theme.label}. Área proprietária: {theme.owner}. "
            f"Eixos: {axes['mode']} / {axes['depth']} / {axes['evidence_lens']} / {axes['context']}. "
            f"Mapa canônico inclui: {topics}{suffix}. "
            f"Fontes-guia: {source_text}. {_evidence_guidance(theme.evidence_class)} "
            "Use os conceitos canônicos ligados; não replique fatos já existentes em outra base."
        )

    @staticmethod
    def _render_concept(concept: CanonicalConcept, axes: dict[str, str]) -> str:
        source_text = ", ".join(concept.sources[:6]) or "fontes técnicas da área"
        memberships = ", ".join(concept.theme_labels)
        return (
            f"📘 CURRÍCULO — {concept.label}. Área principal: {concept.primary_owner}; "
            f"conexões: {memberships}. Modo={axes['mode']}, profundidade={axes['depth']}, "
            f"evidência={axes['evidence_lens']}, contexto={axes['context']}, "
            f"representação={axes['representation']}, verificação={axes['verification']}. "
            f"Fontes-guia: {source_text}. {_evidence_guidance(concept.evidence_class)} "
            "Ao responder, preserve unidades/IDs/equações, explicite hipóteses e conecte às bases existentes sem duplicá-las."
        )

    def duplicates_report(self) -> tuple[dict, ...]:
        rows = []
        for concept in self.concepts:
            if len(concept.theme_ids) > 1 or len(concept.aliases) > 1:
                rows.append({
                    "concept": concept.label,
                    "themes": concept.theme_labels,
                    "aliases": concept.aliases,
                    "owners": concept.owners,
                })
        return tuple(rows)

    def theme_report(self) -> tuple[dict, ...]:
        rows = []
        for theme in self.themes:
            concept_indexes = [
                c.index for c in self.concepts if theme.id in c.theme_ids
            ]
            rows.append({
                "id": theme.id,
                "theme": theme.label,
                "owner": theme.owner,
                "unique_concepts": len(concept_indexes),
                "theme_synthesis_contents": VARIATIONS_PER_ITEM,
                "concept_indexes": tuple(concept_indexes),
                "evidence_class": theme.evidence_class,
            })
        return tuple(rows)
