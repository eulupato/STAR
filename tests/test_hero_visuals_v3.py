from pathlib import Path

from PIL import Image

from knowledge.entities import Entity
from knowledge.hero_visuals import theme_for_entity, visual_references


def test_iconic_themes_match_requested_examples():
    black_panther = Entity(name="Black Panther", category="character", universe="Marvel")
    miles = Entity(
        name="Spider-Man (Miles Morales)",
        category="character",
        universe="Marvel",
        attributes={"real_name": "Miles Morales"},
    )
    loki = Entity(name="Loki", category="character", universe="Marvel")

    assert theme_for_entity(black_panther).accent.upper() == "#8E5BFF"
    assert theme_for_entity(miles).accent.upper() == "#E62429"
    assert theme_for_entity(loki).accent.upper() == "#2FA45A"
    assert theme_for_entity(loki).accent_secondary.upper() == "#E5C75A"


def test_visual_references_are_local_and_deduplicated(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    Image.new("RGB", (8, 8), (40, 20, 90)).save(first)
    Image.new("RGB", (8, 8), (180, 30, 40)).save(second)

    entity = Entity(
        name="Hero",
        category="character",
        image=str(first),
        metadata={
            "image_candidates": [str(first), str(second), str(first)],
        },
    )

    refs = visual_references(entity)
    assert refs == [str(first), str(second)]


def test_unknown_character_derives_theme_from_image(tmp_path):
    image_path = Path(tmp_path) / "hero.png"
    Image.new("RGB", (30, 30), (35, 120, 190)).save(image_path)

    entity = Entity(
        name="Character Without Override",
        category="character",
        universe="Marvel",
        image=str(image_path),
    )
    theme = theme_for_entity(entity)
    assert theme.accent.startswith("#")
    assert theme.panel.startswith("#")
    assert theme.accent != "#E62429"
