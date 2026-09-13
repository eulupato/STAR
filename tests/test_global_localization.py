from core.global_localization import (
    LEGACY_LOCALES,
    STATIC_TEXTS,
    SUPPORTED_LOCALES,
    GlobalLocalizationEngine,
    invariant_values,
)
from core.language_manager import LanguageManager
from core.language_profiles import LOCALES
from core.offline_dictionary import OfflineDictionaryStore
from gui.localized_app import localize_ui_text


class FakeNeuralBackend:
    name = "fake-neural"

    def status(self):
        return {"installed": True, "backend": self.name, "pairs": ["pt->en"]}

    def translate(self, text, source_locale, target_locale):
        return "TRANSLATED: " + text


class NullNeuralBackend:
    name = "null-neural"

    def status(self):
        return {"installed": False, "backend": self.name, "pairs": []}

    def translate(self, text, source_locale, target_locale):
        return None


def make_manager(tmp_path):
    dictionary = OfflineDictionaryStore(tmp_path / "dict.sqlite3")
    engine = GlobalLocalizationEngine(dictionary=dictionary, neural_backend=NullNeuralBackend())
    return LanguageManager(tmp_path / "language.json", dictionary=dictionary, localization=engine)


def test_supported_profiles_cover_all_star_locales_without_inflating_curated_catalog():
    assert tuple(SUPPORTED_LOCALES) == tuple(LOCALES)
    assert len(SUPPORTED_LOCALES) == 18
    assert STATIC_TEXTS
    # O catálogo humano revisado legado continua com seis superfícies. Novos
    # idiomas usam overrides de UI + dicionários/Argos locais; não falsificamos
    # 18 cópias dos mesmos 500k conteúdos semânticos.
    for row in STATIC_TEXTS:
        assert set(row) == set(LEGACY_LOCALES)
        assert all(str(row[locale]).strip() for locale in LEGACY_LOCALES)


def test_static_ui_translation_works_without_neural_model(tmp_path):
    engine = GlobalLocalizationEngine(
        dictionary=OfflineDictionaryStore(tmp_path / "dict.sqlite3"),
        neural_backend=NullNeuralBackend(),
    )
    assert engine.translate("INICIAR", "en-US", "pt-BR").text == "START"
    assert engine.translate("CONFIGURAÇÕES", "fr-FR", "pt-BR").text == "PARAMÈTRES"
    assert engine.translate("SAÚDE", "it-IT", "pt-BR").text == "SALUTE"
    assert engine.translate("INICIAR", "ja-JP", "pt-BR").text == "開始"
    assert engine.translate("CLIMA", "ko-KR", "pt-BR").text == "날씨"
    assert engine.translate("AGORA", "ar-001", "pt-BR").text == "الآن"


def test_historical_profiles_do_not_claim_modern_machine_translation(tmp_path):
    engine = GlobalLocalizationEngine(
        dictionary=OfflineDictionaryStore(tmp_path / "dict.sqlite3"),
        neural_backend=FakeNeuralBackend(),
    )
    status = engine.status()
    assert status["historical_profiles_use_modern_mt"] is False
    assert {"grc-GR", "la-x-classical", "egy-EG"} <= set(status["historical_profiles"])
    # Palavra lexical conhecida pode ser traduzida pelo seed local, mas texto
    # livre histórico não deve ser enviado ao backend moderno.
    result = engine.translate("amor", "la-x-classical", "pt-BR")
    assert result.backend == "dictionary-exact"
    assert result.text == "amor"


def test_neural_translation_preserves_ids_numbers_urls_and_code(tmp_path):
    engine = GlobalLocalizationEngine(
        dictionary=OfflineDictionaryStore(tmp_path / "dict.sqlite3"),
        neural_backend=FakeNeuralBackend(),
    )
    source = (
        "A referência CHEMX-0000042 usa 9.81 m/s e https://example.org/data. "
        "Execute `x = 2 + 2` sem alterar os valores."
    )
    outcome = engine.translate(source, "en-US", "pt-BR")
    assert outcome.complete is True
    assert outcome.backend == "fake-neural"
    assert invariant_values(outcome.text) == invariant_values(source)
    assert "CHEMX-0000042" in outcome.text
    assert "9.81 m/s" in outcome.text
    assert "https://example.org/data" in outcome.text
    assert "`x = 2 + 2`" in outcome.text


def test_missing_translation_preserves_original_instead_of_mixing_languages(tmp_path):
    engine = GlobalLocalizationEngine(
        dictionary=OfflineDictionaryStore(tmp_path / "dict.sqlite3"),
        neural_backend=NullNeuralBackend(),
    )
    source = "hipótese bayesiana multiescala desconhecida"
    outcome = engine.translate(source, "fr-FR", "pt-BR")
    assert outcome.complete is False
    assert outcome.backend == "preserved-original"
    assert outcome.text == source


def test_language_manager_localizes_control_messages(tmp_path):
    manager = make_manager(tmp_path)

    response = manager.handle_command("mude para francês")
    assert manager.locale == "fr-FR"
    assert response is not None
    assert "Langue de STAR" in response
    assert "offline-first" in response

    current = manager.handle_command("langue actuelle")
    assert current is not None
    assert "Langue actuelle" in current

    japanese = manager.handle_command("mude para japonês")
    assert manager.locale == "ja-JP"
    assert japanese is not None
    assert "日本語" in japanese


def test_language_stats_expand_profiles_without_changing_old_semantic_counts(tmp_path):
    manager = make_manager(tmp_path)
    stats = manager.stats()
    assert stats["language_families"] == 13
    assert stats["locale_profiles"] == 18
    assert stats["modern_locales"] == 12
    assert stats["historical_locales"] == 6
    assert stats["curated_expression_families"] == 5
    assert stats["curated_locale_surfaces"] == 6
    assert stats["total_semantic_contents"] == 500000
    assert stats["knowledge_duplication_per_language"] is False
    assert stats["historical_mt_claimed"] is False
    assert stats["global_localization"]["strict_no_partial_translation"] is True
    assert stats["global_localization"]["canonical_locale"] == "pt-BR"


def test_desktop_gui_uses_same_language_manager_without_tk_window(tmp_path):
    manager = make_manager(tmp_path)
    manager.set_locale("es-ES")
    assert localize_ui_text(manager, "INICIAR") == "INICIAR"
    assert localize_ui_text(manager, "CONFIGURAÇÕES") == "AJUSTES"
    assert localize_ui_text(manager, "◈ ILHAS") == "◈ ISLAS"
    assert localize_ui_text(manager, "● V1.9 • OFFLINE") == "● V1.9 • OFFLINE"

    manager.set_locale("fr-FR")
    assert localize_ui_text(manager, "Pergunte algo à STAR...") == "Demandez quelque chose à STAR..."
    assert localize_ui_text(manager, "SISTEMA") == "SYSTÈME"

    manager.set_locale("ja-JP")
    assert localize_ui_text(manager, "INICIAR") == "開始"
    assert localize_ui_text(manager, "AGORA") == "今"
