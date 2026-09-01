from core.islands import get_islands


def test_island_statuses_are_honest_and_enterable_states_are_explicit():
    islands = get_islands()
    assert islands["casa"]["status"] == "available"
    assert islands["herois"]["status"] == "partial"
    assert islands["casa"]["subareas"]["sala"]["status"] == "experimental"
    assert islands["casa"]["subareas"]["cozinha"]["status"] == "available"
    assert islands["casa"]["subareas"]["closet"]["status"] == "available"
    assert islands["casa"]["subareas"]["album"]["status"] == "partial"


def test_get_islands_returns_deep_copy():
    first = get_islands()
    second = get_islands()
    first["casa"]["subareas"]["sala"]["status"] = "broken"
    assert second["casa"]["subareas"]["sala"]["status"] == "experimental"
