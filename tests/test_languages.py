from pathlib import Path

from core.language_catalog import ExpressionCatalog
from core.language_manager import LanguageManager
from core.offline_dictionary import DICTIONARY_SOURCES, OfflineDictionaryStore


def test_expression_catalog_has_exactly_100k_per_language_family():
    catalog = ExpressionCatalog()
    stats = catalog.stats()
    assert stats["language_families"] == 5
    assert stats["locale_profiles"] == 6
    assert stats["base_expressions"] == 50
    assert stats["semantic_concepts_per_language"] == 100
    assert stats["variants_per_concept"] == 1000
    assert stats["contents_per_language"] == 100000
    assert stats["total_semantic_contents"] == 500000


def test_expression_id_boundaries_are_exact():
    catalog = ExpressionCatalog()
    assert catalog.content_id("pt", 0, 0) == "EXP-PTBR-000001"
    assert catalog.content_id("pt", 99, 999) == "EXP-PTBR-100000"
    assert catalog.content_id("en", 99, 999) == "EXP-EN-100000"
    assert catalog.content_id("fr", 99, 999) == "EXP-FR-100000"


def test_contextual_translation_is_not_forced_literal():
    catalog = ExpressionCatalog()
    assert catalog.contextual_equivalent("e aí mano, sereno?", "en-US") == "yo man, all good?"
    assert catalog.contextual_equivalent("e aí mano, sereno?", "en-GB") == "alright mate, you good?"
    assert catalog.contextual_equivalent("tô liso", "en-US") == "I'm broke"
    assert catalog.contextual_equivalent("tô liso", "en-GB") == "I'm skint"
    assert catalog.contextual_equivalent("tô liso", "fr-FR") == "je suis fauché"


def test_each_language_has_at_least_five_dictionary_sources():
    assert set(DICTIONARY_SOURCES) == {"pt", "en", "es", "it", "fr"}
    assert all(len(sources) >= 5 for sources in DICTIONARY_SOURCES.values())
    assert all(len({source["id"] for source in sources}) >= 5 for sources in DICTIONARY_SOURCES.values())


def test_seed_dictionary_works_without_network(tmp_path):
    store = OfflineDictionaryStore(tmp_path / "does-not-exist.sqlite3")
    assert not store.full_index_ready
    assert store.lookup("physics", "en-US", "fr-FR") == "physique"
    assert store.lookup("dinheiro", "pt-BR", "en-GB") == "money"
    assert store.lookup("gravidade", "pt-BR", "it-IT") == "gravità"


def test_language_manager_persists_and_cycles(tmp_path):
    manager = LanguageManager(tmp_path / "language.json", OfflineDictionaryStore(tmp_path / "dict.sqlite3"))
    assert manager.locale == "pt-BR"
    assert manager.set_locale("British English") == "en-GB"
    assert manager.profile()["flag"] == "🇬🇧"
    manager2 = LanguageManager(tmp_path / "language.json", OfflineDictionaryStore(tmp_path / "dict.sqlite3"))
    assert manager2.locale == "en-GB"
    assert manager2.cycle(1) == "es-ES"


def test_voice_style_language_commands_and_offline_translation(tmp_path):
    manager = LanguageManager(tmp_path / "language.json", OfflineDictionaryStore(tmp_path / "dict.sqlite3"))
    changed = manager.handle_command("STAR, mude para inglês UK")
    assert changed is not None
    assert manager.locale == "en-GB"
    translated = manager.handle_command("traduza e aí mano, sereno? para inglês EUA")
    assert translated is not None
    assert "yo man, all good?" in translated


def test_watch_language_mode_is_added_without_replacing_existing_modes():
    from clients import star_watch_app as watch_base
    original_keys = {m.key for m in watch_base.WATCH_MODES}
    import clients.star_watch_language  # noqa: F401
    keys = {m.key for m in watch_base.WATCH_MODES}
    assert original_keys <= keys
    assert "language" in keys
    assert {"voice", "search", "weather", "settings"} <= keys
