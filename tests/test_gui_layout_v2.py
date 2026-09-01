from pathlib import Path


def _show_islands_source() -> str:
    source = Path("gui/app.py").read_text(encoding="utf-8")
    start = source.index("    def show_islands(self):")
    end = source.index("    def show_house(self):", start)
    return source[start:end]


def test_islands_cards_use_dedicated_grid_container():
    block = _show_islands_source()

    assert "cards_grid = tk.Frame(body" in block
    assert 'cards_grid.pack(fill="both", expand=True)' in block
    assert "card = tk.Frame(cards_grid" in block
    assert "card = tk.Frame(body" not in block


def test_islands_grid_has_three_responsive_columns():
    block = _show_islands_source()

    assert "for column in range(3):" in block
    assert "cards_grid.grid_columnconfigure(column, weight=1)" in block
