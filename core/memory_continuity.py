"""BLOCO 13 — memória e continuidade da STAR.

A camada amplia a memória cognitiva já existente; não cria um segundo banco,
segundo grafo ou uma autobiografia paralela. Memórias persistentes continuam em
``cognitive_memory`` no ``star.db`` oficial e relações/consolidações usam o
Knowledge Graph compartilhado. Working memory é bounded e transitória por padrão.

O catálogo de 1B é uma capacidade lógica on-demand: 500 nós canônicos x 2M de
combinações determinísticas. Não representa 1B de lembranças ou linhas físicas.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from math import prod
import re
import unicodedata
from typing import Any, Iterable

from core.universal_knowledge import UniversalKnowledgeArchitecture


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


MEMORY_KINDS = (
    "working",
    "episodic",
    "semantic",
    "conversation",
    "project",
    "people",
    "object",
    "social",
    "autobiographical",
    "temporal",
)

MEMORY_KIND_LABELS = {
    "working": "Working Memory",
    "episodic": "Memória episódica",
    "semantic": "Memória semântica",
    "conversation": "Memória de conversa",
    "project": "Memória de projeto",
    "people": "Memória de pessoas",
    "object": "Memória de objetos",
    "social": "Memória social",
    "autobiographical": "Memória autobiográfica da STAR",
    "temporal": "Memória temporal",
}


@dataclass(frozen=True)
class MemoryBranch:
    kind: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(";") if item.strip())


MEMORY_BRANCHES = (
    MemoryBranch("working", "active_items", "Itens ativos", _subs("conteúdo ativo;entidades ativas;referências recentes;estado temporário")),
    MemoryBranch("working", "active_goals", "Objetivos ativos", _subs("objetivos;prioridades;restrições;próximas ações cognitivas")),
    MemoryBranch("working", "recent_context", "Contexto recente", _subs("janela recente;turnos;ambiente;tarefa atual;contexto")),
    MemoryBranch("working", "temporary_results", "Resultados temporários", _subs("resultados intermediários;cálculos;hipóteses;artefatos transitórios")),
    MemoryBranch("working", "open_threads", "Questões e threads abertas", _subs("perguntas;pendências;hipóteses abertas;itens não resolvidos")),

    MemoryBranch("episodic", "events", "Eventos", _subs("eventos;ocorrências;sequência;resultado;participantes")),
    MemoryBranch("episodic", "experiences", "Experiências", _subs("experiência;percepção;resultado;significado;fonte auditável")),
    MemoryBranch("episodic", "places", "Locais de eventos", _subs("local;ambiente;posição contextual;origem espacial")),
    MemoryBranch("episodic", "participants", "Participantes", _subs("entidades;pessoas;objetos;sistemas;papéis no evento")),
    MemoryBranch("episodic", "outcomes", "Resultados de episódios", _subs("resultado;consequência;mudança;aprendizado;estado posterior")),

    MemoryBranch("semantic", "concepts", "Conceitos lembrados", _subs("conceitos;definições;significados;categorias")),
    MemoryBranch("semantic", "facts", "Fatos lembrados", _subs("fatos;proveniência;confiança;validade;revisão")),
    MemoryBranch("semantic", "rules", "Regras e princípios", _subs("regras;exceções;condições;aplicação")),
    MemoryBranch("semantic", "categories", "Categorias e taxonomias", _subs("categorias;hierarquia;classe;tipo;relação semântica")),
    MemoryBranch("semantic", "meanings", "Significados consolidados", _subs("significado;síntese;interpretação consolidada;contexto")),

    MemoryBranch("conversation", "turns", "Turnos de conversa", _subs("mensagem;papel;turno;sequência;data")),
    MemoryBranch("conversation", "topics", "Tópicos de conversa", _subs("assunto;tópico;mudança de tópico;referência cruzada")),
    MemoryBranch("conversation", "commitments", "Compromissos conversacionais", _subs("pedido;compromisso;limite;preferência declarada;fonte")),
    MemoryBranch("conversation", "decisions", "Decisões em conversa", _subs("decisão;motivo;alternativas;resultado;contexto")),
    MemoryBranch("conversation", "unresolved", "Assuntos não resolvidos", _subs("pendência;follow-up;questão aberta;continuidade")),

    MemoryBranch("project", "goals", "Objetivos de projeto", _subs("objetivo;escopo;critério de sucesso;prioridade")),
    MemoryBranch("project", "milestones", "Marcos", _subs("milestone;versão;release;entrega;data")),
    MemoryBranch("project", "decisions", "Decisões de projeto", _subs("decisão;trade-off;motivo;aprovação;fonte")),
    MemoryBranch("project", "artifacts", "Artefatos de projeto", _subs("arquivo;documento;código;commit;PR;resultado")),
    MemoryBranch("project", "progress", "Progresso e estado", _subs("progresso;status;bloqueio;próximo passo;histórico")),

    MemoryBranch("people", "identity_refs", "Referências de identidade", _subs("nome;identificador;fonte declarada;reconhecimento não autenticador")),
    MemoryBranch("people", "declared_preferences", "Preferências declaradas", _subs("preferência declarada;fonte;contexto;validade;revisão")),
    MemoryBranch("people", "relationships", "Relações com pessoas", _subs("relação;papel;contexto;limites;confiança")),
    MemoryBranch("people", "interactions", "Interações com pessoas", _subs("interação;evento;contexto;data;resultado")),
    MemoryBranch("people", "boundaries", "Limites e consentimento", _subs("consentimento;privacidade;permissão;limite;revogação")),

    MemoryBranch("object", "identity", "Identidade de objetos", _subs("objeto;identificador;tipo;propriedades observadas")),
    MemoryBranch("object", "state_history", "Histórico de estado de objetos", _subs("estado;mudança;observação;incerteza;data")),
    MemoryBranch("object", "location_history", "Histórico de localização", _subs("local;movimento;última observação;incerteza")),
    MemoryBranch("object", "relations", "Relações entre objetos", _subs("parte de;próximo a;contém;associado;dependência")),
    MemoryBranch("object", "affordances", "Usos e affordances lembradas", _subs("função;uso;restrição;risco;contexto")),

    MemoryBranch("social", "roles", "Papéis sociais", _subs("papel;função social;contexto;mudança;limites")),
    MemoryBranch("social", "relationships", "Relações sociais", _subs("relação;grupo;confiança;histórico;contexto")),
    MemoryBranch("social", "norms", "Normas e expectativas", _subs("norma;expectativa;contexto cultural;exceção;fonte")),
    MemoryBranch("social", "shared_events", "Eventos sociais compartilhados", _subs("evento;pessoas;local;data;significado")),
    MemoryBranch("social", "interaction_context", "Contexto de interação", _subs("situação;tom;papéis;limites;continuidade")),

    MemoryBranch("autobiographical", "self_events", "Eventos da própria STAR", _subs("evento próprio;fonte;referência auditável;data;continuidade")),
    MemoryBranch("autobiographical", "release_history", "Histórico de versões", _subs("versão;release;commit;PR;validação;data")),
    MemoryBranch("autobiographical", "capability_changes", "Mudanças de capacidade", _subs("capacidade;adição;remoção;degradação;fonte;versão")),
    MemoryBranch("autobiographical", "experiences", "Experiências auditáveis da STAR", _subs("experiência;interação;fonte;referência;significado;não fabricar")),
    MemoryBranch("autobiographical", "continuity", "Continuidade da STAR", _subs("identidade persistente;história;estado;transição;proveniência")),

    MemoryBranch("temporal", "dates", "Datas e âncoras temporais", _subs("data;hora;timezone;instante;fonte")),
    MemoryBranch("temporal", "intervals", "Intervalos", _subs("início;fim;duração;janela temporal")),
    MemoryBranch("temporal", "sequences", "Sequências", _subs("antes;depois;ordem;cadeia de eventos")),
    MemoryBranch("temporal", "recurrences", "Recorrências", _subs("frequência;periodicidade;exceção;última ocorrência")),
    MemoryBranch("temporal", "relations", "Relações temporais", _subs("precede;segue;simultâneo;sobreposição;causalidade não presumida")),
)

MEMORY_LENSES = (
    ("event", "evento", "o que aconteceu ou está ativo"),
    ("entity", "entidade", "quem ou o que participa da memória"),
    ("date_time", "data e tempo", "quando ocorreu, foi observado ou permanece válido"),
    ("relation", "relação", "como a memória se conecta a outras memórias e entidades"),
    ("location", "local", "onde o evento/objeto/contexto ocorreu quando conhecido"),
    ("importance", "importância", "qual relevância foi registrada e por qual motivo"),
    ("context", "contexto", "qual situação, projeto, conversa ou ambiente dá sentido à memória"),
    ("experience", "experiência", "qual experiência auditável está associada sem fabricar vivência"),
    ("source", "fonte", "qual origem e referência sustentam a lembrança"),
    ("meaning", "significado", "qual significado explícito ou consolidado foi associado"),
)

RETENTION_SCOPE_AXIS = (
    "momentary", "session", "short_term", "task", "conversation", "project", "medium_term", "long_term", "historical", "archival",
)
RETRIEVAL_MODE_AXIS = (
    "exact", "keyword", "entity", "relation", "temporal", "context", "importance", "project", "conversation", "cross_memory",
)
RELATION_MODE_AXIS = (
    "mentions", "related_to", "part_of", "derived_from", "supports", "contradicts", "precedes", "follows", "same_context", "same_entity",
)
TEMPORAL_SCOPE_AXIS = (
    "current", "recent", "today", "session", "week", "month", "year", "historical", "range", "undated",
)
SOURCE_QUALITY_AXIS = ("unknown", "declared", "observed", "documented", "audited")
CONTEXT_SCOPE_AXIS = ("internal", "conversation", "project", "world")
CONSOLIDATION_STAGE_AXIS = (
    "raw", "indexed", "linked", "contextualized", "reviewed", "summarized", "consolidated", "superseded", "archived", "forgotten_candidate",
)

VARIANT_AXES = (
    ("retention_scope", RETENTION_SCOPE_AXIS),
    ("retrieval_mode", RETRIEVAL_MODE_AXIS),
    ("relation_mode", RELATION_MODE_AXIS),
    ("temporal_scope", TEMPORAL_SCOPE_AXIS),
    ("source_quality", SOURCE_QUALITY_AXIS),
    ("context_scope", CONTEXT_SCOPE_AXIS),
    ("consolidation_stage", CONSOLIDATION_STAGE_AXIS),
)

CANONICAL_NODES = len(MEMORY_BRANCHES) * len(MEMORY_LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in VARIANT_AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE

if len(MEMORY_KINDS) != 10:
    raise RuntimeError("B13 requer exatamente 10 tipos centrais de memória")
if len(MEMORY_BRANCHES) != 50:
    raise RuntimeError(f"B13 requer exatamente 50 ramos; encontrados {len(MEMORY_BRANCHES)}")
if len(MEMORY_LENSES) != 10:
    raise RuntimeError("B13 requer exatamente 10 lentes")
if CANONICAL_NODES != 500:
    raise RuntimeError(f"B13 requer 500 nós canônicos; encontrados {CANONICAL_NODES}")
if VARIANTS_PER_NODE != 2_000_000:
    raise RuntimeError(f"B13 requer 2M variações/nó; encontradas {VARIANTS_PER_NODE}")
if ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError(f"B13 requer 1B endereçáveis; encontrados {ADDRESSABLE_CONTENTS}")


MEMORY_POLICY = {
    "working_memory_persistent_by_default": False,
    "memory_equals_fact": False,
    "retrieval_equals_truth": False,
    "consolidation_overwrites_sources": False,
    "autobiographical_experience_may_be_fabricated": False,
    "autobiographical_experience_requires_reference": True,
    "people_memory_may_infer_sensitive_attributes_automatically": False,
    "memory_grants_operational_authorization": False,
    "continuity_preserves_identity_source": "core.star_identity.py via B12",
    "persistent_store": "existing cognitive_memory table in star.db",
    "relations_store": "shared knowledge_nodes/knowledge_edges",
    "rule": "MEMÓRIA PRESERVA CONTINUIDADE, MAS LEMBRANÇA ≠ FATO E EXPERIÊNCIA AUTOBIOGRÁFICA NÃO PODE SER FABRICADA",
}


def _decode_axes(index: int) -> dict[str, str]:
    index = int(index)
    if not 0 <= index < VARIANTS_PER_NODE:
        raise IndexError(index)
    remainder = index
    decoded: dict[str, str] = {}
    for name, values in reversed(VARIANT_AXES):
        remainder, offset = divmod(remainder, len(values))
        decoded[name] = values[offset]
    if remainder:
        raise RuntimeError("falha ao decodificar variante B13")
    return {name: decoded[name] for name, _ in VARIANT_AXES}


class MemoryCatalog:
    NAMESPACE = "B13"
    PREFIX = "MEM-B13"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "memory_kinds": len(MEMORY_KINDS),
            "branches": len(MEMORY_BRANCHES),
            "lenses_per_branch": len(MEMORY_LENSES),
            "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS,
            "variant_axes": {name: len(values) for name, values in VARIANT_AXES},
            "materialization": "on-demand",
            "prepopulated_memory_rows": 0,
            "truthfulness_note": (
                "1B são representações lógicas de memória, contexto, recuperação e consolidação; "
                "não 1B de lembranças, experiências ou linhas persistidas"
            ),
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        node_index, variant_index = int(node_index), int(variant_index)
        if not 0 <= node_index < CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= variant_index < VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = node_index * VARIANTS_PER_NODE + variant_index + 1
        return f"MEM-B13-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"MEM-B13-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, len(MEMORY_LENSES))
        branch = MEMORY_BRANCHES[branch_index]
        lens_key, lens_label, instruction = MEMORY_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {
            "id": f"MEM-B13-{absolute:010d}",
            "namespace": self.NAMESPACE,
            "memory_kind": branch.kind,
            "memory_kind_label": MEMORY_KIND_LABELS[branch.kind],
            "branch": branch.key,
            "branch_label": branch.label,
            "subtopics": branch.subtopics,
            "lens": lens_key,
            "lens_label": lens_label,
            **axes,
            "prompt": (
                f"{MEMORY_KIND_LABELS[branch.kind]} / {branch.label} / {lens_label}: {instruction}. "
                f"Retenção={axes['retention_scope']}; recuperação={axes['retrieval_mode']}; relação={axes['relation_mode']}; "
                f"tempo={axes['temporal_scope']}; fonte={axes['source_quality']}; contexto={axes['context_scope']}; "
                f"consolidação={axes['consolidation_stage']}. Preservar fonte, incerteza e contexto; "
                "lembrança não vira fato automaticamente e working memory não é persistida por padrão."
            ),
        }


class WorkingMemoryBuffer:
    """Buffer pequeno e bounded. Não persiste automaticamente no banco."""

    def __init__(self, max_items: int = 64):
        self.max_items = max(8, min(int(max_items), 512))
        self._items: deque[dict] = deque(maxlen=self.max_items)
        self._next_id = 1

    def add(
        self,
        content: str,
        *,
        key: str = "",
        importance: float = 0.5,
        context: dict | None = None,
        entities: Iterable[str] | None = None,
        source: str = "runtime",
        metadata: dict | None = None,
    ) -> dict:
        content = _clean(content)
        source = _clean(source)
        if not content or not source:
            raise ValueError("working memory requer conteúdo e fonte")
        item = {
            "working_id": f"WM-{self._next_id:08d}",
            "key": _clean(key),
            "content": content,
            "importance": _clamp(importance),
            "context": deepcopy(context or {}),
            "entities": tuple(_clean(x) for x in (entities or ()) if _clean(x)),
            "source": source,
            "metadata": deepcopy(metadata or {}),
            "created_at": _now(),
            "persistent": False,
        }
        self._next_id += 1
        if item["key"]:
            self._items = deque((x for x in self._items if x.get("key") != item["key"]), maxlen=self.max_items)
        self._items.append(item)
        return deepcopy(item)

    def list(self, *, limit: int | None = None) -> list[dict]:
        items = list(self._items)
        if limit is not None:
            items = items[-max(0, int(limit)):]
        return deepcopy(items)

    def get(self, key: str) -> dict | None:
        key = _clean(key)
        for item in reversed(self._items):
            if item.get("key") == key or item.get("working_id") == key:
                return deepcopy(item)
        return None

    def remove(self, key_or_id: str) -> bool:
        value = _clean(key_or_id)
        before = len(self._items)
        self._items = deque(
            (item for item in self._items if item.get("key") != value and item.get("working_id") != value),
            maxlen=self.max_items,
        )
        return len(self._items) != before

    def clear(self) -> None:
        self._items.clear()

    def search(self, query: str, *, limit: int = 10) -> list[dict]:
        tokens = [token for token in re.findall(r"[\wÀ-ÿ]+", _clean(query).casefold()) if len(token) > 1]
        scored = []
        for index, item in enumerate(self._items):
            haystack = f"{item['content']} {' '.join(item['entities'])} {item['context']}".casefold()
            overlap = sum(1 for token in tokens if token in haystack)
            if tokens and not overlap:
                continue
            score = overlap + item["importance"] + (index / max(1, len(self._items))) * 0.1
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return deepcopy([item for _, item in scored[: max(1, min(int(limit), 100))]])


class MemoryContinuity:
    """Orquestra tipos de memória sobre stores oficiais e o grafo compartilhado."""

    NAMESPACE = "B13"
    TAXONOMY_ROOT_ID = "MEMORY-TAX-ROOT"

    def __init__(
        self,
        knowledge: UniversalKnowledgeArchitecture,
        *,
        memory,
        graph=None,
        projects=None,
        self_model=None,
        working_memory: WorkingMemoryBuffer | None = None,
    ):
        self.knowledge = knowledge
        self.memory = memory
        self.graph = graph or knowledge.graph
        self.projects = projects
        self.self_model = self_model
        self.working = working_memory or WorkingMemoryBuffer()
        self.catalog = MemoryCatalog()
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 13 — MEMÓRIA E CONTINUIDADE",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/memory_continuity.py",
            metadata={
                "materialization": "on-demand",
                "persistent_store": "cognitive_memory",
                "working_memory": "bounded transient buffer",
                "relations": "shared knowledge graph",
                "canonical_gate": "BLOCO 2 -> BLOCO 3",
                "autobiographical_source": "B12 SelfHistory when explicitly imported",
                "parallel_database": False,
                "parallel_graph": False,
            },
        )

    @staticmethod
    def _kind(value: str) -> str:
        aliases = {
            "working_memory": "working", "trabalho": "working",
            "episodic_memory": "episodic", "episodica": "episodic",
            "semantic_memory": "semantic", "semantica": "semantic",
            "conversation_memory": "conversation", "conversa": "conversation",
            "project_memory": "project", "projeto": "project",
            "people_memory": "people", "pessoas": "people",
            "object_memory": "object", "objetos": "object",
            "social_memory": "social", "social": "social",
            "autobiographical_memory": "autobiographical", "autobiografica": "autobiographical",
            "temporal_memory": "temporal", "temporal": "temporal",
        }
        normalized = _norm(value)
        kind = aliases.get(normalized, normalized)
        if kind not in MEMORY_KINDS:
            raise ValueError(f"tipo de memória B13 inválido: {value}")
        return kind

    @staticmethod
    def _memory_node_id(memory_id: int) -> str:
        return f"MEMORY-ENTRY-{int(memory_id):010d}"

    def _ensure_memory_graph_node(self, record: dict) -> str:
        memory_id = int(record["id"])
        node_id = self._memory_node_id(memory_id)
        metadata = deepcopy(record.get("metadata") or {})
        self.graph.add_entity(
            "memory_entry",
            _clean(record.get("content"))[:160] or f"Memory {memory_id}",
            node_id=node_id,
            confidence=float(metadata.get("confidence", 1.0)),
            data={
                "block": "B13",
                "memory_id": memory_id,
                "kind": record.get("kind"),
                "importance": record.get("importance"),
                "source": metadata.get("source"),
                "reference": metadata.get("reference"),
                "occurred_at": metadata.get("occurred_at"),
                "canonical_knowledge": False,
            },
        )
        return node_id

    def _link_metadata(self, memory_id: int, metadata: dict) -> None:
        memory_node = self._memory_node_id(memory_id)
        for entity in metadata.get("entities", ()):
            entity_id = self.graph.add_entity(
                "memory_entity", entity,
                data={"block": "B13", "source": "memory metadata"},
            )
            self.graph.relate(memory_node, entity_id, "mentions", metadata={"block": "B13"})
        location = _clean(metadata.get("location"))
        if location:
            location_id = self.graph.add_entity("place", location, data={"block": "B13", "source": "memory metadata"})
            self.graph.relate(memory_node, location_id, "occurred_at_place", metadata={"block": "B13"})
        occurred_at = _clean(metadata.get("occurred_at"))
        if occurred_at:
            time_id = self.graph.add_entity("temporal_anchor", occurred_at, data={"block": "B13"})
            self.graph.relate(memory_node, time_id, "occurred_at", metadata={"block": "B13"})
        for relation in metadata.get("relations", ()):
            if not isinstance(relation, dict):
                continue
            rel = _clean(relation.get("relation")) or "related_to"
            target_memory_id = relation.get("target_memory_id")
            if target_memory_id is not None:
                self.graph.relate(memory_node, self._memory_node_id(int(target_memory_id)), rel, metadata={"block": "B13"})
                continue
            target = _clean(relation.get("target"))
            if target:
                target_type = _clean(relation.get("target_type")) or "memory_relation_target"
                target_id = self.graph.add_entity(target_type, target, data={"block": "B13"})
                self.graph.relate(memory_node, target_id, rel, metadata={"block": "B13"})

    def remember(
        self,
        kind: str,
        content: str,
        *,
        source: str,
        reference: str = "",
        occurred_at: str | None = None,
        entities: Iterable[str] | None = None,
        relations: Iterable[dict] | None = None,
        location: str = "",
        importance: float = 0.5,
        context: dict | None = None,
        experience: bool = False,
        meaning: str = "",
        key: str | None = None,
        confidence: float = 1.0,
        metadata: dict | None = None,
        persist_working: bool = False,
    ) -> dict:
        kind = self._kind(kind)
        content, source, reference = _clean(content), _clean(source), _clean(reference)
        if not content or not source:
            raise ValueError("memória requer conteúdo e fonte")
        if (experience or kind == "autobiographical") and not reference:
            raise ValueError("memória autobiográfica/experiência exige referência auditável")
        meta = deepcopy(metadata or {})
        meta.update({
            "block": "B13",
            "source": source,
            "reference": reference,
            "occurred_at": _clean(occurred_at) or _now(),
            "entities": [_clean(item) for item in (entities or ()) if _clean(item)],
            "relations": [deepcopy(item) for item in (relations or ()) if isinstance(item, dict)],
            "location": _clean(location),
            "context": deepcopy(context or {}),
            "experience": bool(experience),
            "meaning": _clean(meaning),
            "confidence": _clamp(confidence),
            "canonical_knowledge": False,
            "fabricated": False,
        })
        if kind == "people":
            meta["sensitive_attribute_inference"] = False
        if kind == "autobiographical":
            meta["identity_source"] = "B12/core.star_identity"

        working_item = None
        if kind == "working":
            working_item = self.working.add(
                content,
                key=key or "",
                importance=importance,
                context=context,
                entities=entities,
                source=source,
                metadata=meta,
            )
            if not persist_working:
                return {
                    "kind": "working",
                    "working": working_item,
                    "persistent": False,
                    "policy": "working memory is transient unless explicitly persisted",
                }

        memory_id = self.memory.remember(kind, content, key=key, metadata=meta, importance=_clamp(importance))
        record = self.memory.store.memory_by_id(memory_id)
        if record is None:
            raise RuntimeError("memória persistida não pôde ser relida")
        memory_node = self._ensure_memory_graph_node(record)
        self._link_metadata(memory_id, meta)
        return {
            "memory_id": memory_id,
            "memory_node_id": memory_node,
            "kind": kind,
            "persistent": True,
            "working": working_item,
            "record": record,
        }

    def memory_record(self, memory_id: int) -> dict | None:
        return self.memory.store.memory_by_id(int(memory_id))

    def relate_memories(self, source_memory_id: int, target_memory_id: int, relation: str, *, weight: float = 1.0, metadata=None) -> dict:
        relation = _clean(relation)
        if not relation:
            raise ValueError("relação de memória vazia")
        source = self.memory_record(source_memory_id)
        target = self.memory_record(target_memory_id)
        if source is None or target is None:
            raise KeyError("memória de origem/destino inexistente")
        source_node = self._ensure_memory_graph_node(source)
        target_node = self._ensure_memory_graph_node(target)
        self.graph.relate(source_node, target_node, relation, weight=float(weight), metadata={"block": "B13", **dict(metadata or {})})
        return {"source_memory_id": int(source_memory_id), "target_memory_id": int(target_memory_id), "relation": relation, "weight": float(weight)}

    def recall(self, query: str, *, kinds: Iterable[str] | None = None, limit: int = 10, include_working: bool = True) -> list[dict]:
        normalized_kinds = tuple(self._kind(kind) for kind in (kinds or ()))
        limit = max(1, min(int(limit), 100))
        persistent = self.memory.recall(query, kinds=normalized_kinds or None, limit=limit)
        ranked = [{**item, "storage": "persistent"} for item in persistent]
        if include_working and (not normalized_kinds or "working" in normalized_kinds):
            for item in self.working.search(query, limit=limit):
                ranked.append({
                    "id": None,
                    "kind": "working",
                    "memory_key": item.get("key"),
                    "content": item["content"],
                    "importance": item["importance"],
                    "created_at": item["created_at"],
                    "updated_at": item["created_at"],
                    "metadata": deepcopy(item.get("metadata") or {}),
                    "storage": "working",
                    "working_id": item["working_id"],
                })
        ranked.sort(key=lambda item: (float(item.get("importance", 0.0)), str(item.get("updated_at", ""))), reverse=True)
        return ranked[:limit]

    def consolidate(
        self,
        memory_ids: Iterable[int],
        summary: str,
        *,
        source: str,
        reference: str,
        meaning: str = "",
        importance: float = 0.7,
    ) -> dict:
        ids = tuple(dict.fromkeys(int(item) for item in memory_ids))
        if len(ids) < 2:
            raise ValueError("consolidação exige ao menos duas memórias")
        records = [self.memory_record(memory_id) for memory_id in ids]
        if any(record is None for record in records):
            raise KeyError("consolidação referencia memória inexistente")
        result = self.remember(
            "semantic",
            summary,
            source=source,
            reference=reference,
            importance=importance,
            meaning=meaning,
            context={"consolidated_from": list(ids)},
            metadata={"consolidation": True, "consolidated_from": list(ids)},
        )
        for source_id in ids:
            self.relate_memories(result["memory_id"], source_id, "derived_from")
        return {**result, "consolidated_from": list(ids), "source_memories_preserved": True}

    def remember_self_event(self, event: dict) -> dict:
        if not isinstance(event, dict):
            raise TypeError("evento do SelfHistory deve ser dict")
        summary = _clean(event.get("summary"))
        source = _clean(event.get("source"))
        reference = _clean(event.get("reference"))
        if not summary or not source:
            raise ValueError("evento autobiográfico requer summary e source")
        return self.remember(
            "autobiographical",
            summary,
            source=source,
            reference=reference,
            occurred_at=event.get("occurred_at"),
            experience=bool(event.get("is_experience")),
            confidence=float(event.get("confidence", 1.0)),
            context={"self_history_event_id": event.get("event_id"), "event_type": event.get("event_type")},
            metadata={"imported_from_b12_self_history": True},
        )

    def continuity_snapshot(self) -> dict:
        counts = self.memory.store.memory_counts()
        self_history_count = None
        if self.self_model is not None:
            history = getattr(self.self_model, "history", None)
            if history is not None and hasattr(history, "list"):
                self_history_count = len(history.list())
        return {
            "block": "B13",
            "persistent_memory": counts,
            "working_memory_items": len(self.working.list()),
            "b12_self_history_events": self_history_count,
            "identity_continuity_source": "B12 Self Model / official identity",
            "memory_is_fact": False,
            "autobiographical_memory_fabricated": False,
            "operational_authorization": False,
        }

    @staticmethod
    def _branch(key: str) -> MemoryBranch:
        key = _norm(key)
        for branch in MEMORY_BRANCHES:
            if branch.key == key:
                return branch
        raise KeyError(key)

    @staticmethod
    def _kind_node_id(kind: str) -> str:
        return f"MEMORY-KIND-{kind.upper()}"

    @staticmethod
    def _branch_node_id(branch: str) -> str:
        return f"MEMORY-BR-{branch.upper()}"

    def taxonomy_snapshot(self, kind: str | None = None) -> dict:
        kind_key = self._kind(kind) if kind else None
        selected = [branch for branch in MEMORY_BRANCHES if kind_key is None or branch.kind == kind_key]
        return {
            "root": "MEMÓRIA E CONTINUIDADE",
            "kind": kind_key,
            "branches": [
                {"kind": branch.kind, "kind_label": MEMORY_KIND_LABELS[branch.kind], "branch": branch.key, "branch_label": branch.label, "subtopics": list(branch.subtopics)}
                for branch in selected
            ],
            "lenses": [item[0] for item in MEMORY_LENSES],
            "policy": deepcopy(MEMORY_POLICY),
        }

    def _ensure_taxonomy_path(self, branch: MemoryBranch) -> dict:
        root = self.graph.add_entity(
            "memory_taxonomy", "MEMÓRIA E CONTINUIDADE",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B13", "source": "core/memory_continuity.py"},
        )
        b12_id = self.graph.add_entity(
            "memory_continuity_source", "SELF MODEL / Self History",
            node_id="MEMORY-SOURCE-B12",
            data={"block": "B12", "source": "core/self_model.py"},
        )
        mind_id = self.graph.add_entity(
            "memory_cognitive_source", "CognitiveMemory",
            node_id="MEMORY-SOURCE-MIND",
            data={"source": "core/mind.py::CognitiveMemory"},
        )
        self.graph.relate(root, b12_id, "extends_continuity", metadata={"block": "B13"})
        self.graph.relate(root, mind_id, "uses", metadata={"block": "B13"})
        kind_id = self._kind_node_id(branch.kind)
        self.graph.add_entity("memory_kind", MEMORY_KIND_LABELS[branch.kind], node_id=kind_id, data={"block": "B13", "kind": branch.kind})
        self.graph.relate(root, kind_id, "has_part", metadata={"block": "B13", "taxonomy": True})
        branch_id = self._branch_node_id(branch.key)
        self.graph.add_entity("memory_branch", branch.label, node_id=branch_id, data={"block": "B13", "kind": branch.kind, "branch": branch.key})
        self.graph.relate(kind_id, branch_id, "has_part", metadata={"block": "B13", "taxonomy": True})
        return {"root_id": root, "kind_id": kind_id, "branch_id": branch_id}

    def materialize_taxonomy(self, kind: str | None = None) -> dict:
        kind_key = self._kind(kind) if kind else None
        selected = [branch for branch in MEMORY_BRANCHES if kind_key is None or branch.kind == kind_key]
        paths = [self._ensure_taxonomy_path(branch) for branch in selected]
        return {
            "kind": kind_key,
            "branches_materialized": len(paths),
            "knowledge_graph": "shared",
            "parallel_memory_graph_created": False,
            "paths": paths,
        }

    def promote_canonical_memory_knowledge(
        self,
        record_id: str,
        canonical_label: str,
        *,
        memory_kind: str,
        branch: str,
        knowledge_type: str = "concept",
        aliases=None,
        properties=None,
        summary: str = "",
    ) -> dict:
        kind = self._kind(memory_kind)
        branch_obj = self._branch(branch)
        if branch_obj.kind != kind:
            raise ValueError(f"ramo {branch} não pertence a {kind}")
        props = dict(properties or {})
        props.update({
            "memory_is_fact": False,
            "runtime_memory_is_canonical_by_default": False,
            "knowledge_scope": "memory_architecture",
        })
        result = self.knowledge.promote_canonical(
            record_id,
            canonical_label,
            knowledge_type=knowledge_type,
            namespace=self.NAMESPACE,
            summary=summary,
            aliases=aliases,
            properties=props,
            categories=["memory", kind, branch_obj.key],
            provenance={"memory_block": "B13", "memory_kind": kind, "branch": branch_obj.key, "source_record_id": record_id},
        )
        taxonomy = self._ensure_taxonomy_path(branch_obj)
        self.graph.relate(result["knowledge_id"], taxonomy["branch_id"], "is_a", metadata={"block": "B13"})
        return result

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "memory_kinds": list(MEMORY_KINDS),
            "persistent_store": "cognitive_memory",
            "working_memory": {"bounded": True, "max_items": self.working.max_items, "persistent_by_default": False},
            "knowledge_graph": "shared knowledge_nodes/knowledge_edges",
            "parallel_database": False,
            "parallel_graph": False,
            "policy": deepcopy(MEMORY_POLICY),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {"status bloco 13", "status memoria", "status memória", "memoria e continuidade", "memória e continuidade"}:
            stats = self.stats()
            counts = self.continuity_snapshot()["persistent_memory"]
            return (
                f"⭐ BLOCO 13 — MEMÓRIA E CONTINUIDADE: {stats['catalog']['addressable_contents']} conteúdos endereçáveis em B13 | "
                f"10 tipos × 5 ramos/tipo × 10 lentes = {stats['catalog']['canonical_nodes']} nós | "
                f"persistidas={counts['total']} | working={len(self.working.list())} | store=cognitive_memory."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"⭐ {item['id']} — {item['memory_kind_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        match = re.match(r"^(?:taxonomia memoria|taxonomia memória)(?:\s+(.+))?$", raw, re.I)
        if match:
            snapshot = self.taxonomy_snapshot(match.group(1))
            labels = ", ".join(item["branch_label"] for item in snapshot["branches"][:12])
            return f"⭐ Taxonomia B13: {len(snapshot['branches'])} ramos. {labels}{'…' if len(snapshot['branches']) > 12 else ''}"
        if low in {"continuidade da star", "status continuidade", "status da continuidade"}:
            snapshot = self.continuity_snapshot()
            return (
                f"⭐ Continuidade B13: {snapshot['persistent_memory']['total']} memórias persistidas, "
                f"{snapshot['working_memory_items']} itens em working memory. Lembrança ≠ fato; autobiografia não é fabricada."
            )
        return None
