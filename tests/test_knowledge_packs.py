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


def test_manager_loads_and_searches_structured_pack(tmp_path):
    _make_pack(tmp_path)
    manager = KnowledgePackManager(tmp_path, auto_removable=False)

    assert manager.stats() == {"packs": 1, "entries": 2}
    answer = manager.answer("Você pode me dizer o que é uma fração?")
    assert answer is not None
    assert "numerador" in answer
    assert manager.answer("qual é a capital da frança?") is None


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
