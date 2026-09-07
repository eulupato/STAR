import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.executive import Executive
from core.knowledge_packs import KnowledgePackManager


class EmptyInternalKnowledge:
    def answer(self, _text):
        return None


def _make_pack(root, pack_name="matematica_teste"):
    pack = root / pack_name
    pack.mkdir(parents=True)
    (pack / "manifest.json").write_text(
        json.dumps(
            {
                "id": pack_name,
                "name": "Matemática Teste",
                "version": "1.0",
                "content_file": "knowledge.jsonl",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    entries = [
        {
            "id": "fracoes.definicao",
            "title": "Definição de fração",
            "aliases": ["o que é uma fração", "defina fração"],
            "keywords": ["fração", "numerador", "denominador"],
            "answer": "Uma fração representa partes de um todo e é escrita como numerador sobre denominador.",
            "source": {"document": "Livro teste", "pages": [12]},
            "metadata": {"domain": "matemática"},
        },
        {
            "id": "pitagoras",
            "title": "Teorema de Pitágoras",
            "aliases": ["qual é o teorema de pitágoras"],
            "keywords": ["triângulo retângulo", "hipotenusa", "catetos"],
            "answer": "Em um triângulo retângulo, o quadrado da hipotenusa é igual à soma dos quadrados dos catetos.",
            "source": {"document": "Livro teste", "pages": [42]},
        },
    ]
    with (pack / "knowledge.jsonl").open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _make_catalog_pack(root, local_catalog_root):
    pack = root / "heroes_test"
    pack.mkdir(parents=True)
    (pack / "manifest.json").write_text(
        json.dumps(
            {
                "id": "heroes_test",
                "name": "Heróis Teste",
                "content_file": "knowledge.json",
                "catalog": {
                    "file": "catalog.tsv",
                    "expected_counts": {
                        "characters": 3,
                        "teams": 2,
                        "total": 5,
                    },
                    "source": {
                        "type": "community_catalog",
                        "reference": "Marvel Database / Fandom",
                        "official": False,
                    },
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (pack / "knowledge.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "id": "curated:test",
                        "title": "Ficha Curada",
                        "aliases": ["Curated"],
                        "keywords": ["teste"],
                        "answer": "Ficha revisada.",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    local = local_catalog_root / "heroes_test"
    local.mkdir(parents=True)
    (local / "catalog.tsv").write_text(
        "\n".join(
            [
                "tipo\tentrada",
                "PERSONAGEM\tPeter Parker (Earth-616)",
                "PERSONAGEM\tPeter Parker (Earth-1610)",
                "PERSONAGEM\tTony Stark (Earth-616)",
                "EQUIPE\tAvengers (Earth-616)",
                "EQUIPE\tX-Men (Earth-616)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (local / "catalog.meta.json").write_text(
        json.dumps(
            {
                "characters": 3,
                "teams": 2,
                "total": 5,
            }
        ),
        encoding="utf-8",
    )


def test_manager_loads_and_searches_structured_pack(tmp_path):
    _make_pack(tmp_path)
    manager = KnowledgePackManager(tmp_path, auto_removable=False)

    assert manager.stats() == {"packs": 1, "entries": 2}
    answer = manager.answer("Você pode me dizer o que é uma fração?")
    assert answer is not None
    assert "numerador" in answer
    assert manager.answer("qual é a capital da frança?") is None


def test_manager_exposes_public_entries_without_index_internals(tmp_path):
    _make_pack(tmp_path)
    manager = KnowledgePackManager(tmp_path, auto_removable=False)

    entries = manager.list_entries("matematica_teste")
    assert len(entries) == 2
    assert entries[0]["metadata"] == {"domain": "matemática"}
    assert "_search_texts" not in entries[0]


def test_search_can_be_scoped_to_a_single_pack(tmp_path):
    _make_pack(tmp_path, "pack_a")
    _make_pack(tmp_path, "pack_b")
    manager = KnowledgePackManager(tmp_path, auto_removable=False)

    result = manager.search("teorema de pitágoras", pack_id="pack_b")
    assert result is not None
    assert result["pack_id"] == "pack_b"
    assert manager.search("teorema de pitágoras", pack_id="inexistente") is None


def test_executive_uses_pack_before_unknown_fallback(tmp_path):
    _make_pack(tmp_path)
    manager = KnowledgePackManager(tmp_path, auto_removable=False)
    executive = Executive(
        internal_knowledge=EmptyInternalKnowledge(),
        knowledge_packs=manager,
    )

    answer = executive.execute(
        {"input": "qual é o teorema de pitágoras?"},
        {"response_type": None},
    )
    assert "hipotenusa" in answer


def test_manager_reads_pack_from_external_star_knowledge_drive(tmp_path):
    local = tmp_path / "local"
    usb = tmp_path / "usb"
    external_packs = usb / "STAR_KNOWLEDGE" / "packs"
    _make_pack(external_packs, "fisica_usb")

    manager = KnowledgePackManager(
        local,
        external_roots=[external_packs],
        auto_removable=False,
    )

    assert manager.storage_stats() == {"local": 0, "removable": 1, "conflicts": 0}
    assert manager.answer("qual é o teorema de pitágoras?") is not None
    assert manager.list()["fisica_usb"]["storage"] == "removable"


def test_pack_content_file_cannot_escape_pack_directory(tmp_path):
    pack = tmp_path / "seguranca"
    pack.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text(
        json.dumps([{"title": "segredo", "answer": "não carregar"}]),
        encoding="utf-8",
    )
    (pack / "manifest.json").write_text(
        json.dumps({"id": "seguranca", "content_file": "../outside.json"}),
        encoding="utf-8",
    )

    manager = KnowledgePackManager(tmp_path, auto_removable=False)
    assert manager.list()["seguranca"]["entries"] == 0
    assert manager.answer("segredo") is None


def test_catalog_overlay_is_lazy_searchable_and_keeps_variants(tmp_path):
    packs_root = tmp_path / "knowledge" / "packs"
    catalog_root = tmp_path / "knowledge" / "local"
    _make_catalog_pack(packs_root, catalog_root)

    manager = KnowledgePackManager(
        packs_root,
        auto_removable=False,
        local_catalog_root=catalog_root,
    )

    before = manager.catalog_stats("heroes_test")
    assert before["available"] is True
    assert before["total"] == 5
    assert before["loaded"] is False

    results = manager.catalog_search(
        "Peter Parker (Earth-616)",
        "heroes_test",
        entity_type="character",
        limit=10,
    )
    assert results[0]["title"] == "Peter Parker (Earth-616)"
    assert results[0]["metadata"]["continuity"] == "Earth-616"
    assert results[0]["metadata"]["catalog_only"] is True
    assert results[0]["source"]["official"] is False
    assert len({item["id"] for item in results}) == len(results)

    variants = manager.catalog_search(
        "Peter Parker",
        "heroes_test",
        entity_type="character",
        limit=10,
    )
    assert {item["title"] for item in variants} >= {
        "Peter Parker (Earth-616)",
        "Peter Parker (Earth-1610)",
    }
    assert manager.catalog_stats("heroes_test")["loaded"] is True


def test_catalog_can_filter_teams_without_loading_into_regular_entries(tmp_path):
    packs_root = tmp_path / "knowledge" / "packs"
    catalog_root = tmp_path / "knowledge" / "local"
    _make_catalog_pack(packs_root, catalog_root)

    manager = KnowledgePackManager(
        packs_root,
        auto_removable=False,
        local_catalog_root=catalog_root,
    )

    assert manager.stats() == {"packs": 1, "entries": 1}
    teams = manager.catalog_list("heroes_test", entity_type="team", limit=10)
    assert [item["title"] for item in teams] == [
        "Avengers (Earth-616)",
        "X-Men (Earth-616)",
    ]


def test_catalog_file_cannot_escape_allowed_roots(tmp_path):
    packs_root = tmp_path / "packs"
    pack = packs_root / "unsafe"
    pack.mkdir(parents=True)
    outside = tmp_path / "outside.tsv"
    outside.write_text("tipo\tentrada\nPERSONAGEM\tSegredo\n", encoding="utf-8")
    (pack / "manifest.json").write_text(
        json.dumps(
            {
                "id": "unsafe",
                "catalog": {
                    "file": "../outside.tsv",
                    "expected_counts": {"total": 1},
                },
            }
        ),
        encoding="utf-8",
    )

    manager = KnowledgePackManager(packs_root, auto_removable=False)
    stats = manager.catalog_stats("unsafe")
    assert stats["available"] is False
    assert stats["expected_total"] == 1
    assert manager.catalog_search("Segredo", "unsafe") == []


def test_builtin_heroes_pack_is_structured_searchable_and_declares_full_catalog_snapshot():
    manager = KnowledgePackManager(ROOT / "knowledge" / "packs", auto_removable=False)
    heroes = manager.list().get("heroes")

    assert heroes is not None
    assert heroes["entries"] == 12
    result = manager.search("Batman", pack_id="heroes")
    assert result is not None
    assert result["title"] == "Batman"
    assert result["metadata"]["reality_class"] == "fictional"
    assert result["metadata"]["image_status"] == "missing_authorized_asset"
    assert manager.answer("Joana d'Arc", pack_id="heroes") is not None

    catalog = manager.catalog_stats("heroes")
    assert catalog["expected_total"] == 111024
