from knowledge.engine import KnowledgeEngine
from knowledge.sources.marvel_catalog import (
    MARVEL_CATALOG_URL,
    MarvelOfficialCatalog,
    parse_catalog_html,
)


def test_marvel_catalog_parser_keeps_variants_distinct():
    html = """
    <html><body>
      <a href="/characters/spider-man-peter-parker">Spider-Man (Peter Parker)</a>
      <a href="/characters/spider-man-miles-morales">Spider-Man (Miles Morales)</a>
      <a href="/characters/loki">Loki</a>
      <a href="/news/story">Not a character</a>
    </body></html>
    """
    entries, _pages = parse_catalog_html(html, MARVEL_CATALOG_URL)
    assert [entry.name for entry in entries] == [
        "Spider-Man (Peter Parker)",
        "Spider-Man (Miles Morales)",
        "Loki",
    ]
    assert entries[0].real_name == "Peter Parker"
    assert entries[1].real_name == "Miles Morales"
    assert entries[0].identity_key != entries[1].identity_key


def test_marvel_catalog_import_does_not_merge_miles_with_peter(tmp_path):
    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    html = """
    <html><body>
      <a href="/characters/spider-man-peter-parker">Spider-Man (Peter Parker)</a>
      <a href="/characters/spider-man-miles-morales">Spider-Man (Miles Morales)</a>
    </body></html>
    """

    class Client:
        def fetch_html(self, *_args, **_kwargs):
            return html

    catalog = MarvelOfficialCatalog(Client())
    saved = catalog.import_into(engine, online=True, max_pages=1)
    assert saved == 2

    peter = engine.resolve_entity("Spider-Man (Peter Parker)", universe="Marvel")
    miles = engine.resolve_entity("Spider-Man (Miles Morales)", universe="Marvel")
    assert peter is not None
    assert miles is not None
    assert peter.id != miles.id
    assert peter.attributes["real_name"] == "Peter Parker"
    assert miles.attributes["real_name"] == "Miles Morales"


def test_marvel_catalog_parser_accepts_legacy_official_index():
    html = """
    <html><body>
      <a href="/comics/characters/1009187/black_panther">Black Panther</a>
      <a href="/comics/characters/1009368/iron_man">Iron Man</a>
    </body></html>
    """
    entries, _pages = parse_catalog_html(
        html,
        "https://www.marvel.com/comics/characters?l=sem&o=603409",
    )
    assert {entry.name for entry in entries} == {"Black Panther", "Iron Man"}
