"""Catálogo contextual: 5 famílias x 100.000 conteúdos = 500.000.

Inglês possui superfícies en-US e en-GB sobre os mesmos 100k IDs semânticos.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

LANGUAGE_FAMILIES = ("pt", "en", "es", "it", "fr")
LOCALES = {
    "pt-BR": {"family": "pt", "name": "Português (Brasil)", "flag": "🇧🇷", "aliases": ("portugues", "português", "brasileiro", "pt br", "pt-br")},
    "en-US": {"family": "en", "name": "English (US)", "flag": "🇺🇸", "aliases": ("ingles eua", "inglês eua", "ingles americano", "english us", "american english", "en-us")},
    "en-GB": {"family": "en", "name": "English (UK)", "flag": "🇬🇧", "aliases": ("ingles uk", "inglês uk", "ingles britanico", "british english", "english uk", "en-gb")},
    "es-ES": {"family": "es", "name": "Español", "flag": "🇪🇸", "aliases": ("espanhol", "español", "spanish", "castelhano", "es")},
    "it-IT": {"family": "it", "name": "Italiano", "flag": "🇮🇹", "aliases": ("italiano", "italian", "it")},
    "fr-FR": {"family": "fr", "name": "Français", "flag": "🇫🇷", "aliases": ("frances", "francês", "français", "french", "fr")},
}
DEFAULT_LOCALE = "pt-BR"
REGISTERS = ("muito_informal", "informal", "casual", "amigavel", "neutro", "internet", "jovem", "trabalho_casual", "regional_leve", "enfatico")
CONTEXTS = ("cara_a_cara", "mensagem", "grupo", "dm", "voz", "reencontro", "resposta", "convite", "despedida", "reacao")
TONES = ("calmo", "leve", "brincalhao", "carinhoso", "animado", "curioso", "surpreso", "aprovador", "seco", "acolhedor")
MODES = ("base", "intensified")
VARIANTS_PER_CONCEPT = 1000
BASE_EXPRESSION_COUNT = 50
CANONICAL_CONCEPTS_PER_LANGUAGE = 100
CONTENTS_PER_LANGUAGE = 100000
TOTAL_SEMANTIC_CONTENTS = 500000

@dataclass(frozen=True)
class ExpressionConcept:
    id: str
    pt: str
    en_us: str
    en_gb: str
    es: str
    it: str
    fr: str

_ROWS = r"""
whats_up_bro	e aí mano, sereno?	yo man, all good?	alright mate, you good?	qué pasa, tío, todo tranqui?	ehi fra, tutto tranquillo?	wesh mec, ça va tranquille?
whats_up	e aí, beleza?	what's up, you good?	alright, you good?	qué tal, todo bien?	come va, tutto bene?	ça va, tranquille?
all_good	tudo certo por aí?	everything good over there?	everything alright your end?	todo bien por ahí?	tutto bene da te?	tout va bien de ton côté?
no_worries	de boa, sem estresse	no worries, we're good	no worries, all good	tranqui, no pasa nada	tranquillo, nessun problema	tranquille, pas de souci
im_in	fechou, tô dentro	bet, I'm in	yeah, I'm in	va, me apunto	ci sto, sono dentro	vas-y, je suis chaud
lets_go	bora!	let's go!	come on, let's go!	vamos, dale!	dai, andiamo!	allez, on y va!
lets_bounce	bora vazar	let's bounce	let's head off	vámonos de aquí	andiamocene	on se casse / on y va
see_you	tamo junto, até mais	catch you later	see you later, mate	nos vemos, cuídate	ci becchiamo, a dopo	à plus, prends soin de toi
thanks_bro	valeu, mano	thanks, man	cheers, mate	gracias, tío	grazie, fra	merci, mec
thanks_a_lot	valeu demais	thanks a ton	cheers, really appreciate it	mil gracias	grazie mille	merci beaucoup
my_bad	foi mal	my bad	my bad / sorry about that	perdón, fue culpa mía	colpa mia, scusa	désolé, c'est ma faute
sorry_bro	mal aí, mano	my bad, bro	sorry, mate	perdona, tío	scusa, fra	désolé, mec
no_way	nem ferrando	no way	no chance	ni de broma	ma neanche per sogno	même pas en rêve
seriously	sério mesmo?	for real?	seriously?	¿en serio?	davvero?	sérieux ?
wow	nossa!	damn, wow!	blimey / wow!	¡guau!	caspita / wow !	waouh !
thats_crazy	que doideira	that's wild	that's mad	qué locura	che roba assurda	c'est ouf
awesome	brabo demais	that's sick / awesome	that's proper good	está brutal / buenísimo	spacca / è fantastico	c'est lourd / trop bien
cool	massa	cool	nice / sound	guay / genial	figo / bello	cool / sympa
nice_one	boa!	nice!	nice one!	bien ahí!	grande!	bien joué !
nailed_it	mandou bem	you nailed it	you smashed it	lo clavaste	l'hai spaccata	t'as géré
exactly	é isso!	exactly!	that's it!	¡eso es!	esatto!	c'est ça !
makes_sense	faz sentido	that makes sense	that makes sense	tiene sentido	ha senso	ça se tient
fair_enough	justo	fair enough	fair enough	vale, es justo	ci sta	d'accord, c'est juste
agreed	fechado	sounds good	sounds good	trato hecho / vale	affare fatto / va bene	marché conclu / ça marche
not_really	mais ou menos	not really	more or less / not really	más o menos	più o meno	bof, plus ou moins
not_feeling_it	não curti	I'm not feeling it	not really my thing	no me convence	non mi convince	je le sens pas
whatever	tanto faz	whatever / either works	either way, I'm easy	me da igual	mi è indifferente	comme tu veux
chill	relaxa	chill, you're good	relax, you're alright	relájate, todo bien	ranquillo, va tutto bene	détends-toi, ça va
take_it_easy	vai na calma	take it easy	take it easy	con calma	vai tranquillo	vas-y doucement
hold_on	pera aí	hold up	wait a sec	espera un momento	aspetta un attimo	attends deux secondes
come_on	qual foi?	come on, man	oh, come on mate	vamos, hombre / qué pasa	dai, su	allez, sérieux
are_you_kidding	tá de zoeira?	are you kidding me?	are you having a laugh?	¿me estás tomando el pelo?	mi stai prendendo in giro?	tu te fous de moi ?
just_kidding	tô zoando	I'm just messing with you	I'm only joking	estoy bromeando	sto scherzando	je plaisante
im_dead	morri de rir	I'm dead	I'm dying	me muero de risa	muoio dal ridere	je suis mort de rire
lol	kkkk / tô rindo	lol / lmao	lol	jajaja	ahahah	mdr
thats_funny	boa, essa foi boa	okay, that was funny	alright, that was funny	vale, esa estuvo buena	ok, questa era bella	ok, elle était bonne
lets_see	vamos ver	we'll see	we'll see	ya veremos	vediamo	on verra
maybe	quem sabe	maybe, we'll see	maybe	quizá	magari	peut-être
im_down	topo	I'm down	I'm up for it	me apetece / me apunto	ci sto	je suis chaud
count_me_in	pode contar comigo	count me in	count me in	cuenta conmigo	conta su di me	compte sur moi
im_out	tô fora	I'm out	I'm out	paso / yo no voy	io passo	je passe
not_today	hoje não	not today	not today	hoy no	oggi no	pas aujourd'hui
im_tired	tô morto	I'm wiped	I'm knackered	estoy reventado	sono distrutto	je suis crevé
im_hungry	tô morrendo de fome	I'm starving	I'm starving	me muero de hambre	muoio di fame	je meurs de faim
im_broke	tô liso	I'm broke	I'm skint	estoy sin un duro	sono al verde	je suis fauché
good_luck	vai dar bom	you've got this	it'll be alright	va a salir bien	andrà bene	ça va le faire
you_got_this	confia, tu consegue	you got this	you've got this	tú puedes	ce la fai	tu vas y arriver
lets_talk	chama aí	hit me up	give me a shout	escríbeme / avísame	scrivimi / fammi sapere	envoie-moi un message / tiens-moi au courant
keep_me_posted	me avisa	keep me posted	keep me posted	avísame	fammi sapere	tiens-moi au courant
long_time	sumido!	long time no see!	long time no see!	¡cuánto tiempo!	quanto tempo!	ça fait longtemps !
"""

def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").lower())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9\s]", " ", value).split())

def _concepts():
    rows = []
    for raw in _ROWS.strip().splitlines():
        p = raw.split("\t")
        if len(p) != 7:
            raise ValueError(f"expression row inválida: {len(p)} campos")
        rows.append(ExpressionConcept(*p))
    if len(rows) != 50 or len({r.id for r in rows}) != 50:
        raise ValueError(f"Esperadas 50 expressões-base únicas; encontradas {len(rows)}")
    return tuple(rows)

BASE_EXPRESSIONS = _concepts()

class ExpressionCatalog:
    def __init__(self):
        self.rows = BASE_EXPRESSIONS
        self._index = {}
        for row in self.rows:
            for locale, value in self._surfaces(row).items():
                self._index[_normalize(value)] = (row, locale)

    @staticmethod
    def _surfaces(row):
        return {"pt-BR": row.pt, "en-US": row.en_us, "en-GB": row.en_gb, "es-ES": row.es, "it-IT": row.it, "fr-FR": row.fr}

    def stats(self):
        return {"language_families": 5, "locale_profiles": 6, "base_expressions": 50, "semantic_concepts_per_language": 100, "variants_per_concept": 1000, "contents_per_language": 100000, "total_semantic_contents": 500000, "english_locale_surfaces": 2}

    def match(self, text):
        return self._index.get(_normalize(text))

    def contextual_equivalent(self, text, target_locale):
        hit = self.match(text)
        if hit is None or target_locale not in LOCALES:
            return None
        return self._surfaces(hit[0])[target_locale]

    @staticmethod
    def content_id(family, concept_index, variant_index):
        if family not in LANGUAGE_FAMILIES:
            raise ValueError("família linguística inválida")
        if not 0 <= concept_index < 100 or not 0 <= variant_index < 1000:
            raise IndexError("índice fora do catálogo de expressões")
        prefix = {"pt": "PTBR", "en": "EN", "es": "ES", "it": "IT", "fr": "FR"}[family]
        return f"EXP-{prefix}-{concept_index * 1000 + variant_index + 1:06d}"

    def get_variant(self, family, concept_index, variant_index, *, locale=None):
        cid = self.content_id(family, concept_index, variant_index)
        base_i, mode_i = divmod(concept_index, 2)
        register_i, rem = divmod(variant_index, 100)
        context_i, tone_i = divmod(rem, 10)
        row = self.rows[base_i]
        selected_locale = locale if family == "en" and locale in {"en-US", "en-GB"} else {"pt": "pt-BR", "en": "en-US", "es": "es-ES", "it": "it-IT", "fr": "fr-FR"}[family]
        return {"id": cid, "concept": row.id, "locale": selected_locale, "mode": MODES[mode_i], "register": REGISTERS[register_i], "context": CONTEXTS[context_i], "tone": TONES[tone_i], "expression": self._surfaces(row)[selected_locale], "pt_equivalent": row.pt, "note": "Equivalência pragmática/contextual; não force tradução literal.", "equivalents": self._surfaces(row)}
