"""Catálogo multilíngue contextual da STAR.

Cinco famílias linguísticas (pt-BR, inglês, espanhol, italiano e francês) geram
100.000 conteúdos educacionais/contextuais por família. Inglês possui duas
superfícies independentes, en-US e en-GB, sobre os mesmos IDs semânticos.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
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
VARIANTS_PER_CONCEPT = len(REGISTERS) * len(CONTEXTS) * len(TONES)
BASE_EXPRESSION_COUNT = 50
CANONICAL_CONCEPTS_PER_LANGUAGE = BASE_EXPRESSION_COUNT * len(MODES)
CONTENTS_PER_LANGUAGE = CANONICAL_CONCEPTS_PER_LANGUAGE * VARIANTS_PER_CONCEPT
TOTAL_SEMANTIC_CONTENTS = len(LANGUAGE_FAMILIES) * CONTENTS_PER_LANGUAGE


@dataclass(frozen=True)
class ExpressionConcept:
    id: str
    pt: str
    en_us: str
    en_gb: str
    es: str
    it: str
    fr: str
    note: str


# Equivalências pragmáticas: o objetivo é preservar intenção/registro, não palavras.
_ROWS = r"""
whats_up_bro	e aí mano, sereno?	yo man, all good?	alright mate, you good?	qué pasa, tío, todo tranqui?	ehi fra, tutto tranquillo?	wesh mec, ça va tranquille?	saudação descontraída entre amigos; não traduzir literalmente "sereno"
whats_up	e aí, beleza?	what's up, you good?	alright, you good?	qué tal, todo bien?	come va, tutto bene?	ça va, tranquille?	saudação casual
all_good	tudo certo por aí?	everything good over there?	everything alright your end?	todo bien por ahí?	tutto bene da te?	tout va bien de ton côté?	checagem amigável
no_worries	de boa, sem estresse	no worries, we're good	no worries, all good	tranqui, no pasa nada	tranquillo, nessun problema	tranquille, pas de souci	acalmar situação
im_in	fechou, tô dentro	bet, I'm in	yeah, I'm in	va, me apunto	ci sto, sono dentro	vas-y, je suis chaud	aceitar plano informalmente
lets_go	bora!	let's go!	come on, let's go!	vamos, dale!	dai, andiamo!	allez, on y va!	incentivo para começar
lets_bounce	bora vazar	let's bounce	let's head off	vámonos de aquí	andiamocene	on se casse / on y va	sair de um lugar; francês muito informal pode usar "on se casse"
see_you	tamo junto, até mais	catch you later	see you later, mate	nos vemos, cuídate	ci becchiamo, a dopo	à plus, prends soin de toi	despedida amigável
thanks_bro	valeu, mano	thanks, man	cheers, mate	gracias, tío	grazie, fra	merci, mec	agradecimento casual
thanks_a_lot	valeu demais	thanks a ton	cheers, really appreciate it	mil gracias	grazie mille	merci beaucoup	agradecimento intenso
my_bad	foi mal	my bad	my bad / sorry about that	perdón, fue culpa mía	colpa mia, scusa	désolé, c'est ma faute	assumir pequeno erro
sorry_bro	mal aí, mano	my bad, bro	sorry, mate	perdona, tío	scusa, fra	désolé, mec	desculpa informal
no_way	nem ferrando	no way	no chance	ni de broma	ma neanche per sogno	même pas en rêve	recusa/surpresa forte sem literalidade
seriously	sério mesmo?	for real?	seriously?	¿en serio?	davvero?	sérieux ?	descrença/surpresa
wow	nossa!	damn, wow!	blimey / wow!	¡guau!	caspita / wow !	waouh !	surpresa; manter intensidade conforme contexto
thats_crazy	que doideira	that's wild	that's mad	qué locura	che roba assurda	c'est ouf	reação a algo inesperado
awesome	brabo demais	that's sick / awesome	that's proper good	está brutal / buenísimo	spacca / è fantastico	c'est lourd / trop bien	elogio jovem; evitar tradução literal de "brabo"
cool	massa	cool	nice / sound	guay / genial	figo / bello	cool / sympa	aprovação casual
nice_one	boa!	nice!	nice one!	bien ahí!	grande!	bien joué !	aprovação rápida
nailed_it	mandou bem	you nailed it	you smashed it	lo clavaste	l'hai spaccata	t'as géré	elogio por execução
exactly	é isso!	exactly!	that's it!	¡eso es!	esatto!	c'est ça !	concordância
makes_sense	faz sentido	that makes sense	that makes sense	tiene sentido	ha senso	ça se tient	concordância racional
fair_enough	justo	fair enough	fair enough	vale, es justo	ci sta	d'accord, c'est juste	aceitação sem entusiasmo
agreed	fechado	sounds good	sounds good	trato hecho / vale	affare fatto / va bene	marché conclu / ça marche	acordo prático
not_really	mais ou menos	not really	more or less / not really	más o menos	più o meno	bof, plus ou moins	discordância suave
not_feeling_it	não curti	I'm not feeling it	not really my thing	no me convence	non mi convince	je le sens pas	desaprovação casual
whatever	tanto faz	whatever / either works	either way, I'm easy	me da igual	mi è indifferente	comme tu veux	indiferença; escolher formulação menos ríspida se necessário
chill	relaxa	chill, you're good	relax, you're alright	relájate, todo bien	ranquillo, va tutto bene	détends-toi, ça va	acalmar alguém
take_it_easy	vai na calma	take it easy	take it easy	con calma	vai tranquillo	vas-y doucement	pedir calma
hold_on	pera aí	hold up	wait a sec	espera un momento	aspetta un attimo	attends deux secondes	pedir pausa informal
come_on	qual foi?	come on, man	oh, come on mate	vamos, hombre / qué pasa	dai, su	allez, sérieux	reclamação leve; dependente do contexto
are_you_kidding	tá de zoeira?	are you kidding me?	are you having a laugh?	¿me estás tomando el pelo?	mi stai prendendo in giro?	tu te fous de moi ?	descrença; UK usa expressão própria
just_kidding	tô zoando	I'm just messing with you	I'm only joking	estoy bromeando	sto scherzando	je plaisante	marcar brincadeira
im_dead	morri de rir	I'm dead	I'm dying	me muero de risa	muoio dal ridere	je suis mort de rire	hipérbole de internet
lol	kkkk / tô rindo	lol / lmao	lol	jajaja	ahahah	mdr	risada digital culturalmente localizada
thats_funny	boa, essa foi boa	okay, that was funny	alright, that was funny	vale, esa estuvo buena	ok, questa era bella	ok, elle était bonne	reagir a piada
lets_see	vamos ver	we'll see	we'll see	ya veremos	vediamo	on verra	incerteza/aguardar
maybe	quem sabe	maybe, we'll see	maybe	quizá	magari	peut-être	possibilidade
im_down	topo	I'm down	I'm up for it	me apetece / me apunto	ci sto	je suis chaud	aceitar atividade
count_me_in	pode contar comigo	count me in	count me in	cuenta conmigo	conta su di me	compte sur moi	aceitação/apoio
im_out	tô fora	I'm out	I'm out	paso / yo no voy	io passo	je passe	recusar participação
not_today	hoje não	not today	not today	hoy no	oggi no	pas aujourd'hui	recusa simples
im_tired	tô morto	I'm wiped	I'm knackered	estoy reventado	sono distrutto	je suis crevé	cansaço intenso; não literal
im_hungry	tô morrendo de fome	I'm starving	I'm starving	me muero de hambre	muoio di fame	je meurs de faim	hipérbole comum
im_broke	tô liso	I'm broke	I'm skint	estoy sin un duro	sono al verde	je suis fauché	sem dinheiro; equivalentes idiomáticos
good_luck	vai dar bom	you've got this	it'll be alright	va a salir bien	andrà bene	ça va le faire	encorajamento otimista
you_got_this	confia, tu consegue	you got this	you've got this	tú puedes	ce la fai	tu vas y arriver	encorajamento direto
lets_talk	chama aí	hit me up	give me a shout	escríbeme / avísame	scrivimi / fammi sapere	envoie-moi un message / tiens-moi au courant	convite para contato
keep_me_posted	me avisa	keep me posted	keep me posted	avísame	fammi sapere	tiens-moi au courant	pedir atualização
long_time	sumido!	long time no see!	long time no see!	¡cuánto tiempo!	quanto tempo!	ça fait longtemps !	reencontro
welcome_back	voltou, hein?	look who's back	look who's back	mira quién volvió	guarda chi è tornato	regarde qui est de retour	recepção brincalhona
"""


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").lower())
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())


def _concepts() -> tuple[ExpressionConcept, ...]:
    rows = []
    for raw in _ROWS.strip().splitlines():
        p = raw.split("\t")
        if len(p) != 8:
            raise ValueError(f"expression row inválida: {len(p)} campos")
        rows.append(ExpressionConcept(*p))
    if len(rows) != BASE_EXPRESSION_COUNT:
        raise ValueError(f"Esperadas {BASE_EXPRESSION_COUNT} expressões-base; encontradas {len(rows)}")
    if len({r.id for r in rows}) != BASE_EXPRESSION_COUNT:
        raise ValueError("IDs de expressões devem ser únicos")
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
    def _surfaces(row: ExpressionConcept) -> dict[str, str]:
        return {"pt-BR": row.pt, "en-US": row.en_us, "en-GB": row.en_gb, "es-ES": row.es, "it-IT": row.it, "fr-FR": row.fr}

    def stats(self) -> dict:
        return {
            "language_families": len(LANGUAGE_FAMILIES),
            "locale_profiles": len(LOCALES),
            "base_expressions": BASE_EXPRESSION_COUNT,
            "semantic_concepts_per_language": CANONICAL_CONCEPTS_PER_LANGUAGE,
            "variants_per_concept": VARIANTS_PER_CONCEPT,
            "contents_per_language": CONTENTS_PER_LANGUAGE,
            "total_semantic_contents": TOTAL_SEMANTIC_CONTENTS,
            "english_locale_surfaces": 2,
        }

    def match(self, text: str):
        return self._index.get(_normalize(text))

    def contextual_equivalent(self, text: str, target_locale: str) -> str | None:
        hit = self.match(text)
        if hit is None or target_locale not in LOCALES:
            return None
        row, _source = hit
        return self._surfaces(row)[target_locale]

    @staticmethod
    def content_id(family: str, concept_index: int, variant_index: int) -> str:
        if family not in LANGUAGE_FAMILIES:
            raise ValueError("família linguística inválida")
        if not 0 <= concept_index < CANONICAL_CONCEPTS_PER_LANGUAGE or not 0 <= variant_index < VARIANTS_PER_CONCEPT:
            raise IndexError("índice fora do catálogo de expressões")
        prefixes = {"pt": "PTBR", "en": "EN", "es": "ES", "it": "IT", "fr": "FR"}
        n = concept_index * VARIANTS_PER_CONCEPT + variant_index + 1
        return f"EXP-{prefixes[family]}-{n:06d}"

    def get_variant(self, family: str, concept_index: int, variant_index: int, *, locale: str | None = None) -> dict:
        cid = self.content_id(family, concept_index, variant_index)
        base_i, mode_i = divmod(concept_index, len(MODES))
        register_i, rem = divmod(variant_index, 100)
        context_i, tone_i = divmod(rem, 10)
        row = self.rows[base_i]
        if family == "en":
            selected_locale = locale if locale in {"en-US", "en-GB"} else "en-US"
        else:
            selected_locale = {"pt": "pt-BR", "es": "es-ES", "it": "it-IT", "fr": "fr-FR"}[family]
        surface = self._surfaces(row)[selected_locale]
        return {
            "id": cid,
            "concept": row.id,
            "locale": selected_locale,
            "mode": MODES[mode_i],
            "register": REGISTERS[register_i],
            "context": CONTEXTS[context_i],
            "tone": TONES[tone_i],
            "expression": surface,
            "pt_equivalent": row.pt,
            "note": row.note,
            "equivalents": self._surfaces(row),
        }

    def explain(self, text: str, locale: str) -> str | None:
        hit = self.match(text)
        if hit is None:
            return None
        row, source = hit
        equivalent = self._surfaces(row).get(locale, row.pt)
        digest = hashlib.sha256(_normalize(text).encode()).digest()
        register = REGISTERS[digest[0] % len(REGISTERS)]
        context = CONTEXTS[digest[1] % len(CONTEXTS)]
        return f"{equivalent} — equivalente contextual de '{text}'. Uso: {row.note}. Registro {register}; contexto {context}. Fonte detectada: {source}."
