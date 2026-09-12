"""Dicionário offline da STAR e registro auditável de fontes lexicais abertas.

Os dumps grandes não são versionados no Git. O índice SQLite local pode ser gerado
por scripts/build_offline_dictionaries.py e depois funciona sem internet. Um léxico
compacto embutido garante traduções comuns imediatamente.
"""
from __future__ import annotations

from pathlib import Path
import re
import sqlite3
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "runtime" / "language" / "dictionaries.sqlite3"

DICTIONARY_SOURCES = {
    "pt": (
        {"id": "kaikki-pt", "name": "Kaikki/Wiktionary Português", "url": "https://kaikki.org/ptwiktionary/", "license": "CC-BY-SA/GFDL", "kind": "dictionary"},
        {"id": "kaikki-en-pt", "name": "Kaikki English Wiktionary — Portuguese", "url": "https://kaikki.org/dictionary/Portuguese/", "license": "CC-BY-SA/GFDL", "kind": "dictionary"},
        {"id": "freedict-por", "name": "FreeDict Portuguese dictionaries", "url": "https://freedict.org/downloads/", "license": "open-per-dataset", "kind": "bilingual"},
        {"id": "omw-por", "name": "Open Multilingual Wordnet — Portuguese", "url": "https://github.com/globalwordnet/OMW", "license": "open-per-wordnet", "kind": "wordnet"},
        {"id": "apertium-por", "name": "Apertium Portuguese lexical data", "url": "https://github.com/apertium/apertium-por", "license": "GPL", "kind": "lexicon"},
    ),
    "en": (
        {"id": "oewn-2025", "name": "Open English WordNet 2025", "url": "https://en-word.net/downloads", "license": "CC-BY-4.0", "kind": "wordnet"},
        {"id": "kaikki-en", "name": "Kaikki/Wiktionary English", "url": "https://kaikki.org/dictionary/English/", "license": "CC-BY-SA/GFDL", "kind": "dictionary"},
        {"id": "freedict-eng", "name": "FreeDict English dictionaries", "url": "https://freedict.org/downloads/", "license": "open-per-dataset", "kind": "bilingual"},
        {"id": "omw-eng", "name": "Open Multilingual Wordnet — English", "url": "https://github.com/globalwordnet/OMW", "license": "open-per-wordnet", "kind": "wordnet"},
        {"id": "apertium-eng", "name": "Apertium English lexical data", "url": "https://github.com/apertium/apertium-eng", "license": "GPL", "kind": "lexicon"},
    ),
    "es": (
        {"id": "kaikki-es", "name": "Kaikki/Wiktionary Español", "url": "https://kaikki.org/eswiktionary/", "license": "CC-BY-SA/GFDL", "kind": "dictionary"},
        {"id": "kaikki-en-es", "name": "Kaikki English Wiktionary — Spanish", "url": "https://kaikki.org/dictionary/Spanish/", "license": "CC-BY-SA/GFDL", "kind": "dictionary"},
        {"id": "freedict-spa", "name": "FreeDict Spanish dictionaries", "url": "https://freedict.org/downloads/", "license": "open-per-dataset", "kind": "bilingual"},
        {"id": "omw-spa", "name": "Open Multilingual Wordnet — Spanish", "url": "https://github.com/globalwordnet/OMW", "license": "open-per-wordnet", "kind": "wordnet"},
        {"id": "apertium-spa", "name": "Apertium Spanish lexical data", "url": "https://github.com/apertium/apertium-spa", "license": "GPL", "kind": "lexicon"},
    ),
    "it": (
        {"id": "kaikki-it", "name": "Kaikki/Wiktionary Italiano", "url": "https://kaikki.org/itwiktionary/", "license": "CC-BY-SA/GFDL", "kind": "dictionary"},
        {"id": "kaikki-en-it", "name": "Kaikki English Wiktionary — Italian", "url": "https://kaikki.org/dictionary/Italian/", "license": "CC-BY-SA/GFDL", "kind": "dictionary"},
        {"id": "freedict-ita", "name": "FreeDict Italian dictionaries", "url": "https://freedict.org/downloads/", "license": "open-per-dataset", "kind": "bilingual"},
        {"id": "omw-ita", "name": "Open Multilingual Wordnet — Italian", "url": "https://github.com/globalwordnet/OMW", "license": "open-per-wordnet", "kind": "wordnet"},
        {"id": "apertium-ita", "name": "Apertium Italian lexical data", "url": "https://github.com/apertium/apertium-ita", "license": "GPL", "kind": "lexicon"},
    ),
    "fr": (
        {"id": "kaikki-fr", "name": "Kaikki/Wiktionary Français", "url": "https://kaikki.org/frwiktionary/", "license": "CC-BY-SA/GFDL", "kind": "dictionary"},
        {"id": "kaikki-en-fr", "name": "Kaikki English Wiktionary — French", "url": "https://kaikki.org/dictionary/French/", "license": "CC-BY-SA/GFDL", "kind": "dictionary"},
        {"id": "freedict-fra", "name": "FreeDict French dictionaries", "url": "https://freedict.org/downloads/", "license": "open-per-dataset", "kind": "bilingual"},
        {"id": "omw-fra", "name": "Open Multilingual Wordnet — French", "url": "https://github.com/globalwordnet/OMW", "license": "open-per-wordnet", "kind": "wordnet"},
        {"id": "apertium-fra", "name": "Apertium French lexical data", "url": "https://github.com/apertium/apertium-fra", "license": "GPL", "kind": "lexicon"},
    ),
}

# Conceitos pequenos e inequívocos para fallback imediato. O banco completo, quando
# materializado, tem prioridade e pode conter múltiplos sentidos/fontes.
_SEED_ROWS = (
    ("hello", "olá", "hello", "hello", "hola", "ciao", "bonjour"),
    ("friend", "amigo", "friend", "friend", "amigo", "amico", "ami"),
    ("man", "cara", "guy", "bloke", "tío", "tipo", "mec"),
    ("good", "bom", "good", "good", "bueno", "buono", "bon"),
    ("bad", "ruim", "bad", "bad", "malo", "cattivo", "mauvais"),
    ("yes", "sim", "yes", "yes", "sí", "sì", "oui"),
    ("no", "não", "no", "no", "no", "no", "non"),
    ("thanks", "obrigado", "thanks", "thanks", "gracias", "grazie", "merci"),
    ("please", "por favor", "please", "please", "por favor", "per favore", "s'il vous plaît"),
    ("sorry", "desculpa", "sorry", "sorry", "perdón", "scusa", "désolé"),
    ("today", "hoje", "today", "today", "hoy", "oggi", "aujourd'hui"),
    ("tomorrow", "amanhã", "tomorrow", "tomorrow", "mañana", "domani", "demain"),
    ("yesterday", "ontem", "yesterday", "yesterday", "ayer", "ieri", "hier"),
    ("home", "casa", "home", "home", "casa", "casa", "maison"),
    ("work", "trabalho", "work", "work", "trabajo", "lavoro", "travail"),
    ("music", "música", "music", "music", "música", "musica", "musique"),
    ("water", "água", "water", "water", "agua", "acqua", "eau"),
    ("food", "comida", "food", "food", "comida", "cibo", "nourriture"),
    ("time", "tempo", "time", "time", "tiempo", "tempo", "temps"),
    ("love", "amor", "love", "love", "amor", "amore", "amour"),
    ("peace", "paz", "peace", "peace", "paz", "pace", "paix"),
    ("calm", "calma", "calm", "calm", "calma", "calma", "calme"),
    ("money", "dinheiro", "money", "money", "dinero", "soldi", "argent"),
    ("tired", "cansado", "tired", "tired", "cansado", "stanco", "fatigué"),
    ("hungry", "faminto", "hungry", "hungry", "hambriento", "affamato", "affamé"),
    ("beautiful", "bonito", "beautiful", "beautiful", "bonito", "bello", "beau"),
    ("cold", "frio", "cold", "cold", "frío", "freddo", "froid"),
    ("hot", "quente", "hot", "hot", "caliente", "caldo", "chaud"),
    ("rain", "chuva", "rain", "rain", "lluvia", "pioggia", "pluie"),
    ("sun", "sol", "sun", "sun", "sol", "sole", "soleil"),
    ("physics", "física", "physics", "physics", "física", "fisica", "physique"),
    ("energy", "energia", "energy", "energy", "energía", "energia", "énergie"),
    ("force", "força", "force", "force", "fuerza", "forza", "force"),
    ("velocity", "velocidade", "velocity", "velocity", "velocidad", "velocità", "vitesse"),
    ("mass", "massa", "mass", "mass", "masa", "massa", "masse"),
    ("gravity", "gravidade", "gravity", "gravity", "gravedad", "gravità", "gravité"),
    ("light", "luz", "light", "light", "luz", "luce", "lumière"),
    ("wave", "onda", "wave", "wave", "onda", "onda", "onde"),
    ("particle", "partícula", "particle", "particle", "partícula", "particella", "particule"),
    ("space", "espaço", "space", "space", "espacio", "spazio", "espace"),
)

_LOCALE_COLUMNS = {"pt-BR": 1, "en-US": 2, "en-GB": 3, "es-ES": 4, "it-IT": 5, "fr-FR": 6}


def normalize_term(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").lower())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9\s'-]", " ", value).split())


class OfflineDictionaryStore:
    def __init__(self, db_path: Path | str = DEFAULT_DB):
        self.db_path = Path(db_path)
        self._seed = {}
        for row in _SEED_ROWS:
            for locale, col in _LOCALE_COLUMNS.items():
                key = (locale, normalize_term(row[col]))
                self._seed[key] = row

    @staticmethod
    def source_stats() -> dict:
        return {family: len(items) for family, items in DICTIONARY_SOURCES.items()}

    @property
    def full_index_ready(self) -> bool:
        return self.db_path.is_file() and self.db_path.stat().st_size > 0

    def lookup(self, term: str, source_locale: str, target_locale: str) -> str | None:
        norm = normalize_term(term)
        if not norm or source_locale not in _LOCALE_COLUMNS or target_locale not in _LOCALE_COLUMNS:
            return None
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
        seed = self._seed.get((source_locale, norm))
        if seed is None:
            return None
        return seed[_LOCALE_COLUMNS[target_locale]]

    def seed_size(self) -> int:
        return len(_SEED_ROWS)
