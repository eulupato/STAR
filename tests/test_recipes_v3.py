import json

from knowledge.recipes import RecipeBook


def test_recipe_book_loads_structured_json(tmp_path):
    root = tmp_path / "recipes"
    root.mkdir()
    (root / "book.json").write_text(
        json.dumps(
            {
                "recipes": [
                    {
                        "name": "Teste",
                        "ingredients": ["A", "B"],
                        "steps": ["Misture", "Sirva"],
                        "tags": ["simples"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    recipes = RecipeBook(root).load()
    assert len(recipes) == 1
    assert recipes[0].name == "Teste"
    assert recipes[0].ingredients == ("A", "B")
    assert recipes[0].steps == ("Misture", "Sirva")


def test_recipe_book_parses_markdown_sections(tmp_path):
    root = tmp_path / "recipes"
    root.mkdir()
    (root / "recipe.md").write_text(
        "# Receita Markdown\n\n"
        "## Ingredientes\n"
        "- item A\n"
        "- item B\n\n"
        "## Preparo\n"
        "1. Primeiro passo\n"
        "2. Segundo passo\n",
        encoding="utf-8",
    )

    recipes = RecipeBook(root).load()
    assert recipes[0].name == "Receita Markdown"
    assert "item A" in recipes[0].ingredients
    assert "Primeiro passo" in recipes[0].steps


def test_recipe_book_searches_name_ingredients_and_tags(tmp_path):
    root = tmp_path / "recipes"
    root.mkdir()
    (root / "book.json").write_text(
        json.dumps(
            [
                {
                    "name": "Sanduíche",
                    "ingredients": ["tomate", "pão"],
                    "steps": ["Montar"],
                    "tags": ["lanche"],
                },
                {
                    "name": "Salada",
                    "ingredients": ["pepino"],
                    "steps": ["Misturar"],
                    "tags": ["leve"],
                },
            ]
        ),
        encoding="utf-8",
    )

    book = RecipeBook(root)
    assert [item.name for item in book.search("tomate")] == ["Sanduíche"]
    assert [item.name for item in book.search("leve")] == ["Salada"]
