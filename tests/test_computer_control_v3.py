from pathlib import Path

from modules import computer_control


def test_mentions_do_not_trigger_external_actions(monkeypatch):
    calls = []
    monkeypatch.setattr(
        computer_control.webbrowser,
        "open",
        lambda url: calls.append(url),
    )

    assert computer_control.parse(
        "o que é spotify?",
        allow_network=True,
    ) is None
    assert computer_control.parse(
        "não abra o google",
        allow_network=True,
    ) is None
    assert calls == []


def test_google_search_opens_only_search_result(monkeypatch):
    calls = []
    monkeypatch.setattr(
        computer_control.webbrowser,
        "open",
        lambda url: calls.append(url),
    )

    answer = computer_control.parse(
        "abra o google e pesquise estrelas",
        allow_network=True,
    )

    assert "Pesquisando" in answer
    assert len(calls) == 1
    assert "search?q=estrelas" in calls[0]


def test_star_prefix_is_accepted_without_changing_network_guard():
    answer = computer_control.parse(
        "STAR, abra o google",
        allow_network=False,
    )
    assert "Ative o modo ONLINE" in answer


def test_find_files_is_bounded_and_local(tmp_path):
    (tmp_path / "alpha_star.txt").write_text("x", encoding="utf-8")
    (tmp_path / "beta_star.txt").write_text("x", encoding="utf-8")
    (tmp_path / "other.txt").write_text("x", encoding="utf-8")

    hits = computer_control.find_files(
        "star",
        root=tmp_path,
        limit=1,
    )

    assert len(hits) == 1
    assert "star" in Path(hits[0]).name


def test_file_search_has_priority_over_generic_web_search(monkeypatch, tmp_path):
    target = tmp_path / "relatorio_star.txt"
    target.write_text("x", encoding="utf-8")
    web_calls = []

    monkeypatch.setattr(
        computer_control,
        "find_files",
        lambda query: [target] if query == "relatorio_star" else [],
    )
    monkeypatch.setattr(
        computer_control,
        "web_search",
        lambda query: web_calls.append(query) or "web",
    )

    answer = computer_control.parse(
        "procure arquivo relatorio_star",
        allow_network=True,
    )

    assert str(target) in answer
    assert web_calls == []


def test_spotify_suffix_removes_platform_name_from_query(monkeypatch):
    queries = []
    monkeypatch.setattr(
        computer_control,
        "spotify_search",
        lambda query: queries.append(query) or "ok",
    )

    assert computer_control.parse(
        "toca Space Oddity no Spotify",
        allow_network=True,
    ) == "ok"
    assert queries == ["space oddity"]


def test_spotify_prefix_is_explicit(monkeypatch):
    queries = []
    monkeypatch.setattr(
        computer_control,
        "spotify_search",
        lambda query: queries.append(query) or "ok",
    )

    assert computer_control.parse(
        "spotify toca Heroes",
        allow_network=True,
    ) == "ok"
    assert queries == ["heroes"]
