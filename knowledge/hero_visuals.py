"""Tema visual e referências de imagem para a Ilha dos Heróis.

A paleta é tratada como dado de apresentação. Personagens com identidade visual
muito conhecida podem ter override explícito em marvel_themes.json. Todos os
outros recebem uma paleta derivada da imagem local, sem acesso à rede durante a
renderização.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path

from PIL import Image

from knowledge.store import normalize_search_text

THEME_FILE = Path(__file__).resolve().parent / "packs" / "heroes" / "marvel_themes.json"


@dataclass(frozen=True)
class HeroTheme:
    background: str = "#10151D"
    panel: str = "#17202B"
    accent: str = "#6FA8FF"
    accent_secondary: str = "#D9E7FF"
    text: str = "#F4F7FB"
    muted: str = "#AAB5C4"

    def to_dict(self) -> dict[str, str]:
        return {
            "background": self.background,
            "panel": self.panel,
            "accent": self.accent,
            "accent_secondary": self.accent_secondary,
            "text": self.text,
            "muted": self.muted,
        }


@lru_cache(maxsize=1)
def _theme_overrides() -> dict[str, HeroTheme]:
    if not THEME_FILE.exists():
        return {}
    try:
        raw = json.loads(THEME_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    result = {}
    for name, data in raw.items():
        if not isinstance(data, dict):
            continue
        key = normalize_search_text(name)
        if not key:
            continue
        try:
            result[key] = HeroTheme(**data)
        except TypeError:
            continue
    return result


def _mix(hex_color: str, target: tuple[int, int, int], factor: float) -> str:
    value = hex_color.lstrip("#")
    if len(value) != 6:
        value = "6FA8FF"
    rgb = tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    mixed = tuple(
        max(0, min(255, round(channel * (1 - factor) + goal * factor)))
        for channel, goal in zip(rgb, target)
    )
    return "#" + "".join(f"{channel:02X}" for channel in mixed)


@lru_cache(maxsize=512)
def _image_colors(path_value: str, mtime_ns: int) -> tuple[str, str] | None:
    del mtime_ns
    path = Path(path_value)
    if not path.exists() or not path.is_file():
        return None

    try:
        with Image.open(path) as source:
            image = source.convert("RGB")
            image.thumbnail((96, 96), Image.Resampling.BILINEAR)
            quantized = image.quantize(colors=10)
            palette = quantized.getpalette() or []
            colors = quantized.getcolors(maxcolors=4096) or []
    except (OSError, ValueError):
        return None

    ranked = []
    for count, index in sorted(colors, reverse=True):
        start = index * 3
        if start + 2 >= len(palette):
            continue
        rgb = tuple(palette[start:start + 3])
        brightness = sum(rgb) / 3
        spread = max(rgb) - min(rgb)
        if brightness < 28 or brightness > 232:
            continue
        score = count * (1.0 + spread / 255)
        ranked.append((score, rgb))

    if not ranked:
        return None

    primary = ranked[0][1]
    secondary = ranked[1][1] if len(ranked) > 1 else primary
    to_hex = lambda rgb: "#" + "".join(f"{int(v):02X}" for v in rgb)
    return to_hex(primary), to_hex(secondary)


def visual_references(entity) -> list[str]:
    """Retorna imagens locais válidas, deduplicadas, na ordem de prioridade."""
    candidates = []
    if getattr(entity, "image", None):
        candidates.append(entity.image)

    metadata = getattr(entity, "metadata", {}) or {}
    attributes = getattr(entity, "attributes", {}) or {}
    candidates.extend(metadata.get("image_candidates", []) or [])
    candidates.extend(attributes.get("visual_references", []) or [])

    result = []
    seen = set()
    for value in candidates:
        if not value:
            continue
        path = Path(str(value))
        try:
            key = str(path.resolve())
        except OSError:
            key = str(path)
        if key in seen or not path.exists() or not path.is_file():
            continue
        seen.add(key)
        result.append(str(path))
    return result


def _identity_keys(entity) -> list[str]:
    keys = []
    values = [
        getattr(entity, "name", ""),
        getattr(entity, "original_name", ""),
        *((getattr(entity, "aliases", None) or [])),
    ]
    real_name = (getattr(entity, "attributes", {}) or {}).get("real_name")
    if real_name:
        values.append(real_name)

    for value in values:
        key = normalize_search_text(value)
        if key and key not in keys:
            keys.append(key)
    return keys


def theme_for_entity(entity) -> HeroTheme:
    """Resolve tema explícito, override icônico ou paleta derivada da imagem."""
    attributes = getattr(entity, "attributes", {}) or {}
    explicit = attributes.get("theme")
    if isinstance(explicit, dict):
        try:
            return HeroTheme(**explicit)
        except TypeError:
            pass

    overrides = _theme_overrides()
    keys = _identity_keys(entity)

    if "miles morales" in keys and any("spider man" in key for key in keys):
        miles = overrides.get(normalize_search_text("Spider-Man (Miles Morales)"))
        if miles:
            return miles

    for key in keys:
        if key in overrides:
            return overrides[key]

    for key in keys:
        for override_key, theme in overrides.items():
            if len(override_key) >= 5 and (
                f" {override_key} " in f" {key} "
                or f" {key} " in f" {override_key} "
            ):
                return theme

    refs = visual_references(entity)
    if refs:
        path = Path(refs[0])
        try:
            colors = _image_colors(str(path), path.stat().st_mtime_ns)
        except OSError:
            colors = None
        if colors:
            accent, secondary = colors
            return HeroTheme(
                background=_mix(accent, (8, 12, 18), 0.78),
                panel=_mix(accent, (18, 24, 34), 0.68),
                accent=_mix(accent, (255, 255, 255), 0.08),
                accent_secondary=_mix(secondary, (255, 255, 255), 0.18),
                text="#F7F8FB",
                muted="#C4CBD6",
            )

    universe = normalize_search_text(getattr(entity, "universe", "") or "")
    if universe == "marvel":
        return HeroTheme(
            background="#140E11",
            panel="#21151A",
            accent="#E62429",
            accent_secondary="#F4D4D6",
        )
    return HeroTheme()
