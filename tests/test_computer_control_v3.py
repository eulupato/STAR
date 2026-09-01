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
