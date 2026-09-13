"""Dicionário offline multilíngue da STAR.

Dumps grandes permanecem fora do Git; o índice SQLite é materializado localmente e
funciona sem rede. O registro de fontes diferencia dados ingeríveis de referências
históricas que exigem respeito à licença/termos de cada corpus.
"""
from __future__ import annotations

from pathlib import Path
import re
import sqlite3
import unicodedata

from core.language_profiles import LOCALES

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "runtime" / "language" / "dictionaries.sqlite3"


def _source(id_, name, url, license_, kind, *, ingest="compatible-local-dataset"):
    return {"id": id_, "name": name, "url": url, "license": license_, "kind": kind, "ingest": ingest}


DICTIONARY_SOURCES = {
    "pt": (
        _source("kaikki-pt", "Kaikki/Wiktionary Português", "https://kaikki.org/ptwiktionary/", "CC-BY-SA/GFDL", "dictionary"),
        _source("kaikki-en-pt", "Kaikki English Wiktionary — Portuguese", "https://kaikki.org/dictionary/Portuguese/", "CC-BY-SA/GFDL", "dictionary"),
        _source("freedict-por", "FreeDict Portuguese dictionaries", "https://freedict.org/downloads/", "open-per-dataset", "bilingual"),
        _source("omw-por", "Open Multilingual Wordnet — Portuguese", "https://github.com/globalwordnet/OMW", "open-per-wordnet", "wordnet"),
        _source("apertium-por", "Apertium Portuguese lexical data", "https://github.com/apertium/apertium-por", "GPL", "lexicon"),
    ),
    "en": (
        _source("oewn", "Open English WordNet", "https://en-word.net/", "CC-BY-4.0", "wordnet"),
        _source("kaikki-en", "Kaikki/Wiktionary English", "https://kaikki.org/dictionary/English/", "CC-BY-SA/GFDL", "dictionary"),
        _source("freedict-eng", "FreeDict English dictionaries", "https://freedict.org/downloads/", "open-per-dataset", "bilingual"),
        _source("omw-eng", "Open Multilingual Wordnet — English", "https://github.com/globalwordnet/OMW", "open-per-wordnet", "wordnet"),
        _source("wordfreq-en", "Wiktionary/Wiktextract English lexical data", "https://github.com/tatuylonen/wiktextract", "Wiktionary CC-BY-SA/GFDL", "lexicon"),
    ),
    "es": (
        _source("kaikki-es", "Kaikki/Wiktionary Español", "https://kaikki.org/eswiktionary/", "CC-BY-SA/GFDL", "dictionary"),
        _source("kaikki-en-es", "Kaikki English Wiktionary — Spanish", "https://kaikki.org/dictionary/Spanish/", "CC-BY-SA/GFDL", "dictionary"),
        _source("freedict-spa", "FreeDict Spanish dictionaries", "https://freedict.org/downloads/", "open-per-dataset", "bilingual"),
        _source("omw-spa", "Open Multilingual Wordnet — Spanish", "https://github.com/globalwordnet/OMW", "open-per-wordnet", "wordnet"),
        _source("apertium-spa", "Apertium Spanish lexical data", "https://github.com/apertium/apertium-spa", "GPL", "lexicon"),
    ),
    "it": (
        _source("kaikki-it", "Kaikki/Wiktionary Italiano", "https://kaikki.org/itwiktionary/", "CC-BY-SA/GFDL", "dictionary"),
        _source("kaikki-en-it", "Kaikki English Wiktionary — Italian", "https://kaikki.org/dictionary/Italian/", "CC-BY-SA/GFDL", "dictionary"),
        _source("freedict-ita", "FreeDict Italian dictionaries", "https://freedict.org/downloads/", "open-per-dataset", "bilingual"),
        _source("omw-ita", "Open Multilingual Wordnet — Italian", "https://github.com/globalwordnet/OMW", "open-per-wordnet", "wordnet"),
        _source("apertium-ita", "Apertium Italian lexical data", "https://github.com/apertium/apertium-ita", "GPL", "lexicon"),
    ),
    "fr": (
        _source("kaikki-fr", "Kaikki/Wiktionary Français", "https://kaikki.org/frwiktionary/", "CC-BY-SA/GFDL", "dictionary"),
        _source("kaikki-en-fr", "Kaikki English Wiktionary — French", "https://kaikki.org/dictionary/French/", "CC-BY-SA/GFDL", "dictionary"),
        _source("freedict-fra", "FreeDict French dictionaries", "https://freedict.org/downloads/", "open-per-dataset", "bilingual"),
        _source("omw-fra", "Open Multilingual Wordnet — French", "https://github.com/globalwordnet/OMW", "open-per-wordnet", "wordnet"),
        _source("apertium-fra", "Apertium French lexical data", "https://github.com/apertium/apertium-fra", "GPL", "lexicon"),
    ),
    "ja": (
        _source("kaikki-ja", "Kaikki/Wiktionary 日本語", "https://kaikki.org/jawiktionary/", "CC-BY-SA/GFDL", "dictionary"),
        _source("kaikki-en-ja", "Kaikki English Wiktionary — Japanese", "https://kaikki.org/dictionary/Japanese/", "CC-BY-SA/GFDL", "dictionary"),
        _source("jmdict", "JMdict/EDICT", "https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project", "EDRDG licence", "dictionary"),
        _source("ud-ja-gsd", "Universal Dependencies Japanese GSD", "https://github.com/UniversalDependencies/UD_Japanese-GSD", "CC-BY-SA", "corpus"),
        _source("tatoeba-ja", "Tatoeba Japanese", "https://tatoeba.org/", "CC-BY-2.0", "parallel-corpus"),
    ),
    "pl": (
        _source("kaikki-pl", "Kaikki/Wiktionary Polski", "https://kaikki.org/plwiktionary/", "CC-BY-SA/GFDL", "dictionary"),
        _source("kaikki-en-pl", "Kaikki English Wiktionary — Polish", "https://kaikki.org/dictionary/Polish/", "CC-BY-SA/GFDL", "dictionary"),
        _source("freedict-pol", "FreeDict Polish dictionaries", "https://freedict.org/downloads/", "open-per-dataset", "bilingual"),
        _source("omw-pol", "Open Multilingual Wordnet — Polish", "https://github.com/globalwordnet/OMW", "open-per-wordnet", "wordnet"),
        _source("tatoeba-pl", "Tatoeba Polish", "https://tatoeba.org/", "CC-BY-2.0", "parallel-corpus"),
    ),
    "ko": (
        _source("kaikki-ko", "Kaikki/Wiktionary 한국어", "https://kaikki.org/kowiktionary/", "CC-BY-SA/GFDL", "dictionary"),
        _source("kaikki-en-ko", "Kaikki English Wiktionary — Korean", "https://kaikki.org/dictionary/Korean/", "CC-BY-SA/GFDL", "dictionary"),
        _source("ud-ko-gsd", "Universal Dependencies Korean GSD", "https://github.com/UniversalDependencies/UD_Korean-GSD", "CC-BY-SA", "corpus"),
        _source("ud-ko-ksl", "Universal Dependencies Korean KSL", "https://github.com/UniversalDependencies/UD_Korean-KSL", "CC-BY-SA", "corpus"),
        _source("tatoeba-ko", "Tatoeba Korean", "https://tatoeba.org/", "CC-BY-2.0", "parallel-corpus"),
    ),
    "el": (
        _source("kaikki-el", "Kaikki/Wiktionary Ελληνικά", "https://kaikki.org/elwiktionary/", "CC-BY-SA/GFDL", "dictionary"),
        _source("kaikki-en-el", "Kaikki English Wiktionary — Greek", "https://kaikki.org/dictionary/Greek/", "CC-BY-SA/GFDL", "dictionary"),
        _source("freedict-ell", "FreeDict Modern Greek dictionaries", "https://freedict.org/downloads/", "open-per-dataset", "bilingual"),
        _source("ud-el-gdt", "Universal Dependencies Greek GDT", "https://github.com/UniversalDependencies/UD_Greek-GDT", "CC-BY-SA", "corpus"),
        _source("tatoeba-el", "Tatoeba Greek", "https://tatoeba.org/", "CC-BY-2.0", "parallel-corpus"),
    ),
    "grc": (
        _source("kaikki-grc", "Kaikki/Wiktionary Ancient Greek", "https://kaikki.org/dictionary/Ancient%20Greek/", "CC-BY-SA/GFDL", "dictionary"),
        _source("perseus-grc", "Perseus Digital Library Greek resources", "https://www.perseus.tufts.edu/", "per-resource", "historical-corpus"),
        _source("ud-grc-perseus", "UD Ancient Greek Perseus", "https://github.com/UniversalDependencies/UD_Ancient_Greek-Perseus", "CC-BY-SA", "corpus"),
        _source("ud-grc-proiel", "UD Ancient Greek PROIEL", "https://github.com/UniversalDependencies/UD_Ancient_Greek-PROIEL", "CC-BY-SA", "corpus"),
        _source("ud-grc-ptnk", "UD Ancient Greek PTNK", "https://github.com/UniversalDependencies/UD_Ancient_Greek-PTNK", "CC-BY-SA", "corpus"),
    ),
    "la": (
        _source("kaikki-la", "Kaikki/Wiktionary Latin", "https://kaikki.org/lawiktionary/", "CC-BY-SA/GFDL", "dictionary"),
        _source("kaikki-en-la", "Kaikki English Wiktionary — Latin", "https://kaikki.org/dictionary/Latin/", "CC-BY-SA/GFDL", "dictionary"),
        _source("freedict-lat", "FreeDict Latin dictionaries", "https://freedict.org/downloads/", "open-per-dataset", "bilingual"),
        _source("ud-la-perseus", "UD Latin Perseus", "https://github.com/UniversalDependencies/UD_Latin-Perseus", "CC-BY-SA", "corpus"),
        _source("ud-la-proiel", "UD Latin PROIEL", "https://github.com/UniversalDependencies/UD_Latin-PROIEL", "CC-BY-SA", "corpus"),
        _source("ud-la-ittb", "UD Latin ITTB", "https://github.com/UniversalDependencies/UD_Latin-ITTB", "CC-BY-SA", "corpus"),
    ),
    "ar": (
        _source("kaikki-ar", "Kaikki/Wiktionary العربية", "https://kaikki.org/arwiktionary/", "CC-BY-SA/GFDL", "dictionary"),
        _source("kaikki-en-ar", "Kaikki English Wiktionary — Arabic", "https://kaikki.org/dictionary/Arabic/", "CC-BY-SA/GFDL", "dictionary"),
        _source("freedict-ara", "FreeDict Arabic dictionaries", "https://freedict.org/downloads/", "open-per-dataset", "bilingual"),
        _source("ud-ar-padt", "Universal Dependencies Arabic PADT", "https://github.com/UniversalDependencies/UD_Arabic-PADT", "CC-BY-SA", "corpus"),
        _source("tatoeba-ar", "Tatoeba Arabic", "https://tatoeba.org/", "CC-BY-2.0", "parallel-corpus"),
    ),
    "egy": (
        _source("kaikki-egy", "Kaikki/Wiktionary Ancient Egyptian entries", "https://kaikki.org/", "CC-BY-SA/GFDL", "dictionary"),
        _source("wiktextract-egy", "Wiktionary/Wiktextract Ancient Egyptian", "https://github.com/tatuylonen/wiktextract", "Wiktionary CC-BY-SA/GFDL", "lexicon"),
        _source("unicode-egy", "Unicode Egyptian Hieroglyphs repertoire", "https://www.unicode.org/charts/", "Unicode terms", "script-reference"),
        _source("tla-egy", "Thesaurus Linguae Aegyptiae", "https://thesaurus-linguae-aegyptiae.de/", "reference terms apply", "historical-reference", ingest="reference-only"),
        _source("ramses-egy", "Ramses Online", "https://ramses.ulg.ac.be/", "reference terms apply", "historical-reference", ingest="reference-only"),
    ),
}

# Pequeno fallback imediato. Cobertura ampla vem do SQLite local materializado.
_SEED_CONCEPTS = (
    {"pt-BR":"olá","en-US":"hello","en-GB":"hello","es-ES":"hola","it-IT":"ciao","fr-FR":"bonjour","ja-JP":"こんにちは","pl-PL":"cześć","ko-KR":"안녕하세요","el-GR":"γεια","ar-001":"مرحبا","ar-EG":"أهلاً","grc-GR":"χαῖρε","la-x-classical":"salve","la-x-late":"salve","la-x-medieval":"salve","la-x-neo":"salve"},
    {"pt-BR":"sim","en-US":"yes","en-GB":"yes","es-ES":"sí","it-IT":"sì","fr-FR":"oui","ja-JP":"はい","pl-PL":"tak","ko-KR":"네","el-GR":"ναι","ar-001":"نعم","ar-EG":"أيوه","grc-GR":"ναί","la-x-classical":"ita","la-x-late":"ita","la-x-medieval":"ita","la-x-neo":"ita"},
    {"pt-BR":"não","en-US":"no","en-GB":"no","es-ES":"no","it-IT":"no","fr-FR":"non","ja-JP":"いいえ","pl-PL":"nie","ko-KR":"아니요","el-GR":"όχι","ar-001":"لا","ar-EG":"لأ","grc-GR":"οὔ","la-x-classical":"non","la-x-late":"non","la-x-medieval":"non","la-x-neo":"non"},
    {"pt-BR":"obrigado","en-US":"thanks","en-GB":"thanks","es-ES":"gracias","it-IT":"grazie","fr-FR":"merci","ja-JP":"ありがとう","pl-PL":"dziękuję","ko-KR":"감사합니다","el-GR":"ευχαριστώ","ar-001":"شكرا","ar-EG":"شكراً","grc-GR":"χάριν σοι ἔχω","la-x-classical":"gratias tibi ago","la-x-late":"gratias","la-x-medieval":"gratias","la-x-neo":"gratias"},
    {"pt-BR":"hoje","en-US":"today","en-GB":"today","es-ES":"hoy","it-IT":"oggi","fr-FR":"aujourd'hui","ja-JP":"今日","pl-PL":"dzisiaj","ko-KR":"오늘","el-GR":"σήμερα","ar-001":"اليوم","ar-EG":"النهارده"},
    {"pt-BR":"tempo","en-US":"time","en-GB":"time","es-ES":"tiempo","it-IT":"tempo","fr-FR":"temps","ja-JP":"時間","pl-PL":"czas","ko-KR":"시간","el-GR":"χρόνος","ar-001":"وقت","ar-EG":"وقت","grc-GR":"χρόνος","la-x-classical":"tempus","la-x-late":"tempus","la-x-medieval":"tempus","la-x-neo":"tempus"},
    {"pt-BR":"clima","en-US":"weather","en-GB":"weather","es-ES":"clima","it-IT":"meteo","fr-FR":"météo","ja-JP":"天気","pl-PL":"pogoda","ko-KR":"날씨","el-GR":"καιρός","ar-001":"الطقس","ar-EG":"الجو"},
    {"pt-BR":"física","en-US":"physics","en-GB":"physics","es-ES":"física","it-IT":"fisica","fr-FR":"physique","ja-JP":"物理学","pl-PL":"fizyka","ko-KR":"물리학","el-GR":"φυσική","ar-001":"الفيزياء","ar-EG":"الفيزياء"},
    {"pt-BR":"gravidade","en-US":"gravity","en-GB":"gravity","es-ES":"gravedad","it-IT":"gravità","fr-FR":"gravité","ja-JP":"重力","pl-PL":"grawitacja","ko-KR":"중력","el-GR":"βαρύτητα","ar-001":"الجاذبية","ar-EG":"الجاذبية"},
    {"pt-BR":"amor","en-US":"love","en-GB":"love","es-ES":"amor","it-IT":"amore","fr-FR":"amour","ja-JP":"愛","pl-PL":"miłość","ko-KR":"사랑","el-GR":"αγάπη","ar-001":"حب","ar-EG":"حب","grc-GR":"ἀγάπη","la-x-classical":"amor","la-x-late":"amor","la-x-medieval":"amor","la-x-neo":"amor"},
    # Mantém seeds legados exigidos por versões anteriores.
    {"pt-BR":"dinheiro","en-US":"money","en-GB":"money","es-ES":"dinero","it-IT":"soldi","fr-FR":"argent"},
)


def normalize_term(text: str) -> str:
    """Normalização Unicode sem apagar alfabetos não latinos."""
    value = unicodedata.normalize("NFKC", str(text or "")).casefold()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^\w\s'’\-\u200c\u200d]", " ", value, flags=re.UNICODE)
    return " ".join(value.replace("_", " ").split())


class OfflineDictionaryStore:
    def __init__(self, db_path: Path | str = DEFAULT_DB):
        self.db_path = Path(db_path)
        self._seed = {}
        for concept in _SEED_CONCEPTS:
            for locale, surface in concept.items():
                self._seed[(locale, normalize_term(surface))] = concept

    @staticmethod
    def source_stats() -> dict:
        return {family: len(items) for family, items in DICTIONARY_SOURCES.items()}

    @property
    def full_index_ready(self) -> bool:
        return self.db_path.is_file() and self.db_path.stat().st_size > 0

    def lookup(self, term: str, source_locale: str, target_locale: str) -> str | None:
        norm = normalize_term(term)
        if not norm or source_locale not in LOCALES or target_locale not in LOCALES:
            return None
        if source_locale == target_locale:
            return str(term)
        if self.full_index_ready:
            try:
                with sqlite3.connect(self.db_path) as db:
                    row = db.execute(
                        "SELECT translation FROM translations WHERE source_locale=? AND target_locale=? AND term_norm=? ORDER BY priority DESC LIMIT 1",
                        (source_locale, target_locale, norm),
                    ).fetchone()
                if row and row[0]:
                    return str(row[0])
            except (sqlite3.Error, OSError):
                pass
        concept = self._seed.get((source_locale, norm))
        if concept is None:
            return None
        return concept.get(target_locale)

    def seed_size(self) -> int:
        return len(_SEED_CONCEPTS)
