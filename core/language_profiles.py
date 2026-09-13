"""Perfis linguísticos canônicos da STAR.

A fonte de conhecimento continua única em pt-BR. Perfis de idioma controlam somente
entrada, tradução, voz/UI e recursos lexicais. Idiomas históricos são explicitamente
perfis de estudo: não fingimos que um MT moderno cobre grego antigo, latim histórico
ou egípcio antigo.
"""
from __future__ import annotations

DEFAULT_LOCALE = "pt-BR"

# UI mínima embutida para os novos idiomas modernos. Textos livres usam dicionário
# local/Argos instalado; nenhum modelo é baixado automaticamente em runtime.
_UI_JA = {
    "INICIAR": "開始", "CONFIGURAÇÕES": "設定", "SAIR": "終了", "CHAT": "チャット",
    "MENU": "メニュー", "ILHAS": "島", "SISTEMA": "システム", "Você": "あなた",
    "Pergunte algo à STAR...": "STARに質問してください...", "ONLINE": "オンライン", "OFFLINE": "オフライン",
    "OUVINDO": "聞いています", "PROCESSANDO": "処理中", "TRANSCRIVENDO": "文字起こし中",
    "FALANDO": "話しています", "PRONTA": "準備完了", "PENSANDO": "考え中", "RESPONDENDO": "応答中",
    "ATENÇÃO": "注意", "VOZ": "音声", "BUSCA": "検索", "SAÚDE": "健康", "VISÃO": "ビジョン",
    "PEOPLE": "人物", "MEDIR": "測定", "MÍDIA": "メディア", "CLIMA": "天気", "CONFIG": "設定",
    "IDIOMA": "言語", "AGORA": "今", "PRONTO": "準備完了", "ATIVO": "有効",
}
_UI_PL = {
    "INICIAR": "START", "CONFIGURAÇÕES": "USTAWIENIA", "SAIR": "WYJDŹ", "CHAT": "CZAT",
    "MENU": "MENU", "ILHAS": "WYSPY", "SISTEMA": "SYSTEM", "Você": "Ty",
    "Pergunte algo à STAR...": "Zapytaj STAR...", "ONLINE": "ONLINE", "OFFLINE": "OFFLINE",
    "OUVINDO": "SŁUCHAM", "PROCESSANDO": "PRZETWARZANIE", "TRANSCRIVENDO": "TRANSKRYPCJA",
    "FALANDO": "MÓWIĘ", "PRONTA": "GOTOWA", "PENSANDO": "MYŚLĘ", "RESPONDENDO": "ODPOWIADAM",
    "ATENÇÃO": "UWAGA", "VOZ": "GŁOS", "BUSCA": "SZUKAJ", "SAÚDE": "ZDROWIE", "VISÃO": "WIZJA",
    "PEOPLE": "OSOBY", "MEDIR": "ZMIERZ", "MÍDIA": "MEDIA", "CLIMA": "POGODA", "CONFIG": "USTAWIENIA",
    "IDIOMA": "JĘZYK", "AGORA": "TERAZ", "PRONTO": "GOTOWE", "ATIVO": "AKTYWNE",
}
_UI_KO = {
    "INICIAR": "시작", "CONFIGURAÇÕES": "설정", "SAIR": "종료", "CHAT": "채팅",
    "MENU": "메뉴", "ILHAS": "섬", "SISTEMA": "시스템", "Você": "사용자",
    "Pergunte algo à STAR...": "STAR에게 질문하세요...", "ONLINE": "온라인", "OFFLINE": "오프라인",
    "OUVINDO": "듣는 중", "PROCESSANDO": "처리 중", "TRANSCRIVENDO": "받아쓰기 중",
    "FALANDO": "말하는 중", "PRONTA": "준비됨", "PENSANDO": "생각 중", "RESPONDENDO": "응답 중",
    "ATENÇÃO": "주의", "VOZ": "음성", "BUSCA": "검색", "SAÚDE": "건강", "VISÃO": "비전",
    "PEOPLE": "사람", "MEDIR": "측정", "MÍDIA": "미디어", "CLIMA": "날씨", "CONFIG": "설정",
    "IDIOMA": "언어", "AGORA": "지금", "PRONTO": "준비", "ATIVO": "활성",
}
_UI_EL = {
    "INICIAR": "ΕΝΑΡΞΗ", "CONFIGURAÇÕES": "ΡΥΘΜΙΣΕΙΣ", "SAIR": "ΕΞΟΔΟΣ", "CHAT": "ΣΥΝΟΜΙΛΙΑ",
    "MENU": "ΜΕΝΟΥ", "ILHAS": "ΝΗΣΙΑ", "SISTEMA": "ΣΥΣΤΗΜΑ", "Você": "Εσύ",
    "Pergunte algo à STAR...": "Ρώτησε τη STAR...", "ONLINE": "ΣΕ ΣΥΝΔΕΣΗ", "OFFLINE": "ΕΚΤΟΣ ΣΥΝΔΕΣΗΣ",
    "OUVINDO": "ΑΚΟΥΩ", "PROCESSANDO": "ΕΠΕΞΕΡΓΑΣΙΑ", "TRANSCRIVENDO": "ΜΕΤΑΓΡΑΦΗ",
    "FALANDO": "ΜΙΛΑΩ", "PRONTA": "ΕΤΟΙΜΗ", "PENSANDO": "ΣΚΕΦΤΟΜΑΙ", "RESPONDENDO": "ΑΠΑΝΤΩ",
    "ATENÇÃO": "ΠΡΟΣΟΧΗ", "VOZ": "ΦΩΝΗ", "BUSCA": "ΑΝΑΖΗΤΗΣΗ", "SAÚDE": "ΥΓΕΙΑ", "VISÃO": "ΟΡΑΣΗ",
    "PEOPLE": "ΑΤΟΜΑ", "MEDIR": "ΜΕΤΡΗΣΗ", "MÍDIA": "ΠΟΛΥΜΕΣΑ", "CLIMA": "ΚΑΙΡΟΣ", "CONFIG": "ΡΥΘΜΙΣΕΙΣ",
    "IDIOMA": "ΓΛΩΣΣΑ", "AGORA": "ΤΩΡΑ", "PRONTO": "ΕΤΟΙΜΟ", "ATIVO": "ΕΝΕΡΓΟ",
}
_UI_AR = {
    "INICIAR": "ابدأ", "CONFIGURAÇÕES": "الإعدادات", "SAIR": "خروج", "CHAT": "الدردشة",
    "MENU": "القائمة", "ILHAS": "الجزر", "SISTEMA": "النظام", "Você": "أنت",
    "Pergunte algo à STAR...": "اسأل STAR...", "ONLINE": "متصل", "OFFLINE": "غير متصل",
    "OUVINDO": "أستمع", "PROCESSANDO": "جارٍ المعالجة", "TRANSCRIVENDO": "جارٍ النسخ",
    "FALANDO": "أتحدث", "PRONTA": "جاهزة", "PENSANDO": "أفكر", "RESPONDENDO": "أجيب",
    "ATENÇÃO": "تنبيه", "VOZ": "الصوت", "BUSCA": "البحث", "SAÚDE": "الصحة", "VISÃO": "الرؤية",
    "PEOPLE": "الأشخاص", "MEDIR": "قياس", "MÍDIA": "الوسائط", "CLIMA": "الطقس", "CONFIG": "الإعدادات",
    "IDIOMA": "اللغة", "AGORA": "الآن", "PRONTO": "جاهز", "ATIVO": "نشط",
}

LOCALES = {
    "pt-BR": {"family": "pt", "name": "Português (Brasil)", "flag": "🇧🇷", "aliases": ("portugues", "português", "brasileiro", "pt br", "pt-br"), "kind": "modern", "argos": "pt", "ui_fallback": None},
    "en-US": {"family": "en", "name": "English (US)", "flag": "🇺🇸", "aliases": ("ingles eua", "inglês eua", "ingles americano", "english us", "american english", "en-us"), "kind": "modern", "argos": "en", "ui_fallback": None},
    "en-GB": {"family": "en", "name": "English (UK)", "flag": "🇬🇧", "aliases": ("ingles uk", "inglês uk", "ingles britanico", "british english", "english uk", "en-gb"), "kind": "modern", "argos": "en", "ui_fallback": None},
    "es-ES": {"family": "es", "name": "Español", "flag": "🇪🇸", "aliases": ("espanhol", "español", "spanish", "castelhano", "es"), "kind": "modern", "argos": "es", "ui_fallback": None},
    "it-IT": {"family": "it", "name": "Italiano", "flag": "🇮🇹", "aliases": ("italiano", "italian", "it"), "kind": "modern", "argos": "it", "ui_fallback": None},
    "fr-FR": {"family": "fr", "name": "Français", "flag": "🇫🇷", "aliases": ("frances", "francês", "français", "french", "fr"), "kind": "modern", "argos": "fr", "ui_fallback": None},
    "ja-JP": {"family": "ja", "name": "日本語 (Japonês)", "flag": "🇯🇵", "aliases": ("japones", "japonês", "japanese", "nihongo", "日本語", "ja", "ja-jp"), "kind": "modern", "argos": "ja", "ui_fallback": None, "ui_terms": _UI_JA},
    "pl-PL": {"family": "pl", "name": "Polski", "flag": "🇵🇱", "aliases": ("polones", "polonês", "polish", "polski", "pl", "pl-pl"), "kind": "modern", "argos": "pl", "ui_fallback": None, "ui_terms": _UI_PL},
    "ko-KR": {"family": "ko", "name": "한국어 (Coreano)", "flag": "🇰🇷", "aliases": ("coreano", "korean", "hanguk-eo", "한국어", "ko", "ko-kr"), "kind": "modern", "argos": "ko", "ui_fallback": None, "ui_terms": _UI_KO},
    "el-GR": {"family": "el", "name": "Ελληνικά (Grego moderno)", "flag": "🇬🇷", "aliases": ("grego", "grego moderno", "grego atual", "modern greek", "ελληνικά", "el", "el-gr"), "kind": "modern", "argos": "el", "ui_fallback": None, "ui_terms": _UI_EL},
    "grc-GR": {"family": "grc", "name": "Ἑλληνικὴ ἀρχαία (Grego antigo)", "flag": "🏛️", "aliases": ("grego antigo", "grego classico", "grego clássico", "ancient greek", "grc"), "kind": "historical", "argos": None, "ui_fallback": "el-GR", "periods": ("Arcaico", "Clássico", "Helenístico/Koine", "Tardo-antigo"), "note": "perfil de estudo lexical/corpus; não usa MT de grego moderno como substituto"},
    "la-x-classical": {"family": "la", "name": "Latina — Clássico", "flag": "🏛️", "aliases": ("latim", "latim classico", "latim clássico", "classical latin", "la classical"), "kind": "historical", "argos": None, "ui_fallback": "pt-BR", "era": "Clássico", "note": "perfil histórico; tradução depende de léxico/corpus local"},
    "la-x-late": {"family": "la", "name": "Latina — Tardio", "flag": "🏛️", "aliases": ("latim tardio", "late latin"), "kind": "historical", "argos": None, "ui_fallback": "pt-BR", "era": "Tardio"},
    "la-x-medieval": {"family": "la", "name": "Latina — Medieval", "flag": "🏛️", "aliases": ("latim medieval", "medieval latin"), "kind": "historical", "argos": None, "ui_fallback": "pt-BR", "era": "Medieval"},
    "la-x-neo": {"family": "la", "name": "Latina — Neolatim", "flag": "🏛️", "aliases": ("neolatim", "latim moderno", "neo-latin", "neo latin"), "kind": "historical", "argos": None, "ui_fallback": "pt-BR", "era": "Renascimento/Neolatim"},
    "ar-001": {"family": "ar", "name": "العربية (Árabe padrão moderno)", "flag": "🌍", "aliases": ("arabe", "árabe", "arabic", "arabe padrao", "árabe padrão", "msa", "ar"), "kind": "modern", "argos": "ar", "ui_fallback": None, "ui_terms": _UI_AR, "rtl": True},
    "ar-EG": {"family": "ar", "name": "العربية المصرية (Árabe egípcio)", "flag": "🇪🇬", "aliases": ("arabe egipcio", "árabe egípcio", "egyptian arabic", "masri", "ar-eg"), "kind": "modern-dialect", "argos": "ar", "ui_fallback": "ar-001", "ui_terms": _UI_AR, "rtl": True},
    "egy-EG": {"family": "egy", "name": "Egípcio antigo", "flag": "𓂀", "aliases": ("egipcio antigo", "egípcio antigo", "ancient egyptian", "medio egipcio", "médio egípcio", "egy"), "kind": "historical", "argos": None, "ui_fallback": "ar-EG", "related_modern_locale": "ar-EG", "periods": ("Antigo", "Médio", "Novo", "Demótico"), "note": "Egípcio antigo não é árabe; o árabe egípcio é apenas o perfil moderno relacionado geograficamente."},
}

LOCALE_ORDER = tuple(LOCALES)
LANGUAGE_FAMILIES = tuple(dict.fromkeys(meta["family"] for meta in LOCALES.values()))
MODERN_LOCALES = tuple(code for code, meta in LOCALES.items() if meta["kind"].startswith("modern"))
HISTORICAL_LOCALES = tuple(code for code, meta in LOCALES.items() if meta["kind"] == "historical")


def ui_term(text: str, locale: str) -> str | None:
    """Retorna override embutido ou None para o pipeline geral/fallback."""
    meta = LOCALES.get(locale) or {}
    return (meta.get("ui_terms") or {}).get(str(text))


def presentation_fallback(locale: str) -> str | None:
    meta = LOCALES.get(locale) or {}
    return meta.get("ui_fallback")


def stats() -> dict:
    return {
        "language_families": len(LANGUAGE_FAMILIES),
        "locale_profiles": len(LOCALES),
        "modern_locales": len(MODERN_LOCALES),
        "historical_locales": len(HISTORICAL_LOCALES),
        "offline_runtime": True,
        "historical_mt_claimed": False,
    }
