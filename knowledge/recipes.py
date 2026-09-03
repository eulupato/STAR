"""Livro de receitas local da STAR.

A GUI apenas consome RecipeBook. Arquivos do usuário podem ser JSON, Markdown
ou texto simples e permanecem locais.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re

from knowledge.store import normalize_search_text


@dataclass(frozen=True)
class Recipe:
    name: str
    ingredients: tuple[str, ...] = field(default_factory=tuple)
    steps: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    source: str | None = None


class RecipeBook:
    SUPPORTED = {".json", ".md", ".txt"}

    def __init__(self, root: str | Path):
        self.root = Path(root)

    @staticmethod
    def _items(value) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            values = value.splitlines()
        elif isinstance(value, (list, tuple)):
            values = value
        else:
            values = [value]
        result = []
        for raw in values:
            text = str(raw).strip()
            if text:
                result.append(text)
        return tuple(result)

    @classmethod
    def _from_mapping(cls, data: dict, source: Path) -> Recipe | None:
        name = str(
            data.get("name")
            or data.get("title")
            or data.get("nome")
            or ""
        ).strip()
        if not name:
            return None

        ingredients = cls._items(
            data.get("ingredients")
            or data.get("ingredientes")
        )
        steps = cls._items(
            data.get("steps")
            or data.get("instructions")
            or data.get("preparation")
            or data.get("preparo")
            or data.get("modo_de_preparo")
        )
        notes = cls._items(data.get("notes") or data.get("notas"))
        tags = cls._items(data.get("tags"))

        if not ingredients and not steps:
            return None
        return Recipe(
            name=name,
            ingredients=ingredients,
            steps=steps,
            notes=notes,
            tags=tags,
            source=str(source),
        )

    @classmethod
    def _load_json(cls, path: Path) -> list[Recipe]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("recipes"), list):
            items = data["recipes"]
        elif isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = [data]
        else:
            return []

        result = []
        for item in items:
            if not isinstance(item, dict):
                continue
            recipe = cls._from_mapping(item, path)
            if recipe is not None:
                result.append(recipe)
        return result

    @classmethod
    def _load_text(cls, path: Path) -> list[Recipe]:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines:
            return []

        name = path.stem.replace("_", " ").strip().title()
        ingredients = []
        steps = []
        notes = []
        section = None

        for raw in lines:
            line = raw.strip()
            if not line:
                continue

            if line.startswith("#"):
                heading = line.lstrip("#").strip()
                normalized_heading = normalize_search_text(heading.rstrip(":"))
                if normalized_heading in {"ingredientes", "ingredients"}:
                    section = "ingredients"
                    continue
                if normalized_heading in {
                    "preparo",
                    "modo de preparo",
                    "instrucoes",
                    "instructions",
                    "steps",
                    "passos",
                }:
                    section = "steps"
                    continue
                if normalized_heading in {"notas", "notes", "observacoes"}:
                    section = "notes"
                    continue
                if section is None and heading:
                    name = heading
                    continue

            normalized = normalize_search_text(line.rstrip(":"))
            if normalized in {"ingredientes", "ingredients"}:
                section = "ingredients"
                continue
            if normalized in {
                "preparo",
                "modo de preparo",
                "instrucoes",
                "instructions",
                "steps",
                "passos",
            }:
                section = "steps"
                continue
            if normalized in {"notas", "notes", "observacoes"}:
                section = "notes"
                continue

            item = re.sub(r"^[-*•]\s*", "", line)
            item = re.sub(r"^\d+[.)]\s*", "", item).strip()
            if not item:
                continue
            if section == "ingredients":
                ingredients.append(item)
            elif section == "steps":
                steps.append(item)
            elif section == "notes":
                notes.append(item)

        if not ingredients and not steps:
            return []
        return [
            Recipe(
                name=name,
                ingredients=tuple(ingredients),
                steps=tuple(steps),
                notes=tuple(notes),
                source=str(path),
            )
        ]

    def load(self) -> list[Recipe]:
        if not self.root.exists():
            return []

        recipes = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in self.SUPPORTED:
                continue
            try:
                if path.suffix.lower() == ".json":
                    recipes.extend(self._load_json(path))
                else:
                    recipes.extend(self._load_text(path))
            except (OSError, json.JSONDecodeError):
                continue

        unique = {}
        for recipe in recipes:
            key = normalize_search_text(recipe.name)
            if key:
                unique[key] = recipe
        return sorted(unique.values(), key=lambda item: item.name.casefold())

    def search(self, query: str) -> list[Recipe]:
        recipes = self.load()
        q = normalize_search_text(query)
        if not q:
            return recipes
        tokens = q.split()
        result = []
        for recipe in recipes:
            haystack = normalize_search_text(
                " ".join(
                    [
                        recipe.name,
                        *recipe.ingredients,
                        *recipe.tags,
                    ]
                )
            )
            if all(token in haystack for token in tokens):
                result.append(recipe)
        return result



class RecipeSession:
    """Estado simples para acompanhar o preparo passo a passo."""

    def __init__(self, recipe: Recipe):
        self.recipe = recipe
        self.index = 0

    @property
    def total(self) -> int:
        return len(self.recipe.steps)

    @property
    def current(self) -> str | None:
        if not self.recipe.steps:
            return None
        return self.recipe.steps[self.index]

    @property
    def position(self) -> int:
        return 0 if self.total == 0 else self.index + 1

    @property
    def finished(self) -> bool:
        return self.total > 0 and self.index == self.total - 1

    def next(self) -> str | None:
        if self.total == 0:
            return None
        if self.index < self.total - 1:
            self.index += 1
        return self.current

    def previous(self) -> str | None:
        if self.total == 0:
            return None
        if self.index > 0:
            self.index -= 1
        return self.current

    def reset(self) -> str | None:
        self.index = 0
        return self.current
