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


def test_hero_catalog_tabs_do_not_invent_missing_data():
    from gui.heroes_view import hero_tab_text

    entity = Entity(
        name="Test Hero",
        category="character",
        universe="Marvel",
        publisher="Marvel Comics",
        powers=["Flight"],
    )

    info = hero_tab_text(entity, "info")
    biography = hero_tab_text(entity, "biography")
    appearances = hero_tab_text(entity, "appearances")

    assert "NOME DE HERÓI: Test Hero" in info
    assert "PODERES: Flight" in info
    assert "NOME REAL: —" in info
    assert "AINDA NÃO INDEXADA" in biography
    assert "AINDA NÃO INDEXADAS" in appearances


def test_hero_catalog_statistics_only_use_explicit_0_to_10_values():
    from gui.heroes_view import hero_statistic_value, statistic_bar

    entity = Entity(
        name="Stats Hero",
        category="character",
        attributes={
            "statistics": {
                "strength": 8,
                "defense": "50%",
                "speed": 90,
            }
        },
    )

    assert hero_statistic_value(entity, ("strength",)) == 8
    assert hero_statistic_value(entity, ("defense",)) == 5
    assert hero_statistic_value(entity, ("speed",)) is None
    assert statistic_bar(None) == "—"
    assert len(statistic_bar(10)) == 7


def test_full_hero_profile_preserves_image_attribution_and_complementary_fields():
    from gui.heroes_view import full_profile_text, image_credit_text

    entity = Entity(
        name="Credit Hero",
        category="character",
        original_name="Original Credit Hero",
        gender="female",
        occupation=["Reporter"],
        metadata={
            "image_attribution": {
                "cache/hero.png": {
                    "author": "Example Artist",
                    "license": "CC BY 4.0",
                    "source_url": "https://example.test/hero",
                }
            }
        },
    )

    profile = full_profile_text(entity)
    credit = image_credit_text(entity, "cache/hero.png")

    assert "NOME ORIGINAL: Original Credit Hero" in profile
    assert "GÊNERO: female" in profile
    assert "OCUPAÇÃO: Reporter" in profile
    assert "CRÉDITOS DE IMAGEM" in profile
    assert "Example Artist" in credit
    assert "CC BY 4.0" in credit


def test_full_profile_displays_field_provenance():
    from gui.heroes_view import full_profile_text

    entity = Entity(
        name="Provenance Hero",
        category="character",
        universe="Marvel",
        powers=["Flight"],
        metadata={
            "field_provenance": {
                "powers": [
                    {
                        "source_type": "official_web",
                        "source_ref": "Marvel Comics",
                        "url": "https://www.marvel.com/characters/provenance-hero",
                    }
                ]
            }
        },
    )

    profile = full_profile_text(entity)
    assert "PROVENIÊNCIA POR CAMPO" in profile
    assert "POWERS: Marvel Comics" in profile
    assert "https://www.marvel.com/characters/provenance-hero" in profile


def test_appearances_tab_renders_indexed_titles():
    from gui.heroes_view import hero_tab_text

    entity = Entity(
        name="Appearance Hero",
        category="character",
        first_appearance="Hero #1",
        attributes={"appearances": ["Hero #1", "Hero #2"]},
    )

    text = hero_tab_text(entity, "appearances")

    assert "APARIÇÕES INDEXADAS" in text
    assert "Hero #1, Hero #2" in text
    assert "PRIMEIRA APARIÇÃO: Hero #1" in text
