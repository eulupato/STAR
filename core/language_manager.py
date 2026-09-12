"""Gerenciador de idioma, tradução contextual e comandos de voz offline da STAR."""
from __future__ import annotations

import json
from pathlib import Path
import re

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


class LanguageManager:
    def __init__(self, settings_path: Path | str = SETTINGS_FILE, dictionary: OfflineDictionaryStore | None = None):
        self.settings_path = Path(settings_path)
        self.dictionary = dictionary or OfflineDictionaryStore()
        self.expressions = ExpressionCatalog()
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

    def stats(self) -> dict:
        expression = self.expressions.stats()
        return {
            **expression,
            "selected_locale": self.locale,
            "dictionary_sources": self.dictionary.source_stats(),
            "dictionary_seed_entries": self.dictionary.seed_size(),
            "full_dictionary_index_ready": self.dictionary.full_index_ready,
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

    def translate(self, text: str, target_locale: str, source_locale: str | None = None) -> str | None:
        target = resolve_locale(target_locale) or (target_locale if target_locale in LOCALES else None)
        if target is None:
            return None
        contextual = self.expressions.contextual_equivalent(text, target)
        if contextual:
            return contextual
        source = source_locale if source_locale in LOCALES else self.detect_locale(text)
        exact = self.dictionary.lookup(text, source, target)
        if exact:
            return exact
        # Fallback conservador: traduz somente tokens conhecidos; preserva o resto.
        pieces = re.findall(r"\w+(?:['’-]\w+)*|[^\w\s]+|\s+", str(text), flags=re.UNICODE)
        translated_any = False
        out = []
        for piece in pieces:
            if not piece or piece.isspace() or not any(ch.isalnum() for ch in piece):
                out.append(piece)
                continue
            value = self.dictionary.lookup(piece, source, target)
            if value is None:
                out.append(piece)
            else:
                translated_any = True
                if piece[:1].isupper():
                    value = value[:1].upper() + value[1:]
                out.append(value)
        return "".join(out) if translated_any else None

    def translate_to_portuguese(self, text: str) -> str:
        if self.locale == "pt-BR":
            return str(text)
        return self.translate(text, "pt-BR", self.locale) or str(text)

    def translate_response(self, text: str) -> str:
        if self.locale == "pt-BR":
            return str(text)
        return self.translate(text, self.locale, "pt-BR") or str(text)

    def handle_command(self, text: str) -> str | None:
        raw = str(text or "").strip()
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
                    return f"Idioma da STAR alterado para {self.display(locale)}. O modo permanece offline-first."

        if norm in {"qual idioma", "qual idioma esta ativo", "idioma atual", "current language", "que idioma", "lingua atual"}:
            return f"Idioma atual: {self.display()}."

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
                    result = self.translate(source_text, target, source)
                    if result:
                        return f"{result}  [{self.display(target)} • equivalente contextual/offline]"
                    return (
                        f"Não encontrei '{source_text}' no índice offline atual. "
                        "Não vou inventar uma tradução; atualize/materialize os dicionários locais."
                    )
        return None
