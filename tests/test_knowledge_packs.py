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


def _make_pack(root):
    pack = root / "matematica_teste"
    pack.mkdir(parents=True)
    (pack / "manifest.json").write_text(
        json.dumps(
            {
                "id": "matematica_teste",
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
    manager = KnowledgePackManager(tmp_path)

    assert manager.stats() == {"packs": 1, "entries": 2}
    answer = manager.answer("Você pode me dizer o que é uma fração?")
    assert answer is not None
    assert "numerador" in answer
    assert manager.answer("qual é a capital da frança?") is None


def test_executive_uses_pack_before_unknown_fallback(tmp_path):
    _make_pack(tmp_path)
    manager = KnowledgePackManager(tmp_path)
    executive = Executive(
        internal_knowledge=EmptyInternalKnowledge(),
        knowledge_packs=manager,
    )

    answer = executive.execute(
        {"input": "qual é o teorema de pitágoras?"},
        {"response_type": None},
    )
    assert "hipotenusa" in answer
