"""Localização global e tradução segura da STAR.

Princípios:
- o conteúdo canônico continua sendo a fonte de verdade;
- idioma altera somente a superfície apresentada;
- IDs, números, fórmulas, caminhos, URLs e código nunca são traduzidos;
- tradução parcial não é apresentada como se fosse completa;
- Argos Translate é opcional/lazy e nunca é baixado no startup.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol

from core.language_catalog import LOCALES, ExpressionCatalog
from core.offline_dictionary import OfflineDictionaryStore, normalize_term

SUPPORTED_LOCALES = tuple(LOCALES)
ARGOS_CODES = {
    "pt-BR": "pt",
    "en-US": "en",
    "en-GB": "en",
    "es-ES": "es",
    "it-IT": "it",
    "fr-FR": "fr",
}


def _row(pt: str, en_us: str, en_gb: str, es: str, it: str, fr: str) -> dict[str, str]:
    return {
        "pt-BR": pt,
        "en-US": en_us,
        "en-GB": en_gb,
        "es-ES": es,
        "it-IT": it,
        "fr-FR": fr,
    }


# Textos fixos de UI/estado são traduzidos deterministicamente, mesmo quando
# nenhum modelo neural estiver instalado. Textos livres continuam pelo pipeline.
STATIC_TEXTS = (
    _row("INICIAR", "START", "START", "INICIAR", "AVVIA", "DÉMARRER"),
    _row("CONFIGURAÇÕES", "SETTINGS", "SETTINGS", "AJUSTES", "IMPOSTAZIONI", "PARAMÈTRES"),
    _row("SAIR", "EXIT", "EXIT", "SALIR", "ESCI", "QUITTER"),
    _row("CHAT", "CHAT", "CHAT", "CHAT", "CHAT", "CHAT"),
    _row("MENU", "MENU", "MENU", "MENÚ", "MENU", "MENU"),
    _row("ILHAS", "ISLANDS", "ISLANDS", "ISLAS", "ISOLE", "ÎLES"),
    _row("Pergunte algo à STAR...", "Ask STAR something...", "Ask STAR something...", "Pregúntale algo a STAR...", "Chiedi qualcosa a STAR...", "Demandez quelque chose à STAR..."),
    _row("ONLINE", "ONLINE", "ONLINE", "EN LÍNEA", "ONLINE", "EN LIGNE"),
    _row("OFFLINE", "OFFLINE", "OFFLINE", "SIN CONEXIÓN", "OFFLINE", "HORS LIGNE"),
    _row("OUVINDO", "LISTENING", "LISTENING", "ESCUCHANDO", "IN ASCOLTO", "ÉCOUTE"),
    _row("PROCESSANDO", "PROCESSING", "PROCESSING", "PROCESANDO", "ELABORAZIONE", "TRAITEMENT"),
    _row("TRANSCRIVENDO", "TRANSCRIBING", "TRANSCRIBING", "TRANSCRIBIENDO", "TRASCRIZIONE", "TRANSCRIPTION"),
    _row("PRONTA", "READY", "READY", "LISTA", "PRONTA", "PRÊTE"),
    _row("PENSANDO", "THINKING", "THINKING", "PENSANDO", "PENSANDO", "RÉFLEXION"),
    _row("RESPONDENDO", "RESPONDING", "RESPONDING", "RESPONDIENDO", "RISPONDENDO", "RÉPONSE"),
    _row("ATENÇÃO", "ATTENTION", "ATTENTION", "ATENCIÓN", "ATTENZIONE", "ATTENTION"),
    _row("VOZ", "VOICE", "VOICE", "VOZ", "VOCE", "VOIX"),
    _row("BUSCA", "SEARCH", "SEARCH", "BÚSQUEDA", "RICERCA", "RECHERCHE"),
    _row("SAÚDE", "HEALTH", "HEALTH", "SALUD", "SALUTE", "SANTÉ"),
    _row("GPS", "GPS", "GPS", "GPS", "GPS", "GPS"),
    _row("VISÃO", "VISION", "VISION", "VISIÓN", "VISIONE", "VISION"),
    _row("PEOPLE", "PEOPLE", "PEOPLE", "PERSONAS", "PERSONE", "PERSONNES"),
    _row("MEDIR", "MEASURE", "MEASURE", "MEDIR", "MISURA", "MESURER"),
    _row("MÍDIA", "MEDIA", "MEDIA", "MULTIMEDIA", "MEDIA", "MÉDIA"),
    _row("CLIMA", "WEATHER", "WEATHER", "CLIMA", "METEO", "MÉTÉO"),
    _row("CONFIG", "SETTINGS", "SETTINGS", "AJUSTES", "IMPOSTAZIONI", "PARAMÈTRES"),
    _row("IDIOMA", "LANGUAGE", "LANGUAGE", "IDIOMA", "LINGUA", "LANGUE"),
    _row("TOQUE PARA FALAR", "TAP TO SPEAK", "TAP TO SPEAK", "TOCA PARA HABLAR", "TOCCA PER PARLARE", "TOUCHEZ POUR PARLER"),
    _row("SEM SENSOR", "NO SENSOR", "NO SENSOR", "SIN SENSOR", "NESSUN SENSORE", "AUCUN CAPTEUR"),
    _row("SENSOR OFF", "SENSOR OFF", "SENSOR OFF", "SENSOR APAGADO", "SENSORE OFF", "CAPTEUR OFF"),
    _row("Nenhuma pessoa cadastrada", "No people registered", "No people registered", "No hay personas registradas", "Nessuna persona registrata", "Aucune personne enregistrée"),
    _row("SELECIONAR IMAGEM", "SELECT IMAGE", "SELECT IMAGE", "SELECCIONAR IMAGEN", "SELEZIONA IMMAGINE", "SÉLECTIONNER UNE IMAGE"),
    _row("ADICIONAR PESSOA", "ADD PERSON", "ADD PERSON", "AÑADIR PERSONA", "AGGIUNGI PERSONA", "AJOUTER UNE PERSONNE"),
    _row("Pressione o núcleo para iniciar a conversa.", "Press the core to start the conversation.", "Press the core to start the conversation.", "Pulsa el núcleo para iniciar la conversación.", "Premi il nucleo per iniziare la conversazione.", "Appuyez sur le noyau pour démarrer la conversation."),
    _row("GIRE  •  PRESSIONE  •  FALE", "TURN  •  PRESS  •  SPEAK", "TURN  •  PRESS  •  SPEAK", "GIRA  •  PULSA  •  HABLA", "RUOTA  •  PREMI  •  PARLA", "TOURNEZ  •  APPUYEZ  •  PARLEZ"),
    _row("GIRE PARA TROCAR • PRESSIONE PARA CONFIRMAR", "TURN TO CHANGE • PRESS TO CONFIRM", "TURN TO CHANGE • PRESS TO CONFIRM", "GIRA PARA CAMBIAR • PULSA PARA CONFIRMAR", "RUOTA PER CAMBIARE • PREMI PER CONFERMARE", "TOURNEZ POUR CHANGER • APPUYEZ POUR CONFIRMER"),
    _row("A seleção vale para texto, voz, traduções e respostas do Core.", "The selection applies to text, voice, translations and Core responses.", "The selection applies to text, voice, translations and Core responses.", "La selección se aplica al texto, la voz, las traducciones y las respuestas del Core.", "La selezione vale per testo, voce, traduzioni e risposte del Core.", "La sélection s'applique au texte, à la voix, aux traductions et aux réponses du Core."),
    _row("Sensor de saúde não conectado.", "Health sensor not connected.", "Health sensor not connected.", "Sensor de salud no conectado.", "Sensore salute non connesso.", "Capteur de santé non connecté."),
    _row("GPS não conectado.", "GPS not connected.", "GPS not connected.", "GPS no conectado.", "GPS non connesso.", "GPS non connecté."),
    _row("Módulo laser não conectado.", "Laser module not connected.", "Laser module not connected.", "Módulo láser no conectado.", "Modulo laser non connesso.", "Module laser non connecté."),
    _row("SIMULAÇÃO — aguardando sensores reais do relógio.", "SIMULATION — waiting for real watch sensors.", "SIMULATION — waiting for real watch sensors.", "SIMULACIÓN — esperando sensores reales del reloj.", "SIMULAZIONE — in attesa dei sensori reali dell'orologio.", "SIMULATION — en attente des capteurs réels de la montre."),
    _row("SIMULAÇÃO — posição real não está sendo lida no PC.", "SIMULATION — real position is not being read on the PC.", "SIMULATION — real position is not being read on the PC.", "SIMULACIÓN — la posición real no se está leyendo en el PC.", "SIMULAZIONE — la posizione reale non viene letta sul PC.", "SIMULATION — la position réelle n'est pas lue sur le PC."),
    _row("SIMULAÇÃO — futuro LaserDistanceProvider.", "SIMULATION — future LaserDistanceProvider.", "SIMULATION — future LaserDistanceProvider.", "SIMULACIÓN — futuro LaserDistanceProvider.", "SIMULAZIONE — futuro LaserDistanceProvider.", "SIMULATION — futur LaserDistanceProvider."),
)

STATIC_INDEX: dict[str, dict[str, str]] = {}
for surfaces in STATIC_TEXTS:
    for surface in surfaces.values():
        key = normalize_term(surface)
        if key:
            STATIC_INDEX[key] = surfaces


MESSAGES = {
    "language_changed": _row(
        "Idioma da STAR alterado para {display}. O modo permanece offline-first.",
        "STAR language changed to {display}. Offline-first mode remains active.",
        "STAR language changed to {display}. Offline-first mode remains active.",
        "Idioma de STAR cambiado a {display}. El modo offline-first sigue activo.",
        "Lingua di STAR cambiata in {display}. La modalità offline-first resta attiva.",
        "Langue de STAR changée vers {display}. Le mode offline-first reste actif.",
    ),
    "current_language": _row(
        "Idioma atual: {display}.",
        "Current language: {display}.",
        "Current language: {display}.",
        "Idioma actual: {display}.",
        "Lingua attuale: {display}.",
        "Langue actuelle : {display}.",
    ),
    "translation_missing": _row(
        "Não encontrei uma tradução completa e confiável para '{text}' no runtime local. Preservei o original para não alterar a informação.",
        "I did not find a complete, reliable translation for '{text}' in the local runtime. I preserved the original so the information is not changed.",
        "I did not find a complete, reliable translation for '{text}' in the local runtime. I preserved the original so the information is not changed.",
        "No encontré una traducción completa y fiable para '{text}' en el runtime local. Conservé el original para no alterar la información.",
        "Non ho trovato una traduzione completa e affidabile per '{text}' nel runtime locale. Ho mantenuto l'originale per non alterare l'informazione.",
        "Je n'ai pas trouvé de traduction complète et fiable pour « {text} » dans le runtime local. J'ai conservé l'original afin de ne pas modifier l'information.",
    ),
    "language_confirmed": _row(
        "Idioma confirmado: {display}",
        "Language confirmed: {display}",
        "Language confirmed: {display}",
        "Idioma confirmado: {display}",
        "Lingua confermata: {display}",
        "Langue confirmée : {display}",
    ),
}


class NeuralTranslationBackend(Protocol):
    name: str

    def translate(self, text: str, source_locale: str, target_locale: str) -> str | None: ...

    def status(self) -> dict: ...


class ArgosTranslationBackend:
    """Backend neural offline opcional.

    O import é lazy. A classe nunca baixa modelos; instalação é responsabilidade
    explícita do script scripts/setup_offline_translation.py.
    """

    name = "argos"

    @staticmethod
    def _modules():
        try:
            import argostranslate.package as package
            import argostranslate.translate as translate
        except (ImportError, OSError):
            return None, None
        return package, translate

    def status(self) -> dict:
        package, translate = self._modules()
        if package is None or translate is None:
            return {"installed": False, "backend": self.name, "pairs": []}
        try:
            packages = package.get_installed_packages()
            pairs = sorted({f"{p.from_code}->{p.to_code}" for p in packages if p.from_code and p.to_code})
        except Exception:
            pairs = []
        return {"installed": True, "backend": self.name, "pairs": pairs}

    def translate(self, text: str, source_locale: str, target_locale: str) -> str | None:
        source = ARGOS_CODES.get(source_locale)
        target = ARGOS_CODES.get(target_locale)
        if not source or not target:
            return None
        if source == target:
            return str(text)
        _, translate = self._modules()
        if translate is None:
            return None
        try:
            value = translate.translate(str(text), source, target)
        except Exception:
            return None
        value = str(value or "").strip()
        return value or None


@dataclass(frozen=True)
class TranslationOutcome:
    text: str
    source_locale: str
    target_locale: str
    backend: str
    complete: bool
    protected_segments: int = 0
    reason: str = ""


_PROTECTED_PATTERNS = (
    re.compile(r"```.*?```", re.S),
    re.compile(r"`[^`\n]+`"),
    re.compile(r"https?://[^\s)\]}>,]+", re.I),
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b[A-Za-z]:\\[^\n\r]+?(?=(?:\s{2,}|$))"),
    re.compile(r"(?<!\w)/(?:[\w.\-]+/)+[\w.\-]+"),
    re.compile(r"\b[A-Z][A-Z0-9]{1,20}(?:-[A-Z0-9]+)*-\d{4,}\b"),
    re.compile(r"\$[^$\n]+\$"),
    re.compile(r"(?<!\w)[+-]?\d+(?:[.,]\d+)?(?:e[+-]?\d+)?(?:\s?(?:%|°[CF]|[A-Za-zµΩ]+(?:/[A-Za-z]+)?))?", re.I),
)


def protect_invariants(text: str) -> tuple[str, dict[str, str]]:
    """Substitui trechos que não podem mudar por placeholders estáveis."""
    value = str(text)
    mapping: dict[str, str] = {}

    def replace(match: re.Match) -> str:
        token = f"__STARPROTECTED{len(mapping):04d}__"
        mapping[token] = match.group(0)
        return token

    for pattern in _PROTECTED_PATTERNS:
        value = pattern.sub(replace, value)
    return value, mapping


def restore_invariants(text: str, mapping: dict[str, str]) -> str | None:
    value = str(text)
    for token, original in mapping.items():
        if token not in value:
            return None
        value = value.replace(token, original)
    if any(token in value for token in mapping):
        return None
    return value


def invariant_values(text: str) -> tuple[str, ...]:
    found: list[str] = []
    for pattern in _PROTECTED_PATTERNS:
        found.extend(match.group(0) for match in pattern.finditer(str(text)))
    return tuple(sorted(found))


class GlobalLocalizationEngine:
    """Traduz a superfície sem alterar o conteúdo canônico."""

    def __init__(
        self,
        dictionary: OfflineDictionaryStore | None = None,
        expressions: ExpressionCatalog | None = None,
        neural_backend: NeuralTranslationBackend | None = None,
    ):
        self.dictionary = dictionary or OfflineDictionaryStore()
        self.expressions = expressions or ExpressionCatalog()
        self.neural = neural_backend or ArgosTranslationBackend()

    @staticmethod
    def message(key: str, locale: str, **values) -> str:
        if locale not in SUPPORTED_LOCALES:
            locale = "pt-BR"
        row = MESSAGES.get(key)
        if row is None:
            raise KeyError(f"Mensagem de localização desconhecida: {key}")
        return row[locale].format(**values)

    @staticmethod
    def static(text: str, locale: str) -> str | None:
        if locale not in SUPPORTED_LOCALES:
            return None
        surfaces = STATIC_INDEX.get(normalize_term(text))
        return surfaces.get(locale) if surfaces else None

    def status(self) -> dict:
        neural = self.neural.status()
        return {
            "supported_locales": list(SUPPORTED_LOCALES),
            "canonical_locale": "pt-BR",
            "policy": "canonical-content + localized-surface + invariant-protection",
            "strict_no_partial_translation": True,
            "static_strings": len(STATIC_TEXTS),
            "neural": neural,
            "dictionary_index_ready": self.dictionary.full_index_ready,
        }

    def translate(
        self,
        text: str,
        target_locale: str,
        source_locale: str,
    ) -> TranslationOutcome:
        original = str(text)
        if target_locale not in SUPPORTED_LOCALES or source_locale not in SUPPORTED_LOCALES:
            return TranslationOutcome(original, source_locale, target_locale, "identity", False, reason="unsupported-locale")
        if target_locale == source_locale:
            return TranslationOutcome(original, source_locale, target_locale, "identity", True)

        static = self.static(original, target_locale)
        if static is not None:
            return TranslationOutcome(static, source_locale, target_locale, "static-catalog", True)

        contextual = self.expressions.contextual_equivalent(original, target_locale)
        if contextual:
            return TranslationOutcome(contextual, source_locale, target_locale, "contextual-catalog", True)

        exact = self.dictionary.lookup(original, source_locale, target_locale)
        if exact:
            return TranslationOutcome(exact, source_locale, target_locale, "dictionary-exact", True)

        protected, mapping = protect_invariants(original)
        neural = self.neural.translate(protected, source_locale, target_locale)
        if neural:
            restored = restore_invariants(neural, mapping)
            if restored is not None and invariant_values(restored) == invariant_values(original):
                return TranslationOutcome(
                    restored,
                    source_locale,
                    target_locale,
                    self.neural.name,
                    True,
                    protected_segments=len(mapping),
                )

        dictionary_value = self._strict_dictionary_sentence(original, source_locale, target_locale)
        if dictionary_value is not None:
            return TranslationOutcome(
                dictionary_value,
                source_locale,
                target_locale,
                "dictionary-complete",
                True,
                protected_segments=len(mapping),
            )

        return TranslationOutcome(
            original,
            source_locale,
            target_locale,
            "preserved-original",
            False,
            protected_segments=len(mapping),
            reason="no-complete-local-translation",
        )

    def _strict_dictionary_sentence(self, text: str, source_locale: str, target_locale: str) -> str | None:
        pieces = re.findall(r"\w+(?:['’-]\w+)*|[^\w\s]+|\s+", str(text), flags=re.UNICODE)
        out: list[str] = []
        translated_words = 0
        missing_words = 0
        for piece in pieces:
            if not piece or piece.isspace() or not any(ch.isalnum() for ch in piece):
                out.append(piece)
                continue
            if piece.upper() == "STAR" or piece.isupper() or piece[:1].isdigit():
                out.append(piece)
                continue
            translated = self.dictionary.lookup(piece, source_locale, target_locale)
            if translated is None:
                missing_words += 1
                out.append(piece)
                continue
            translated_words += 1
            if piece[:1].isupper():
                translated = translated[:1].upper() + translated[1:]
            out.append(translated)
        if translated_words and missing_words == 0:
            return "".join(out)
        return None
