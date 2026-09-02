from pathlib import Path

from knowledge.entities import Entity
from knowledge.sources.wikidata import (
    WikidataProfile,
    format_short_description,
    merge_wikidata_profile,
    score_candidate,
)


def test_wikidata_candidate_requires_matching_publisher():
    spider = Entity(
        name="Spider-Man (Miles Morales)",
        category="character",
        universe="Marvel",
        publisher="Marvel Comics",
        attributes={"real_name": "Miles Morales"},
    )
    good = {
        "label": "Miles Morales",
        "description": "fictional superhero appearing in Marvel Comics",
        "aliases": ["Spider-Man"],
    }
    wrong = {
        "label": "Miles Morales",
        "description": "fictional superhero from DC Comics",
        "aliases": ["Spider-Man"],
    }

    assert score_candidate(spider, good) >= 12
    assert score_candidate(spider, wrong) < 0


def test_wikidata_short_description_is_tied_to_character():
    entity = Entity(
        name="Storm",
        category="character",
        universe="Marvel",
    )
    text = format_short_description(
        entity,
        "fictional superhero appearing in Marvel Comics",
    )
    assert text.startswith("Storm —")
    assert text.endswith(".")


def test_wikidata_merge_replaces_only_catalog_fallback(tmp_path):
    image = Path(tmp_path) / "storm.jpg"
    image.write_bytes(b"image")
    entity = Entity(
        name="Storm",
        category="character",
        universe="Marvel",
        description="Descrição básica temporária.",
        metadata={
            "description_kind": "catalog_fallback",
            "description_verified": False,
        },
    )
    profile = WikidataProfile(
        qid="Q181300",
        label="Storm",
        description=(
            "Storm — fictional superhero appearing in Marvel Comics."
        ),
        description_language="en",
        entity_url="https://www.wikidata.org/wiki/Q181300",
        image_source_url=(
            "https://commons.wikimedia.org/wiki/File:Storm.jpg"
        ),
        image_attribution={
            "author": "Example",
            "license": "CC BY-SA 4.0",
        },
    )

    merged = merge_wikidata_profile(
        entity,
        profile,
        image_path=str(image),
    )

    assert merged.description == profile.description
    assert merged.metadata["description_verified"] is True
    assert merged.image == str(image)
    assert (
        merged.metadata["image_attribution"][str(image)]["license"]
        == "CC BY-SA 4.0"
    )
    assert any(
        source.source_type == "wikidata"
        for source in merged.sources
    )
    assert any(
        source.source_type == "wikimedia_commons"
        for source in merged.sources
    )


def test_wikidata_merge_does_not_override_verified_description():
    entity = Entity(
        name="Batman",
        category="character",
        universe="DC",
        description="Descrição oficial já validada.",
        metadata={"description_kind": "official_web"},
    )
    profile = WikidataProfile(
        qid="Q2695156",
        label="Batman",
        description="Batman — fictional superhero from DC Comics.",
        description_language="en",
        entity_url="https://www.wikidata.org/wiki/Q2695156",
    )

    merged = merge_wikidata_profile(entity, profile)
    assert merged.description == "Descrição oficial já validada."



def test_wikidata_merge_replaces_stale_local_image(tmp_path):
    replacement = Path(tmp_path) / "replacement.jpg"
    replacement.write_bytes(b"image")
    entity = Entity(
        name="Storm",
        category="character",
        universe="Marvel",
        image=str(Path(tmp_path) / "missing.jpg"),
    )
    profile = WikidataProfile(
        qid="Q181300",
        label="Storm",
        description="Storm — fictional superhero appearing in Marvel Comics.",
        description_language="en",
        entity_url="https://www.wikidata.org/wiki/Q181300",
    )

    merged = merge_wikidata_profile(
        entity,
        profile,
        image_path=str(replacement),
    )
    assert merged.image == str(replacement)


def test_wikidata_merge_fills_only_missing_structured_fields():
    entity = Entity(
        name="Structured Hero",
        category="character",
        universe="Marvel",
        occupation=["Official occupation"],
    )
    profile = WikidataProfile(
        qid="Q123",
        label="Structured Hero",
        description="Structured Hero — fictional superhero appearing in Marvel Comics.",
        description_language="en",
        entity_url="https://www.wikidata.org/wiki/Q123",
        aliases=["Hero Alias"],
        gender="female",
        occupation=["Supplemental occupation"],
        affiliations=["Example Team"],
        creators=["Example Creator"],
    )

    merged = merge_wikidata_profile(entity, profile)

    assert "Hero Alias" in merged.aliases
    assert merged.gender == "female"
    assert merged.occupation == ["Official occupation"]
    assert merged.affiliations == ["Example Team"]
    assert merged.creators == ["Example Creator"]
    provenance = merged.metadata["field_provenance"]
    assert provenance["gender"][0]["source_type"] == "wikidata"
    assert provenance["affiliations"][0]["source_ref"] == "Wikidata"


def test_wikidata_claim_helpers_extract_qids():
    from knowledge.sources.wikidata import WikidataClient

    data = {
        "claims": {
            "P21": [
                {"mainsnak": {"datavalue": {"value": {"id": "Q6581072"}}}},
                {"mainsnak": {}},
            ]
        }
    }
    assert WikidataClient._claim_item_ids(data, "P21") == ["Q6581072"]


def test_wikidata_accepts_exact_fictional_candidate_without_publisher_text():
    entity = Entity(
        name="Nova",
        category="character",
        universe="Marvel",
        publisher="Marvel Comics",
    )
    candidate = {
        "label": "Nova",
        "description": "fictional superhero",
        "aliases": [],
    }

    assert score_candidate(entity, candidate) >= 12


def test_wikidata_cache_rejects_untrusted_host_with_reason(tmp_path):
    from knowledge.sources.wikidata import WikidataClient

    client = WikidataClient(tmp_path / "wikidata")
    result = client.cache_commons_image(
        "https://example.com/hero.jpg",
        online=False,
        entity_name="Hero",
        qid="Q1",
    )

    assert result is None
    assert client.image_rejections[-1]["reason"] == "unsupported_source_host"
    assert client.image_rejections[-1]["entity"] == "Hero"


def test_wikidata_commons_image_promotes_over_official_reference(tmp_path):
    from knowledge.sources.wikidata import merge_wikidata_profile

    official = tmp_path / "official.jpg"
    commons = tmp_path / "commons.jpg"
    official.write_bytes(b"official")
    commons.write_bytes(b"commons")
    entity = Entity(
        name="Hero",
        category="character",
        universe="Marvel",
        image=str(official),
        metadata={
            "image_candidates": [str(official)],
            "image_attribution": {
                str(official): {
                    "license": "No open license recorded",
                    "rights_status": "official_source_local_reference",
                }
            },
        },
    )
    profile = WikidataProfile(
        qid="Q1",
        label="Hero",
        description="",
        description_language="",
        entity_url="https://www.wikidata.org/wiki/Q1",
        image_source_url="https://commons.wikimedia.org/wiki/File:Hero.jpg",
        image_attribution={
            "author": "Example",
            "license": "CC BY-SA 4.0",
            "source_url": "https://commons.wikimedia.org/wiki/File:Hero.jpg",
            "rights_status": "open_license_verified",
        },
    )

    merged = merge_wikidata_profile(
        entity,
        profile,
        image_path=str(commons),
    )

    assert merged.image == str(commons)
    assert str(official) in merged.metadata["image_candidates"]
    assert str(commons) in merged.metadata["image_candidates"]
