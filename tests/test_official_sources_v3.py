from pathlib import Path

from knowledge.engine import KnowledgeEngine
from knowledge.entities import Entity, KnowledgeSource
from knowledge.sources.official import (
    DCOfficialSource,
    MarvelOfficialSource,
    OfficialWebClient,
    merge_official_profile,
)


def client(tmp_path):
    return OfficialWebClient(tmp_path / "official-cache")


def test_dc_official_profile_parser(tmp_path):
    html = """
    <html><head>
      <meta property="og:title" content="Batman | Official DC Character">
      <meta property="og:description" content="The Dark Knight protects Gotham City.">
      <meta property="og:image" content="https://static.dc.com/batman.jpg">
    </head><body>
      <h1>Batman</h1>
      <h2>Character Facts</h2>
      <div>Powers:</div><div>martial arts, detective skill, advanced technology</div>
      <div>First Appearance:</div><div>DETECTIVE COMICS #27 (1939)</div>
      <div>Alias/Alter Ego:</div><div>Bruce Wayne</div>
      <div>AKA:</div><div>Dark Knight, Caped Crusader</div>
      <div>Base of Operations:</div><div>Gotham City</div>
      <div>Occupation:</div><div>CEO of Wayne Enterprises</div>
      <h2>Related Characters</h2>
      <a href="/characters/robin">Robin</a>
      <a href="/characters/superman">Superman</a>
    </body></html>
    """
    source = DCOfficialSource(client(tmp_path))
    profile = source.parse(html, "https://www.dc.com/characters/batman")
    assert profile is not None
    assert profile.name == "Batman"
    assert "Bruce Wayne" in profile.aliases
    assert "Dark Knight" in profile.aliases
    assert "Gotham City" in profile.origin_place
    assert "martial arts" in profile.powers
    assert {r.target_name for r in profile.relationships} == {"Robin", "Superman"}
    assert profile.image_url == "https://static.dc.com/batman.jpg"


def test_marvel_official_profile_parser(tmp_path):
    html = """
    <html><head>
      <meta property="og:title" content="Spider-Man (Peter Parker) | Characters | Marvel">
      <meta property="og:description" content="Peter Parker uses his powers to help others.">
      <meta property="og:image" content="https://cdn.marvel.com/spider-man.jpg">
    </head><body>
      <h1>Peter Parker Spider-Man</h1>
      <div>Other Aliases</div><div>Friendly Neighborhood Spider-Man, Spidey</div>
      <div>Education</div><div>Science</div>
      <div>Place of Origin</div><div>Forest Hills, New York</div>
      <div>Identity</div><div>Secret</div>
      <div>Known Relatives</div><div>Aunt May</div>
      <div>Powers</div><div>Superhuman Strength, Spider-Sense, Wallcrawling</div>
      <div>Group Affiliation</div><div>Avengers, Fantastic Four</div>
      <h2>Connections</h2>
      <a href="/characters/iron-man-tony-stark">Iron Man</a>
    </body></html>
    """
    source = MarvelOfficialSource(client(tmp_path))
    profile = source.parse(html, "https://www.marvel.com/characters/spider-man-peter-parker/in-comics")
    assert profile is not None
    assert "Friendly Neighborhood Spider-Man" in profile.aliases
    assert "Spider-Sense" in profile.powers
    assert "Avengers" in profile.affiliations
    assert "Forest Hills" in profile.origin_place
    assert profile.image_url == "https://cdn.marvel.com/spider-man.jpg"


def test_marvel_candidates_use_real_name_from_pdf(tmp_path):
    entity = Entity(
        name="Wolverine",
        category="character",
        universe="Marvel",
        attributes={"real_name": "James Howlett"},
    )
    urls = MarvelOfficialSource(client(tmp_path)).candidate_urls(entity)
    assert "https://www.marvel.com/characters/wolverine-james-howlett" in urls


def test_official_merge_prioritizes_official_and_preserves_pdf_reference(tmp_path):
    source = DCOfficialSource(client(tmp_path))
    profile = source.parse(
        """
        <html><head>
        <meta property="og:title" content="Batman | Official DC Character">
        <meta property="og:description" content="Official description">
        </head><body>
        <div>Powers:</div><div>detective skill</div>
        <div>First Appearance:</div><div>DETECTIVE COMICS #27</div>
        <div>Alias/Alter Ego:</div><div>Bruce Wayne</div>
        </body></html>
        """,
        "https://www.dc.com/characters/batman",
    )
    entity = Entity(
        name="Batman",
        category="character",
        universe="DC",
        description="Descrição extraída do PDF",
        image="/local/pdf-portrait.png",
        powers=["martial arts"],
        sources=[KnowledgeSource("PDF", "dc.pdf", page=10)],
    )
    merged = merge_official_profile(entity, profile, image_path="/web/cache.jpg")
    assert merged.description == "Official description"
    assert merged.image == "/web/cache.jpg"
    assert merged.metadata["supplemental_pdf_description"] == "Descrição extraída do PDF"
    assert "/local/pdf-portrait.png" in merged.metadata["image_candidates"]
    assert "/web/cache.jpg" in merged.metadata["image_candidates"]
    assert "martial arts" in merged.powers
    assert "detective skill" in merged.powers
    assert any(s.url == "https://www.dc.com/characters/batman" for s in merged.sources)


def test_official_source_rejects_wrong_character_profile(tmp_path):
    source = DCOfficialSource(client(tmp_path))
    source.client.fetch_html = lambda *_args, **_kwargs: """
        <html><head>
          <meta property="og:title" content="Superman | Official DC Character">
        </head><body>
          <div>Alias/Alter Ego:</div><div>Clark Kent</div>
        </body></html>
    """
    entity = Entity(
        name="Batman",
        category="character",
        universe="DC",
        attributes={"real_name": "Bruce Wayne"},
    )
    assert source.fetch_profile(entity, online=True) is None


def test_marvel_real_name_prevents_ambiguous_profile_merge(tmp_path):
    source = MarvelOfficialSource(client(tmp_path))
    urls = source.candidate_urls(
        Entity(
            name="Spider-Man",
            category="character",
            universe="Marvel",
            attributes={"real_name": "Miles Morales"},
        )
    )
    assert urls[0].endswith("spider-man-miles-morales")

    source.client.fetch_html = lambda *_args, **_kwargs: """
        <html><head>
          <meta property="og:title"
                content="Spider-Man (Peter Parker) | Characters | Marvel">
        </head><body>
          <div>Other Aliases</div><div>Peter Parker</div>
        </body></html>
    """
    entity = Entity(
        name="Spider-Man",
        category="character",
        universe="Marvel",
        attributes={"real_name": "Miles Morales"},
    )
    assert source.fetch_profile(entity, online=True) is None



def test_marvel_catalog_discovered_url_is_tried_first(tmp_path):
    source = MarvelOfficialSource(client(tmp_path))
    entity = Entity(
        name="Spider-Man (Miles Morales)",
        category="character",
        universe="Marvel",
        attributes={"real_name": "Miles Morales"},
        metadata={
            "official_profile_url":
                "https://www.marvel.com/characters/spider-man-miles-morales"
        },
    )
    urls = source.candidate_urls(entity)
    assert urls[0] == "https://www.marvel.com/characters/spider-man-miles-morales"
