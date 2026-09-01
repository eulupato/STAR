"""Entidades genéricas da STAR Knowledge V3."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class KnowledgeSource:
    source_type: str
    source_ref: str
    page: int | None = None
    url: str | None = None
    retrieved_at: str | None = None
    field_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Relationship:
    predicate: str
    target_name: str
    target_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Entity:
    name: str
    category: str
    id: str = field(default_factory=lambda: uuid4().hex)
    original_name: str | None = None
    aliases: list[str] = field(default_factory=list)
    universe: str | None = None
    publisher: str | None = None
    team: list[str] = field(default_factory=list)
    species: str | None = None
    gender: str | None = None
    origin: str | None = None
    origin_place: str | None = None
    occupation: list[str] = field(default_factory=list)
    affiliations: list[str] = field(default_factory=list)
    status: str | None = None
    first_appearance: str | None = None
    creators: list[str] = field(default_factory=list)
    description: str | None = None
    personality: str | None = None
    history_summary: str | None = None
    powers: list[str] = field(default_factory=list)
    abilities: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    equipment: list[str] = field(default_factory=list)
    weapons: list[str] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    image: str | None = None
    tags: list[str] = field(default_factory=list)
    sources: list[KnowledgeSource] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data
