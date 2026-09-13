"""Gerenciador de idioma, tradução contextual e localização global da STAR."""
from __future__ import annotations

import json
from pathlib import Path

from core.global_localization import GlobalLocalizationEngine, TranslationOutcome
from core.language_catalog import ExpressionCatalog
from core.language_profiles import DEFAULT_LOCALE, LANGUAGE_FAMILIES, LOCALES, LOCALE_ORDER, stats as profile_stats
from core.offline_dictionary import OfflineDictionaryStore, normalize_term

ROOT = Path(__file__).resolve().parents[1]
SETTINGS_FILE = ROOT / "runtime" / "language" / "settings.json"


def resolve_locale(value: str) -> str | None:
    raw = normalize_term(value)
    if not raw:
        return None
    for code, meta in LOCALES.items():
        if normalize_term(code) == raw or normalize_term(meta["name"]) == raw:
            return code
        for alias in meta.get("aliases", ()):
            if normalize_term(alias) == raw:
                return code
    compact = raw.replace(" ", "")
    fallback = {
        "portugues": "pt-BR", "portuguesbrasil": "pt-BR", "ptbr": "pt-BR",
        "english": "en-US", "ingles": "en-US", "enus": "en-US", "engb": "en-GB",
        "spanish": "es-ES", "espanol": "es-ES", "espanhol": "es-ES",
        "italian": "it-IT", "italiano": "it-IT", "french": "fr-FR", "francais": "fr-FR", "frances": "fr-FR",
        "japanese": "ja-JP", "japones": "ja-JP", "polish": "pl-PL", "polones": "pl-PL",
        "korean": "ko-KR", "coreano": "ko-KR", "greek": "el-GR", "grego": "el-GR",
        "ancientgreek": "grc-GR", "gregoantigo": "grc-GR", "latin": "la-x-classical", "latim": "la-x-classical",
        "arabic": "ar-001", "arabe": "ar-001", "egyptianarabic": "ar-EG", "arabeegipcio": "ar-EG",
        "ancientegyptian": "egy-EG", "egipcioantigo": "egy-EG",
    }
    return fallback.get(compact)


def _strip_wake_prefix(raw: str) -> str:
    value = str(raw or "").strip()
    normalized = normalize_term(value)
    prefixes = ("ei star ", "ok star ", "ola star ", "hey star ", "star ")
    for prefix in prefixes:
        if normalized.startswith(prefix):
            return value[len(prefix):].strip() if len(value) >= len(prefix) else normalized[len(prefix):].strip()
    return value


class LanguageManager:
    """Fonte única de verdade para idioma ativo e tradução da superfície.

    Conhecimento permanece canônico em pt-BR. Os 18 perfis são camadas de entrada,
    saída, UI e léxico; não duplicam fatos pelo projeto.
    """

    def __init__(self, settings_path=SETTINGS_FILE, dictionary=None, localization=None):
        self.settings_path = Path(settings_path)
        self.dictionary = dictionary or OfflineDictionaryStore()
        self.expressions = ExpressionCatalog()
        self.localization = localization or GlobalLocalizationEngine(dictionary=self.dictionary, expressions=self.expressions)
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
        self.settings_path.write_text(json.dumps({"locale": self.locale}, ensure_ascii=False, indent=2), encoding="utf-8")

    def set_locale(self, locale: str) -> str:
        resolved = resolve_locale(locale) or (locale if locale in LOCALES else None)
        if resolved is None:
            raise ValueError(f"Idioma não suportado: {locale}")
        self.locale = resolved; self._save(); return self.locale

    def cycle(self, steps: int = 1) -> str:
        index = LOCALE_ORDER.index(self.locale) if self.locale in LOCALE_ORDER else 0
        self.locale = LOCALE_ORDER[(index + int(steps)) % len(LOCALE_ORDER)]
        self._save(); return self.locale

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
        direct = self.localization.static(text, target)
        if direct is not None:
            return direct
        # Para novos idiomas modernos, usa MT somente se o modelo Argos já estiver
        # instalado localmente. Sem pacote, preserva o texto: nunca acessa internet.
        outcome = self.localization.translate(str(text), target, "pt-BR")
        return outcome.text if outcome.complete else str(text)

    def stats(self) -> dict:
        expression = self.expressions.stats()
        profiles = profile_stats()
        localization = self.localization.status()
        return {
            "language_families": profiles["language_families"],
            "locale_profiles": profiles["locale_profiles"],
            "modern_locales": profiles["modern_locales"],
            "historical_locales": profiles["historical_locales"],
            "curated_expression_families": expression["language_families"],
            "curated_locale_surfaces": expression["locale_profiles"],
            "base_expressions": expression["base_expressions"],
            "semantic_concepts_per_curated_language": expression["semantic_concepts_per_language"],
            "variants_per_concept": expression["variants_per_concept"],
            "contents_per_curated_language": expression["contents_per_language"],
            "total_semantic_contents": expression["total_semantic_contents"],
            "selected_locale": self.locale,
            "dictionary_sources": self.dictionary.source_stats(),
            "dictionary_seed_entries": self.dictionary.seed_size(),
            "full_dictionary_index_ready": self.dictionary.full_index_ready,
            "global_localization": localization,
            "knowledge_duplication_per_language": False,
            "historical_mt_claimed": False,
        }

    def detect_locale(self, text: str) -> str:
        hit = self.expressions.match(text)
        if hit:
            return hit[1]
        # Sinais de escrita permitem detectar famílias novas mesmo sem um dicionário
        # completo materializado; ambiguidades latinas permanecem no locale ativo.
        value = str(text or "")
        if any("\u3040" <= ch <= "\u30ff" for ch in value): return "ja-JP"
        if any("\uac00" <= ch <= "\ud7af" for ch in value): return "ko-KR"
        if any("\u0600" <= ch <= "\u06ff" for ch in value): return "ar-001"
        if any("\u0370" <= ch <= "\u03ff" for ch in value):
            return "grc-GR" if self.locale == "grc-GR" else "el-GR"
        norm = normalize_term(value)
        for locale in LOCALE_ORDER:
            if self.dictionary.lookup(norm, locale, "pt-BR") is not None:
                return locale
        return self.locale if self.locale in LOCALES else DEFAULT_LOCALE

    def translate_with_report(self, text: str, target_locale: str, source_locale: str | None = None) -> TranslationOutcome:
        target = resolve_locale(target_locale) or (target_locale if target_locale in LOCALES else None)
        source = source_locale if source_locale in LOCALES else self.detect_locale(text)
        if target is None:
            return TranslationOutcome(str(text), source, str(target_locale), "identity", False, reason="unsupported-locale")
        return self.localization.translate(str(text), target, source)

    def translate(self, text: str, target_locale: str, source_locale: str | None = None) -> str | None:
        outcome = self.translate_with_report(text, target_locale, source_locale)
        return outcome.text if outcome.complete else None

    def translate_to_portuguese(self, text: str) -> str:
        if self.locale == "pt-BR": return str(text)
        outcome = self.translate_with_report(text, "pt-BR", self.locale)
        return outcome.text if outcome.complete else str(text)

    def translate_response(self, text: str) -> str:
        if self.locale == "pt-BR": return str(text)
        return self.translate_with_report(text, self.locale, "pt-BR").text

    def handle_command(self, text: str) -> str | None:
        raw = _strip_wake_prefix(str(text or "").strip())
        norm = normalize_term(raw)
        if not norm: return None

        set_prefixes = (
            "mude para ", "muda para ", "troque para ", "troca para ", "idioma ", "fale em ",
            "switch to ", "change language to ", "speak ", "cambia a ", "cambiar a ", "habla ",
            "passa a ", "cambia lingua in ", "parla ", "passe en ", "change de langue vers ", "parle ",
        )
        for prefix in set_prefixes:
            p = normalize_term(prefix)
            if norm.startswith(p):
                tail = norm[len(p):].strip()
                locale = resolve_locale(tail)
                if locale:
                    self.set_locale(locale)
                    return self.message("language_changed", locale, display=self.display(locale))

        # Comandos diretos úteis nas novas interfaces/idiomas.
        direct_switches = {
            "日本語": "ja-JP", "polski": "pl-PL", "한국어": "ko-KR", "ελληνικά": "el-GR",
            "العربية": "ar-001", "العربية المصرية": "ar-EG", "latin": "la-x-classical",
            "lingua latina": "la-x-classical", "ancient greek": "grc-GR",
        }
        if raw.strip().casefold() in {key.casefold() for key in direct_switches}:
            for key, locale in direct_switches.items():
                if raw.strip().casefold() == key.casefold():
                    self.set_locale(locale); return self.message("language_changed", locale, display=self.display(locale))

        if norm in {"qual idioma", "qual idioma esta ativo", "idioma atual", "current language", "que idioma", "lingua atual", "idioma actual", "langue actuelle", "lingua corrente"}:
            return self.message("current_language", display=self.display())

        markers = (" para ", " to ", " al ", " a ", " en ", " in ")
        translation_starts = ("traduza ", "traduz ", "translate ", "traduce ", "traduci ", "traduis ")
        lowered = raw.lower().strip()
        for start in translation_starts:
            if lowered.startswith(start):
                body = raw[len(start):].strip()
                for marker in markers:
                    pos = body.lower().rfind(marker)
                    if pos <= 0: continue
                    source_text = body[:pos].strip(" \"'“”")
                    target_text = body[pos + len(marker):].strip(" \"'“”?.!")
                    target = resolve_locale(target_text)
                    if not target: continue
                    source = self.detect_locale(source_text)
                    outcome = self.translate_with_report(source_text, target, source)
                    if outcome.complete:
                        return f"{outcome.text}  [{self.display(target)} • {outcome.backend}]"
                    return self.message("translation_missing", locale=self.locale, text=source_text)
        return None
