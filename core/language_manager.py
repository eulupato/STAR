"""Gerenciador de idioma, tradução contextual e localização global da STAR."""
from __future__ import annotations

import json
from pathlib import Path
import re

from core.global_localization import GlobalLocalizationEngine, TranslationOutcome
from core.language_catalog import DEFAULT_LOCALE, LOCALES, ExpressionCatalog
from core.offline_dictionary import OfflineDictionaryStore, normalize_term

ROOT = Path(__file__).resolve().parents[1]
SETTINGS_FILE = ROOT / "runtime" / "language" / "settings.json"
LOCALE_ORDER = ("pt-BR", "en-US", "en-GB", "es-ES", "it-IT", "fr-FR")


def resolve_locale(value: str) -> str | None:
    raw = normalize_term(value)
    if not raw:
        return None
    for code, meta in LOCALES.items():
        if normalize_term(code) == raw or normalize_term(meta["name"]) == raw:
            return code
        for alias in meta["aliases"]:
            if normalize_term(alias) == raw:
                return code
    compact = raw.replace(" ", "")
    fallback = {
        "portugues": "pt-BR", "portuguesbrasil": "pt-BR", "ptbr": "pt-BR",
        "english": "en-US", "ingles": "en-US", "enus": "en-US", "engb": "en-GB",
        "spanish": "es-ES", "espanol": "es-ES", "espanhol": "es-ES",
        "italian": "it-IT", "italiano": "it-IT", "french": "fr-FR", "francais": "fr-FR", "frances": "fr-FR",
    }
    return fallback.get(compact)


def _strip_wake_prefix(raw: str) -> str:
    """Tolera wake words mesmo quando o manager é usado fora do StarCore."""
    value = str(raw or "").strip()
    normalized = normalize_term(value)
    prefixes = ("ei star ", "ok star ", "ola star ", "hey star ", "star ")
    for prefix in prefixes:
        if normalized.startswith(prefix):
            return normalized[len(prefix):].strip()
    return value


class LanguageManager:
    """Fonte única de verdade para idioma ativo e tradução da superfície.

    A STAR processa internamente em pt-BR e localiza a entrada/saída nas bordas.
    Nenhum engine de conhecimento precisa duplicar fatos por idioma.
    """

    def __init__(
        self,
        settings_path: Path | str = SETTINGS_FILE,
        dictionary: OfflineDictionaryStore | None = None,
        localization: GlobalLocalizationEngine | None = None,
    ):
        self.settings_path = Path(settings_path)
        self.dictionary = dictionary or OfflineDictionaryStore()
        self.expressions = ExpressionCatalog()
        self.localization = localization or GlobalLocalizationEngine(
            dictionary=self.dictionary,
            expressions=self.expressions,
        )
        self.locale = self._load_locale()

    def _load_locale(self) -> str:
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            locale = str(data.get("locale", DEFAULT_LOCALE))
            return locale if locale in LOCALES else DEFAULT_LOCALE
        except (OSError, json.JSONDecodeError, AttributeError):
            return DEFAULT_LOCALE

    def _save(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(
            json.dumps({"locale": self.locale}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def set_locale(self, locale: str) -> str:
        resolved = resolve_locale(locale) or (locale if locale in LOCALES else None)
        if resolved is None:
            raise ValueError(f"Idioma não suportado: {locale}")
        self.locale = resolved
        self._save()
        return self.locale

    def cycle(self, steps: int = 1) -> str:
        index = LOCALE_ORDER.index(self.locale) if self.locale in LOCALE_ORDER else 0
        self.locale = LOCALE_ORDER[(index + int(steps)) % len(LOCALE_ORDER)]
        self._save()
        return self.locale

    def profile(self, locale: str | None = None) -> dict:
        code = locale or self.locale
        return {"code": code, **LOCALES[code]}

    def display(self, locale: str | None = None) -> str:
        profile = self.profile(locale)
        return f"{profile['flag']} {profile['name']}"

    def message(self, key: str, locale: str | None = None, **values) -> str:
        return self.localization.message(key, locale or self.locale, **values)

    def localize_static(self, text: str, locale: str | None = None) -> str:
        target = locale or self.locale
        return self.localization.static(text, target) or str(text)

    def stats(self) -> dict:
        expression = self.expressions.stats()
        localization = self.localization.status()
        return {
            **expression,
            "selected_locale": self.locale,
            "dictionary_sources": self.dictionary.source_stats(),
            "dictionary_seed_entries": self.dictionary.seed_size(),
            "full_dictionary_index_ready": self.dictionary.full_index_ready,
            "global_localization": localization,
        }

    def detect_locale(self, text: str) -> str:
        hit = self.expressions.match(text)
        if hit:
            return hit[1]
        norm = normalize_term(text)
        for locale in LOCALE_ORDER:
            if self.dictionary.lookup(norm, locale, "pt-BR") is not None:
                return locale
        return self.locale if self.locale in LOCALES else DEFAULT_LOCALE

    def translate_with_report(
        self,
        text: str,
        target_locale: str,
        source_locale: str | None = None,
    ) -> TranslationOutcome:
        target = resolve_locale(target_locale) or (target_locale if target_locale in LOCALES else None)
        source = source_locale if source_locale in LOCALES else self.detect_locale(text)
        if target is None:
            return TranslationOutcome(
                str(text), source, str(target_locale), "identity", False, reason="unsupported-locale"
            )
        return self.localization.translate(str(text), target, source)

    def translate(self, text: str, target_locale: str, source_locale: str | None = None) -> str | None:
        outcome = self.translate_with_report(text, target_locale, source_locale)
        return outcome.text if outcome.complete else None

    def translate_to_portuguese(self, text: str) -> str:
        if self.locale == "pt-BR":
            return str(text)
        outcome = self.translate_with_report(text, "pt-BR", self.locale)
        return outcome.text if outcome.complete else str(text)

    def translate_response(self, text: str) -> str:
        """Localiza uma resposta canônica sem nunca apresentar tradução parcial."""
        if self.locale == "pt-BR":
            return str(text)
        outcome = self.translate_with_report(text, self.locale, "pt-BR")
        return outcome.text

    def handle_command(self, text: str) -> str | None:
        raw = _strip_wake_prefix(str(text or "").strip())
        norm = normalize_term(raw)
        if not norm:
            return None

        # Comandos de seleção em PT/EN/ES/IT/FR; chegam aqui tanto por texto quanto STT.
        set_prefixes = (
            "mude para ", "muda para ", "troque para ", "troca para ", "idioma ", "fale em ",
            "switch to ", "change language to ", "speak ",
            "cambia a ", "cambiar a ", "habla ",
            "passa a ", "cambia lingua in ", "parla ",
            "passe en ", "change de langue vers ", "parle ",
        )
        for prefix in set_prefixes:
            p = normalize_term(prefix)
            if norm.startswith(p):
                tail = norm[len(p):].strip()
                locale = resolve_locale(tail)
                if locale:
                    self.set_locale(locale)
                    return self.message("language_changed", locale, display=self.display(locale))

        if norm in {
            "qual idioma", "qual idioma esta ativo", "idioma atual", "current language",
            "que idioma", "lingua atual", "idioma actual", "langue actuelle", "lingua corrente",
        }:
            return self.message("current_language", display=self.display())

        # Tradução explícita. Mantém o texto original antes do marcador alvo.
        markers = (" para ", " to ", " al ", " a ", " en ", " in ")
        translation_starts = ("traduza ", "traduz ", "translate ", "traduce ", "traduci ", "traduis ")
        lowered = raw.lower().strip()
        for start in translation_starts:
            if lowered.startswith(start):
                body = raw[len(start):].strip()
                for marker in markers:
                    pos = body.lower().rfind(marker)
                    if pos <= 0:
                        continue
                    source_text = body[:pos].strip(" \"'“”")
                    target_text = body[pos + len(marker):].strip(" \"'“”?.!")
                    target = resolve_locale(target_text)
                    if not target:
                        continue
                    source = self.detect_locale(source_text)
                    outcome = self.translate_with_report(source_text, target, source)
                    if outcome.complete:
                        return f"{outcome.text}  [{self.display(target)} • {outcome.backend}]"
                    return self.message(
                        "translation_missing",
                        locale=self.locale,
                        text=source_text,
                    )
        return None
