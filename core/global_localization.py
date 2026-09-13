"""Localização global e tradução segura da STAR.

Princípios:
- conteúdo canônico continua em uma única fonte de verdade;
- idioma altera somente superfícies de entrada/saída;
- IDs, números, fórmulas, caminhos, URLs e código não são traduzidos;
- tradução parcial nunca é apresentada como completa;
- Argos é opcional/lazy, usa somente pacotes já instalados e nunca baixa no boot;
- línguas históricas usam léxico/corpus próprio, sem serem mascaradas por MT moderno.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol

from core.language_catalog import ExpressionCatalog
from core.language_profiles import LOCALES, ui_term, presentation_fallback
from core.offline_dictionary import OfflineDictionaryStore, normalize_term

SUPPORTED_LOCALES = tuple(LOCALES)
ARGOS_CODES = {code: meta.get("argos") for code, meta in LOCALES.items() if meta.get("argos")}
LEGACY_LOCALES = ("pt-BR", "en-US", "en-GB", "es-ES", "it-IT", "fr-FR")


def _row(pt: str, en_us: str, en_gb: str, es: str, it: str, fr: str) -> dict[str, str]:
    return {"pt-BR": pt, "en-US": en_us, "en-GB": en_gb, "es-ES": es, "it-IT": it, "fr-FR": fr}


# Catálogo fixo legado preservado. Novos idiomas usam overrides em language_profiles
# e, para strings não embutidas, o pipeline local de dicionário/Argos.
STATIC_TEXTS = (
    _row("System for Thought, Analysis and Response", "System for Thought, Analysis and Response", "System for Thought, Analysis and Response", "System for Thought, Analysis and Response", "System for Thought, Analysis and Response", "System for Thought, Analysis and Response"),
    _row("INICIAR", "START", "START", "INICIAR", "AVVIA", "DÉMARRER"),
    _row("CONFIGURAÇÕES", "SETTINGS", "SETTINGS", "AJUSTES", "IMPOSTAZIONI", "PARAMÈTRES"),
    _row("SAIR", "EXIT", "EXIT", "SALIR", "ESCI", "QUITTER"),
    _row("CHAT", "CHAT", "CHAT", "CHAT", "CHAT", "CHAT"),
    _row("MENU", "MENU", "MENU", "MENÚ", "MENU", "MENU"),
    _row("ILHAS", "ISLANDS", "ISLANDS", "ISLAS", "ISOLE", "ÎLES"),
    _row("SISTEMA", "SYSTEM", "SYSTEM", "SISTEMA", "SISTEMA", "SYSTÈME"),
    _row("Você", "You", "You", "Tú", "Tu", "Vous"),
    _row("Pergunte algo à STAR...", "Ask STAR something...", "Ask STAR something...", "Pregúntale algo a STAR...", "Chiedi qualcosa a STAR...", "Demandez quelque chose à STAR..."),
    _row("ONLINE", "ONLINE", "ONLINE", "EN LÍNEA", "ONLINE", "EN LIGNE"),
    _row("OFFLINE", "OFFLINE", "OFFLINE", "SIN CONEXIÓN", "OFFLINE", "HORS LIGNE"),
    _row("OUVINDO", "LISTENING", "LISTENING", "ESCUCHANDO", "IN ASCOLTO", "ÉCOUTE"),
    _row("PROCESSANDO", "PROCESSING", "PROCESSING", "PROCESANDO", "ELABORAZIONE", "TRAITEMENT"),
    _row("TRANSCRIVENDO", "TRANSCRIBING", "TRANSCRIBING", "TRANSCRIBIENDO", "TRASCRIZIONE", "TRANSCRIPTION"),
    _row("FALANDO", "SPEAKING", "SPEAKING", "HABLANDO", "PARLANDO", "PAROLE"),
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
    _row("AGORA", "NOW", "NOW", "AHORA", "ORA", "MAINTENANT"),
    _row("MODO DE FUNCIONAMENTO", "OPERATING MODE", "OPERATING MODE", "MODO DE FUNCIONAMIENTO", "MODALITÀ DI FUNZIONAMENTO", "MODE DE FONCTIONNEMENT"),
    _row("🎙️ VOZ DA STAR", "🎙️ STAR VOICE", "🎙️ STAR VOICE", "🎙️ VOZ DE STAR", "🎙️ VOCE DI STAR", "🎙️ VOIX DE STAR"),
    _row("⚡ CONVERSA RÁPIDA", "⚡ FAST CONVERSATION", "⚡ FAST CONVERSATION", "⚡ CONVERSACIÓN RÁPIDA", "⚡ CONVERSAZIONE RAPIDA", "⚡ CONVERSATION RAPIDE"),
    _row("⭐ VOZ OFICIAL", "⭐ OFFICIAL VOICE", "⭐ OFFICIAL VOICE", "⭐ VOZ OFICIAL", "⭐ VOCE UFFICIALE", "⭐ VOIX OFFICIELLE"),
    _row("TESTAR VOZ OFICIAL", "TEST OFFICIAL VOICE", "TEST OFFICIAL VOICE", "PROBAR VOZ OFICIAL", "TESTA VOCE UFFICIALE", "TESTER LA VOIX OFFICIELLE"),
    _row("Pronto para testar.", "Ready to test.", "Ready to test.", "Listo para probar.", "Pronto per il test.", "Prêt pour le test."),
    _row("Versão", "Version", "Version", "Versión", "Versione", "Version"),
    _row("Conhecimento local", "Local knowledge", "Local knowledge", "Conocimiento local", "Conoscenza locale", "Connaissance locale"),
    _row("Modo de voz", "Voice mode", "Voice mode", "Modo de voz", "Modalità voce", "Mode vocal"),
    _row("Reconhecimento local", "Local recognition", "Local recognition", "Reconocimiento local", "Riconoscimento locale", "Reconnaissance locale"),
    _row("ATIVO", "ACTIVE", "ACTIVE", "ACTIVO", "ATTIVO", "ACTIF"),
    _row("PRONTO", "READY", "READY", "LISTO", "PRONTO", "PRÊT"),
    _row("INSTALAÇÃO PENDENTE", "INSTALLATION PENDING", "INSTALLATION PENDING", "INSTALACIÓN PENDIENTE", "INSTALLAZIONE IN SOSPESO", "INSTALLATION EN ATTENTE"),
    _row("VOLTAR AO CHAT", "BACK TO CHAT", "BACK TO CHAT", "VOLVER AL CHAT", "TORNA ALLA CHAT", "RETOUR AU CHAT"),
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
    "current_language": _row("Idioma atual: {display}.", "Current language: {display}.", "Current language: {display}.", "Idioma actual: {display}.", "Lingua attuale: {display}.", "Langue actuelle : {display}."),
    "translation_missing": _row(
        "Não encontrei uma tradução completa e confiável para '{text}' no runtime local. Preservei o original para não alterar a informação.",
        "I did not find a complete, reliable translation for '{text}' in the local runtime. I preserved the original so the information is not changed.",
        "I did not find a complete, reliable translation for '{text}' in the local runtime. I preserved the original so the information is not changed.",
        "No encontré una traducción completa y fiable para '{text}' en el runtime local. Conservé el original para no alterar la información.",
        "Non ho trovato una traduzione completa e affidabile per '{text}' nel runtime locale. Ho mantenuto l'originale per non alterare l'informazione.",
        "Je n'ai pas trouvé de traduction complète et fiable pour « {text} » dans le runtime local. J'ai conservé l'original afin de ne pas modifier l'information.",
    ),
    "language_confirmed": _row("Idioma confirmado: {display}", "Language confirmed: {display}", "Language confirmed: {display}", "Idioma confirmado: {display}", "Lingua confermata: {display}", "Langue confirmée : {display}"),
}

MESSAGE_EXTENSIONS = {
    "ja-JP": {
        "language_changed": "STARの言語を{display}に変更しました。オフライン優先モードは有効です。",
        "current_language": "現在の言語: {display}。",
        "translation_missing": "ローカル環境で「{text}」の完全で信頼できる翻訳が見つかりませんでした。情報を変えないよう原文を保持しました。",
        "language_confirmed": "言語を確認しました: {display}",
    },
    "pl-PL": {
        "language_changed": "Język STAR zmieniono na {display}. Tryb offline-first pozostaje aktywny.",
        "current_language": "Aktualny język: {display}.",
        "translation_missing": "Nie znaleziono kompletnego i wiarygodnego tłumaczenia „{text}” w lokalnym środowisku. Zachowano oryginał.",
        "language_confirmed": "Potwierdzony język: {display}",
    },
    "ko-KR": {
        "language_changed": "STAR 언어가 {display}(으)로 변경되었습니다. 오프라인 우선 모드는 계속 활성화됩니다.",
        "current_language": "현재 언어: {display}.",
        "translation_missing": "로컬 환경에서 '{text}'의 완전하고 신뢰할 수 있는 번역을 찾지 못했습니다. 정보 보존을 위해 원문을 유지했습니다.",
        "language_confirmed": "확인된 언어: {display}",
    },
    "el-GR": {
        "language_changed": "Η γλώσσα της STAR άλλαξε σε {display}. Η λειτουργία offline-first παραμένει ενεργή.",
        "current_language": "Τρέχουσα γλώσσα: {display}.",
        "translation_missing": "Δεν βρέθηκε πλήρης και αξιόπιστη τοπική μετάφραση για «{text}». Διατηρήθηκε το πρωτότυπο.",
        "language_confirmed": "Επιβεβαιωμένη γλώσσα: {display}",
    },
    "ar-001": {
        "language_changed": "تم تغيير لغة STAR إلى {display}. يظل وضع العمل دون اتصال هو الأساس.",
        "current_language": "اللغة الحالية: {display}.",
        "translation_missing": "لم أجد ترجمة محلية كاملة وموثوقة لـ «{text}». تم الاحتفاظ بالنص الأصلي حتى لا تتغير المعلومة.",
        "language_confirmed": "اللغة المؤكدة: {display}",
    },
    "ar-EG": {
        "language_changed": "تم تغيير لغة STAR إلى {display}. وضع العمل أوفلاين ما زال هو الأساس.",
        "current_language": "اللغة الحالية: {display}.",
        "translation_missing": "ما لقيتش ترجمة محلية كاملة وموثوقة لـ «{text}». احتفظت بالنص الأصلي عشان المعلومة ما تتغيرش.",
        "language_confirmed": "اللغة المؤكدة: {display}",
    },
}


class NeuralTranslationBackend(Protocol):
    name: str
    def translate(self, text: str, source_locale: str, target_locale: str) -> str | None: ...
    def status(self) -> dict: ...


class ArgosTranslationBackend:
    """Backend neural offline opcional, sem downloads automáticos."""
    name = "argos-local"

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


def _alpha_id(index: int) -> str:
    value = int(index); chars = []
    while True:
        value, remainder = divmod(value, 26); chars.append(chr(ord("A") + remainder))
        if value == 0: break
        value -= 1
    return "".join(reversed(chars))


def protect_invariants(text: str) -> tuple[str, dict[str, str]]:
    value = str(text); mapping = {}
    def replace(match: re.Match) -> str:
        token = f"__STARPROTECTED{_alpha_id(len(mapping))}__"; mapping[token] = match.group(0); return token
    for pattern in _PROTECTED_PATTERNS:
        value = pattern.sub(replace, value)
    return value, mapping


def restore_invariants(text: str, mapping: dict[str, str]) -> str | None:
    value = str(text)
    for token, original in mapping.items():
        if token not in value: return None
        value = value.replace(token, original)
    if any(token in value for token in mapping): return None
    return value


def invariant_values(text: str) -> tuple[str, ...]:
    found = []
    for pattern in _PROTECTED_PATTERNS:
        found.extend(match.group(0) for match in pattern.finditer(str(text)))
    return tuple(sorted(found))


class GlobalLocalizationEngine:
    """Traduz a superfície sem alterar o conteúdo canônico."""

    def __init__(self, dictionary=None, expressions=None, neural_backend=None):
        self.dictionary = dictionary or OfflineDictionaryStore()
        self.expressions = expressions or ExpressionCatalog()
        self.neural = neural_backend or ArgosTranslationBackend()

    @classmethod
    def _fallback_locale(cls, locale: str) -> str | None:
        seen = set()
        current = locale
        while current and current not in seen:
            seen.add(current)
            fallback = presentation_fallback(current)
            if not fallback or fallback == current:
                return None
            return fallback
        return None

    @classmethod
    def message(cls, key: str, locale: str, **values) -> str:
        if locale not in SUPPORTED_LOCALES:
            locale = "pt-BR"
        extension = MESSAGE_EXTENSIONS.get(locale, {}).get(key)
        if extension is not None:
            return extension.format(**values)
        row = MESSAGES.get(key)
        if row is None:
            raise KeyError(f"Mensagem de localização desconhecida: {key}")
        if locale in row:
            return row[locale].format(**values)
        fallback = cls._fallback_locale(locale)
        if fallback:
            return cls.message(key, fallback, **values)
        return row["pt-BR"].format(**values)

    @classmethod
    def static(cls, text: str, locale: str) -> str | None:
        if locale not in SUPPORTED_LOCALES:
            return None
        override = ui_term(str(text), locale)
        if override is not None:
            return override
        surfaces = STATIC_INDEX.get(normalize_term(text))
        if surfaces and locale in surfaces:
            return surfaces[locale]
        fallback = cls._fallback_locale(locale)
        if fallback:
            return cls.static(text, fallback)
        return None

    def status(self) -> dict:
        return {
            "supported_locales": list(SUPPORTED_LOCALES),
            "canonical_locale": "pt-BR",
            "policy": "canonical-content + localized-surface + invariant-protection",
            "strict_no_partial_translation": True,
            "static_strings": len(STATIC_TEXTS),
            "neural": self.neural.status(),
            "dictionary_index_ready": self.dictionary.full_index_ready,
            "historical_profiles_use_modern_mt": False,
            "historical_profiles": [code for code, meta in LOCALES.items() if meta.get("kind") == "historical"],
        }

    def translate(self, text: str, target_locale: str, source_locale: str) -> TranslationOutcome:
        original = str(text)
        if target_locale not in SUPPORTED_LOCALES or source_locale not in SUPPORTED_LOCALES:
            return TranslationOutcome(original, source_locale, target_locale, "identity", False, reason="unsupported-locale")
        if target_locale == source_locale:
            return TranslationOutcome(original, source_locale, target_locale, "identity", True)

        static = self.static(original, target_locale)
        if static is not None:
            return TranslationOutcome(static, source_locale, target_locale, "static-catalog", True)

        # O catálogo pragmático legado é usado apenas onde possui superfície humana
        # revisada; para novos idiomas o pipeline segue para léxico/MT local.
        try:
            contextual = self.expressions.contextual_equivalent(original, target_locale)
        except (KeyError, ValueError):
            contextual = None
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
                return TranslationOutcome(restored, source_locale, target_locale, self.neural.name, True, protected_segments=len(mapping))

        dictionary_value = self._strict_dictionary_sentence(original, source_locale, target_locale)
        if dictionary_value is not None:
            return TranslationOutcome(dictionary_value, source_locale, target_locale, "dictionary-complete", True, protected_segments=len(mapping))

        return TranslationOutcome(original, source_locale, target_locale, "preserved-original", False, protected_segments=len(mapping), reason="no-complete-local-translation")

    def _strict_dictionary_sentence(self, text: str, source_locale: str, target_locale: str) -> str | None:
        pieces = re.findall(r"\w+(?:['’-]\w+)*|[^\w\s]+|\s+", str(text), flags=re.UNICODE)
        out = []; translated_words = 0; missing_words = 0
        for piece in pieces:
            if not piece or piece.isspace() or not any(ch.isalnum() for ch in piece):
                out.append(piece); continue
            if piece.upper() == "STAR" or (piece.isupper() and len(piece) > 1) or piece[:1].isdigit():
                out.append(piece); continue
            translated = self.dictionary.lookup(piece, source_locale, target_locale)
            if translated is None:
                missing_words += 1; out.append(piece); continue
            translated_words += 1
            if piece[:1].isupper() and translated[:1].isalpha():
                translated = translated[:1].upper() + translated[1:]
            out.append(translated)
        return "".join(out) if translated_words and missing_words == 0 else None
