"""BLOCO 3 — Arquitetura Universal do Conhecimento da STAR.

Pipeline central:

CANONICAL KNOWLEDGE
→ CLAIMS
→ EVIDENCE
→ KNOWLEDGE GRAPH
→ SEMANTIC RELATIONS
→ INDEXES
→ CACHE
→ STAR

O BLOCO 3 não cria um segundo ledger nem um segundo grafo. Claims/evidências são
fornecidos pelo BLOCO 2; o grafo é o Knowledge Graph já existente na MIND; esta
camada organiza conhecimento canônico, metadados, aliases, taxonomias, índices,
consulta e cache. O catálogo de 1B é lógico e materializado sob demanda.
"""
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import re
import time
from typing import Any

from core.cognitive_catalog import CONTEXTS, FAMILIES, LENSES, STYLES
from core.epistemics import EpistemicFoundation
from database.universal_knowledge_store import UniversalKnowledgeStore, normalize_text


KNOWLEDGE_TYPES = (
    "concept",
    "entity",
    "property",
    "category",
    "taxonomy",
    "subtopic",
    "context",
    "event",
    "rule",
    "exception",
)

SEMANTIC_FAMILIES = (
    "identity",
    "taxonomy",
    "composition",
    "causality",
    "dependency",
    "evidence",
    "temporal",
    "contextual",
    "equivalence",
    "cross_domain",
)

ACCESS_MODES = (
    "exact_lookup",
    "alias_lookup",
    "full_text",
    "facet_filter",
    "graph_neighbors",
    "taxonomy_walk",
    "claim_trace",
    "temporal_filter",
    "cross_link",
    "cached_query",
)

SEMANTIC_RELATIONS = (
    "related_to",
    "is_a",
    "instance_of",
    "part_of",
    "has_part",
    "broader_than",
    "narrower_than",
    "equivalent_to",
    "same_as",
    "causes",
    "caused_by",
    "depends_on",
    "supports",
    "contradicts",
    "refines",
    "contextualizes",
    "precedes",
    "follows",
    "associated_with",
    "cross_link",
)

CLAIM_ROLES = (
    "canonical",
    "supporting",
    "corroborating",
    "contextual",
    "exception",
    "historical",
)

UNIVERSAL_COMPONENTS = (
    "concepts",
    "entities",
    "aliases",
    "relations",
    "properties",
    "categories",
    "taxonomies",
    "subtopics",
    "sources",
    "evidence",
    "contexts",
    "events",
    "rules",
    "exceptions",
    "temporality",
    "provenance",
    "cross_links",
)

UNIVERSAL_AREAS = (
    ("canonical_knowledge", "conhecimento canônico"),
    ("claims", "claims e afirmações"),
    ("evidence", "evidências"),
    ("knowledge_graph", "Knowledge Graph"),
    ("semantic_relations", "relações semânticas"),
    ("concepts", "conceitos"),
    ("entities", "entidades"),
    ("aliases", "aliases e equivalências nominais"),
    ("properties", "propriedades"),
    ("categories", "categorias"),
    ("taxonomies", "taxonomias"),
    ("subtopics", "subtemas"),
    ("sources", "fontes"),
    ("contexts", "contextos"),
    ("events", "eventos"),
    ("rules", "regras"),
    ("exceptions", "exceções"),
    ("temporality", "temporalidade"),
    ("provenance", "proveniência"),
    ("indexes_cache", "índices, cache, deduplicação e atualização"),
)

UNIVERSAL_CANONICAL_NODES = len(UNIVERSAL_AREAS) * len(LENSES)
UNIVERSAL_VARIANTS_PER_NODE = (
    len(FAMILIES)
    * len(STYLES)
    * len(CONTEXTS)
    * len(KNOWLEDGE_TYPES)
    * len(SEMANTIC_FAMILIES)
    * len(ACCESS_MODES)
)
UNIVERSAL_ADDRESSABLE_CONTENTS = UNIVERSAL_CANONICAL_NODES * UNIVERSAL_VARIANTS_PER_NODE

if UNIVERSAL_CANONICAL_NODES != 1_000:
    raise RuntimeError("BLOCO 3 deve manter exatamente 1.000 nós canônicos")
if UNIVERSAL_VARIANTS_PER_NODE != 1_000_000:
    raise RuntimeError("BLOCO 3 deve manter exatamente 1.000.000 combinações por nó")
if UNIVERSAL_ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("BLOCO 3 deve manter exatamente 1B de representações endereçáveis")


class UniversalKnowledgeCatalog:
    """Catálogo lógico de 1B por namespace, sem materializar 1B de linhas."""

    PREFIX = "UK"

    @staticmethod
    def _namespace(namespace: str) -> str:
        value = str(namespace or "").strip().upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9_-]{1,15}", value):
            raise ValueError("namespace universal inválido")
        return value

    def stats(self, namespace: str = "B03") -> dict:
        namespace = self._namespace(namespace)
        return {
            "namespace": namespace,
            "areas": len(UNIVERSAL_AREAS),
            "lenses_per_area": len(LENSES),
            "canonical_nodes": UNIVERSAL_CANONICAL_NODES,
            "variants_per_node": UNIVERSAL_VARIANTS_PER_NODE,
            "addressable_contents": UNIVERSAL_ADDRESSABLE_CONTENTS,
            "materialization": "on-demand",
            "prepopulated_knowledge_rows": 0,
            "truthfulness_note": (
                "1B é capacidade lógica independente por namespace; não representa "
                "1B de fatos pesquisados ou linhas pré-carregadas"
            ),
        }

    def content_id(self, namespace: str, node_index: int, variant_index: int) -> str:
        namespace = self._namespace(namespace)
        node_index = int(node_index)
        variant_index = int(variant_index)
        if not 0 <= node_index < UNIVERSAL_CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= variant_index < UNIVERSAL_VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = node_index * UNIVERSAL_VARIANTS_PER_NODE + variant_index + 1
        return f"{self.PREFIX}-{namespace}-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(
            r"UK-([A-Z][A-Z0-9_-]{1,15})-(\d{10})",
            str(identifier or "").strip().upper(),
        )
        if not match:
            return None
        namespace = match.group(1)
        absolute = int(match.group(2))
        if not 1 <= absolute <= UNIVERSAL_ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, UNIVERSAL_VARIANTS_PER_NODE)
        area_index, lens_index = divmod(node_index, len(LENSES))
        area_key, area_label = UNIVERSAL_AREAS[area_index]
        lens_key, lens_label = LENSES[lens_index]

        remainder = variant_index
        dimensions = []
        for size in (10, 10, 10, 10, 10, 10):
            remainder, index = divmod(remainder, size)
            dimensions.append(index)
        access_i, semantic_i, kind_i, context_i, style_i, family_i = dimensions

        return {
            "id": f"UK-{namespace}-{absolute:010d}",
            "namespace": namespace,
            "node_index": node_index,
            "variant_index": variant_index,
            "area": area_key,
            "area_label": area_label,
            "lens": lens_key,
            "lens_label": lens_label,
            "family": FAMILIES[family_i],
            "style": STYLES[style_i],
            "context": CONTEXTS[context_i],
            "knowledge_type": KNOWLEDGE_TYPES[kind_i],
            "semantic_family": SEMANTIC_FAMILIES[semantic_i],
            "access_mode": ACCESS_MODES[access_i],
            "prompt": (
                f"Organizar {area_label} pela lente {lens_label}, como "
                f"{KNOWLEDGE_TYPES[kind_i]}, usando {SEMANTIC_FAMILIES[semantic_i]} "
                f"e acesso {ACCESS_MODES[access_i]}; preservar claims, evidências, "
                "proveniência, temporalidade, deduplicação e cross-links."
            ),
        }


class QueryCache:
    """Cache LRU/TTL pequeno e descartável; nunca é fonte de verdade."""

    def __init__(self, max_entries: int = 256, ttl_seconds: float = 120.0):
        self.max_entries = max(1, int(max_entries))
        self.ttl_seconds = max(1.0, float(ttl_seconds))
        self._data: OrderedDict[tuple, tuple[float, Any]] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.invalidations = 0

    def get(self, key: tuple):
        item = self._data.get(key)
        if item is None:
            self.misses += 1
            return None
        created_at, value = item
        if time.monotonic() - created_at > self.ttl_seconds:
            self._data.pop(key, None)
            self.misses += 1
            return None
        self._data.move_to_end(key)
        self.hits += 1
        return deepcopy(value)

    def set(self, key: tuple, value):
        self._data[key] = (time.monotonic(), deepcopy(value))
        self._data.move_to_end(key)
        while len(self._data) > self.max_entries:
            self._data.popitem(last=False)

    def invalidate(self):
        if self._data:
            self.invalidations += 1
        self._data.clear()

    def stats(self) -> dict:
        return {
            "entries": len(self._data),
            "max_entries": self.max_entries,
            "ttl_seconds": self.ttl_seconds,
            "hits": self.hits,
            "misses": self.misses,
            "invalidations": self.invalidations,
            "source_of_truth": False,
        }


class UniversalKnowledgeArchitecture:
    """Orquestra conhecimento canônico sobre Epistemics + Knowledge Graph."""

    PIPELINE = (
        "CANONICAL KNOWLEDGE",
        "CLAIMS",
        "EVIDENCE",
        "KNOWLEDGE GRAPH",
        "SEMANTIC RELATIONS",
        "INDEXES",
        "CACHE",
        "STAR",
    )

    def __init__(
        self,
        epistemics: EpistemicFoundation,
        graph,
        *,
        store: UniversalKnowledgeStore | None = None,
        cache: QueryCache | None = None,
    ):
        self.epistemics = epistemics
        self.graph = graph
        self.store = store or UniversalKnowledgeStore(epistemics.store)
        self.catalog = UniversalKnowledgeCatalog()
        self.cache = cache or QueryCache()
        self._register_current_namespaces()

    def _register_current_namespaces(self):
        current = (
            ("B01", "BLOCO 1 — PRINCÍPIOS INVIOLÁVEIS", "core/foundations.py"),
            ("B02", "BLOCO 2 — FUNDAÇÃO EPISTÊMICA", "core/epistemics.py"),
            ("B03", "BLOCO 3 — ARQUITETURA UNIVERSAL DO CONHECIMENTO", "core/universal_knowledge.py"),
        )
        for namespace, label, source in current:
            self.store.register_namespace(
                namespace,
                label,
                logical_capacity=UNIVERSAL_ADDRESSABLE_CONTENTS,
                source=source,
                metadata={"materialization": "on-demand"},
            )

    @staticmethod
    def stable_knowledge_id(namespace: str, knowledge_type: str, canonical_label: str) -> str:
        normalized = normalize_text(canonical_label)
        if not normalized:
            raise ValueError("canonical_label vazio")
        payload = f"{namespace.upper()}\n{knowledge_type}\n{normalized}"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24].upper()
        return f"UKNOW-{digest}"

    def register_namespace(
        self,
        namespace: str,
        label: str,
        *,
        logical_capacity: int = UNIVERSAL_ADDRESSABLE_CONTENTS,
        source: str | None = None,
        metadata=None,
    ) -> dict:
        result = self.store.register_namespace(
            namespace,
            label,
            logical_capacity=logical_capacity,
            source=source,
            metadata=metadata,
        )
        self.cache.invalidate()
        return result

    def promote_canonical(
        self,
        record_id: str,
        canonical_label: str,
        *,
        knowledge_type: str = "concept",
        namespace: str = "B03",
        summary: str = "",
        aliases: list[str] | tuple[str, ...] | None = None,
        properties: dict | None = None,
        categories: list[str] | tuple[str, ...] | None = None,
        subtopics: list[str] | tuple[str, ...] | None = None,
        contexts: list[str] | tuple[str, ...] | None = None,
        rules: list | tuple | None = None,
        exceptions: list | tuple | None = None,
        valid_from: str | None = None,
        valid_until: str | None = None,
        provenance: dict | None = None,
    ) -> dict:
        if knowledge_type not in KNOWLEDGE_TYPES:
            raise ValueError(f"knowledge_type inválido: {knowledge_type}")
        namespace = str(namespace or "").strip().upper()
        if self.store.get_namespace(namespace) is None:
            raise ValueError(f"namespace não registrado: {namespace}")

        trace = self.epistemics.trace(record_id)
        claim = trace["record"]
        if claim["lifecycle_state"] != "CANONICAL":
            raise ValueError("CANONICAL KNOWLEDGE exige claim CANONICAL do BLOCO 2")
        if claim["epistemic_kind"] != "fact":
            raise ValueError("CANONICAL KNOWLEDGE exige claim classificado como fact")

        knowledge_id = self.stable_knowledge_id(namespace, knowledge_type, canonical_label)
        existing = self.store.find_by_identity(namespace, canonical_label, knowledge_type)
        created = existing is None

        if existing is None:
            source = trace.get("origin_source")
            provenance_payload = provenance or {
                "canonical_claim_id": record_id,
                "origin_type": claim["origin_type"],
                "origin_ref": claim["origin_ref"],
                "learned_at": claim["learned_at"],
                "source_id": source.get("source_id") if source else None,
            }
            self.store.upsert_knowledge(
                knowledge_id,
                namespace=namespace,
                canonical_label=canonical_label,
                knowledge_type=knowledge_type,
                canonical_claim_id=record_id,
                summary=summary,
                properties=properties or {},
                rules=rules or [],
                exceptions=exceptions or [],
                provenance=provenance_payload,
                valid_from=valid_from or claim.get("valid_from"),
                valid_until=valid_until or claim.get("valid_until"),
            )
            self.store.link_claim(knowledge_id, record_id, "canonical")
        else:
            knowledge_id = existing["knowledge_id"]
            role = "canonical" if existing["canonical_claim_id"] == record_id else "corroborating"
            self.store.link_claim(knowledge_id, record_id, role)

        self.graph.add_entity(
            f"universal_{knowledge_type}",
            canonical_label,
            data={
                "namespace": namespace,
                "canonical_claim_id": self.store.get_knowledge(knowledge_id)["canonical_claim_id"],
                "source_of_truth": "universal_knowledge",
            },
            confidence=float(claim["confidence"]),
            node_id=knowledge_id,
        )

        for alias in aliases or ():
            self.store.add_alias(knowledge_id, alias, source_ref=record_id)
        for facet_type, values in (
            ("category", categories or ()),
            ("subtopic", subtopics or ()),
            ("context", contexts or ()),
        ):
            for value in values:
                self.store.add_facet(knowledge_id, facet_type, value)

        self.store.record_event(
            knowledge_id,
            "canonical_registered" if created else "canonical_deduplicated",
            source_record_id=record_id,
            payload={"created": created, "knowledge_type": knowledge_type, "namespace": namespace},
        )
        self.cache.invalidate()
        result = self.store.get_knowledge(knowledge_id)
        result["created"] = created
        return result

    def add_alias(self, knowledge_id: str, alias: str, *, locale: str = "", source_ref: str | None = None) -> dict:
        result = self.store.add_alias(knowledge_id, alias, locale=locale, source_ref=source_ref)
        self.cache.invalidate()
        return result

    def add_facet(self, knowledge_id: str, facet_type: str, value: str) -> dict:
        if facet_type not in {"category", "subtopic", "context"}:
            raise ValueError("facet_type deve ser category, subtopic ou context")
        result = self.store.add_facet(knowledge_id, facet_type, value)
        self.cache.invalidate()
        return result

    def link_claim(self, knowledge_id: str, record_id: str, *, role: str = "supporting") -> dict:
        if role not in CLAIM_ROLES:
            raise ValueError(f"role inválido: {role}")
        record = self.epistemics.store.get_epistemic_record(record_id)
        if record is None:
            raise KeyError(record_id)
        if record["lifecycle_state"] == "RETRACTED" and role != "historical":
            raise ValueError("claim RETRACTED só pode ser vinculado como historical")
        result = self.store.link_claim(knowledge_id, record_id, role)
        self.cache.invalidate()
        return result

    def relate(
        self,
        source_knowledge_id: str,
        target_knowledge_id: str,
        relation: str,
        *,
        weight: float = 1.0,
        metadata: dict | None = None,
    ) -> dict:
        if relation not in SEMANTIC_RELATIONS:
            raise ValueError(f"relação semântica inválida: {relation}")
        if source_knowledge_id == target_knowledge_id:
            raise ValueError("relação semântica exige dois conhecimentos distintos")
        for knowledge_id in (source_knowledge_id, target_knowledge_id):
            if self.store.get_knowledge(knowledge_id) is None:
                raise KeyError(knowledge_id)
        payload = {"semantic": True, **(metadata or {})}
        self.graph.relate(
            source_knowledge_id,
            target_knowledge_id,
            relation,
            weight=max(0.0, min(float(weight), 1.0)),
            metadata=payload,
        )
        self.cache.invalidate()
        return {
            "source_id": source_knowledge_id,
            "target_id": target_knowledge_id,
            "relation": relation,
            "weight": max(0.0, min(float(weight), 1.0)),
            "metadata": payload,
        }

    def add_taxonomy(self, child_id: str, parent_id: str, *, relation: str = "is_a") -> dict:
        if relation not in {"is_a", "part_of", "instance_of", "narrower_than"}:
            raise ValueError("relação taxonômica inválida")
        inverse = {
            "is_a": "broader_than",
            "part_of": "has_part",
            "instance_of": "broader_than",
            "narrower_than": "broader_than",
        }[relation]
        forward = self.relate(child_id, parent_id, relation, metadata={"taxonomy": True})
        self.relate(parent_id, child_id, inverse, metadata={"taxonomy": True, "inverse_of": relation})
        return forward

    def add_cross_link(self, source_id: str, target_id: str, *, label: str | None = None, weight: float = 1.0) -> dict:
        return self.relate(
            source_id,
            target_id,
            "cross_link",
            weight=weight,
            metadata={"cross_link": True, "label": label},
        )

    def record_event(
        self,
        knowledge_id: str,
        event_type: str,
        *,
        event_time: str | None = None,
        source_record_id: str | None = None,
        payload: dict | None = None,
    ) -> dict:
        result = self.store.record_event(
            knowledge_id,
            event_type,
            event_time=event_time,
            source_record_id=source_record_id,
            payload=payload,
        )
        self.cache.invalidate()
        return result

    def update(self, knowledge_id: str, **changes) -> dict:
        mapping = {
            "summary": "summary",
            "properties": "properties_json",
            "rules": "rules_json",
            "exceptions": "exceptions_json",
            "provenance": "provenance_json",
            "valid_from": "valid_from",
            "valid_until": "valid_until",
        }
        unknown = set(changes) - set(mapping)
        if unknown:
            raise ValueError("campos de atualização inválidos: " + ", ".join(sorted(unknown)))
        store_changes = {mapping[key]: value for key, value in changes.items()}
        result = self.store.update_knowledge(knowledge_id, store_changes)
        canonical_trace = self.epistemics.trace(result["canonical_claim_id"])
        self.graph.add_entity(
            f"universal_{result['knowledge_type']}",
            result["canonical_label"],
            data={
                "namespace": result["namespace"],
                "canonical_claim_id": result["canonical_claim_id"],
                "revision": result["revision"],
                "source_of_truth": "universal_knowledge",
            },
            confidence=float(canonical_trace["record"]["confidence"]),
            node_id=knowledge_id,
        )
        self.store.record_event(
            knowledge_id,
            "canonical_metadata_updated",
            source_record_id=result["canonical_claim_id"],
            payload={"fields": sorted(changes)},
        )
        self.cache.invalidate()
        return self.store.get_knowledge(knowledge_id)

    def get(self, knowledge_id: str) -> dict | None:
        return self.store.get_knowledge(knowledge_id)

    def query(self, query: str, *, namespace: str | None = None, limit: int = 10) -> list[dict]:
        normalized = normalize_text(query)
        if not normalized:
            return []
        namespace_key = str(namespace or "").upper() or None
        key = ("query", normalized, namespace_key, max(1, min(int(limit), 100)))
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        results = self.store.search(query, namespace=namespace_key, limit=limit)
        self.cache.set(key, results)
        return results

    def query_facet(
        self,
        facet_type: str,
        value: str,
        *,
        namespace: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        key = (
            "facet",
            str(facet_type).lower(),
            normalize_text(value),
            str(namespace or "").upper() or None,
            max(1, min(int(limit), 500)),
        )
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        results = self.store.query_facet(facet_type, value, namespace=namespace, limit=limit)
        self.cache.set(key, results)
        return results

    def trace(self, knowledge_id: str) -> dict:
        knowledge = self.store.get_knowledge(knowledge_id)
        if knowledge is None:
            raise KeyError(knowledge_id)
        canonical_claim = self.epistemics.trace(knowledge["canonical_claim_id"])
        claims = []
        for link in knowledge["claims"][:50]:
            try:
                traced = self.epistemics.trace(link["record_id"])
            except KeyError:
                continue
            claims.append({"role": link["role"], "trace": traced})
        return {
            "knowledge": knowledge,
            "canonical_claim": canonical_claim,
            "claims": claims,
            "semantic_relations": self.graph.neighbors(knowledge_id, limit=200),
            "events": self.store.events(knowledge_id, limit=200),
            "pipeline": list(self.PIPELINE),
        }

    def stats(self) -> dict:
        namespaces = self.store.list_namespaces()
        return {
            "status": "experimental-integrated",
            "pipeline": list(self.PIPELINE),
            "components": list(UNIVERSAL_COMPONENTS),
            "catalog": self.catalog.stats("B03"),
            "namespaces": namespaces,
            "namespace_capacity_independent": True,
            "registered_logical_capacity": sum(int(item["logical_capacity"]) for item in namespaces),
            "persisted": self.store.stats(),
            "cache": self.cache.stats(),
            "graph_source": "knowledge_nodes/knowledge_edges",
            "claims_evidence_source": "BLOCO 2 / epistemic ledger",
        }

    def handle(self, text: str) -> str | None:
        raw = " ".join(str(text or "").strip().split())
        low = raw.casefold()
        if not raw:
            return None
        if low in {
            "status bloco 3",
            "status conhecimento universal",
            "arquitetura universal do conhecimento",
            "status arquitetura universal",
        }:
            stats = self.stats()
            return (
                "🌐 BLOCO 3 — ARQUITETURA UNIVERSAL DO CONHECIMENTO: "
                f"{stats['catalog']['addressable_contents']} conteúdos endereçáveis em B03 | "
                f"{len(stats['namespaces'])} namespaces independentes | "
                f"{stats['persisted']['knowledge']} conhecimentos canônicos materializados | "
                f"FTS5={'ATIVO' if stats['persisted']['fts5_available'] else 'FALLBACK'} | "
                "claims/evidências=BLOCO 2 | grafo=COMPARTILHADO."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"🌐 {item['id']} — {item['area_label']} / {item['lens_label']}\n{item['prompt']}"
        trace_match = re.fullmatch(
            r"(?:rastreie conhecimento|trace knowledge|status conhecimento)\s+(UKNOW-[A-F0-9]{24})",
            raw,
            re.I,
        )
        if trace_match:
            try:
                traced = self.trace(trace_match.group(1).upper())
            except KeyError:
                return "Conhecimento universal não encontrado."
            knowledge = traced["knowledge"]
            claim = traced["canonical_claim"]["record"]
            return (
                f"🌐 {knowledge['knowledge_id']} | {knowledge['knowledge_type']} | "
                f"{knowledge['canonical_label']} | claim={claim['lifecycle_state']} | "
                f"aliases={len(knowledge['aliases'])} | facetas={len(knowledge['facets'])} | "
                f"relações={len(traced['semantic_relations'])}."
            )
        query_match = re.match(
            r"^(?:buscar conhecimento universal|busque conhecimento universal|consulta universal)\s+(.+)$",
            raw,
            re.I,
        )
        if query_match:
            results = self.query(query_match.group(1), limit=5)
            if not results:
                return "Não encontrei conhecimento canônico no índice universal para essa consulta."
            return "🌐 Conhecimento universal:\n" + "\n".join(
                f"- {item['canonical_label']} [{item['knowledge_type']}] ({item['knowledge_id']})"
                for item in results
            )
        return None
