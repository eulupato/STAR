"""BLOCO 8 — Linguagem e Comunicação da STAR.

Organiza conhecimento linguístico e comunicacional geral sobre o mesmo BLOCO 2,
BLOCO 3 e Knowledge Graph. Reutiliza o LanguageManager, localização e catálogo
pragmático existentes sem criar um runtime de tradução paralelo.

O BLOCO 8 distingue conhecimento linguístico de suporte operacional de locale:
alemão, mandarim e japonês entram na arquitetura de conhecimento B08 agora, mas
não são declarados como idiomas completos de interface/tradução enquanto o
runtime oficial ainda não os suportar.

Escala: 50 ramos x 20 lentes = 1.000 nós; 1.000.000 variações/no = 1B
endereçáveis em B08, sempre materializados sob demanda.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
import unicodedata
from typing import Any

from core.universal_knowledge import UniversalKnowledgeArchitecture


@dataclass(frozen=True)
class CommunicationBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in raw.split(";") if x.strip())


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).casefold()
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value


def _clean(text: str) -> str:
    return " ".join(str(text or "").strip().split())


COMMUNICATION_DOMAINS = (
    "language_systems",
    "grammar_structure",
    "meaning_pragmatics",
    "writing_conventions",
    "variation_register",
    "figurative_humor",
    "narrative_discourse",
    "indirect_communication",
    "multimodal_nonverbal",
    "speech_voice",
    "digital_language",
    "culture_sociolinguistics",
    "translation_multilingualism",
)

DOMAIN_LABELS = {
    "language_systems": "Sistemas linguísticos",
    "grammar_structure": "Gramática, sintaxe e estrutura",
    "meaning_pragmatics": "Semântica, pragmática e significado",
    "writing_conventions": "Ortografia, pontuação e escrita",
    "variation_register": "Variação, dialetos e registros",
    "figurative_humor": "Linguagem figurada, ironia e humor",
    "narrative_discourse": "Narrativa, discurso e conversação",
    "indirect_communication": "Comunicação indireta e intenção",
    "multimodal_nonverbal": "Gestos e comunicação não verbal",
    "speech_voice": "Voz, prosódia e silêncio",
    "digital_language": "Linguagem digital e internetês",
    "culture_sociolinguistics": "Cultura, sociedade e identidade linguística",
    "translation_multilingualism": "Tradução, contraste e multilinguismo",
}

COMMUNICATION_BRANCHES = (
    CommunicationBranch("language_systems", "phonetics_phonology", "Fonética e fonologia", _subs("sons da fala;fonemas;alofones;prosódia;ritmo;entonação;contrastes sonoros")),
    CommunicationBranch("language_systems", "writing_systems", "Sistemas de escrita e relação som-grafia", _subs("alfabetos;silabários;caracteres;grafemas;romanização;transliteração;pronúncia e escrita")),
    CommunicationBranch("language_systems", "morphology", "Morfologia", _subs("morfemas;flexão;derivação;composição;palavras;marcação gramatical")),
    CommunicationBranch("language_systems", "lexicon_word_formation", "Léxico e formação de palavras", _subs("léxico;vocabulário;neologismos;empréstimos;derivação;composição;mudança lexical")),

    CommunicationBranch("grammar_structure", "parts_of_speech", "Classes e categorias gramaticais", _subs("substantivos;verbos;adjetivos;advérbios;pronomes;determinantes;preposições;partículas")),
    CommunicationBranch("grammar_structure", "phrase_structure", "Sintagmas e constituintes", _subs("sintagmas;constituintes;núcleo;modificadores;dependências;hierarquia estrutural")),
    CommunicationBranch("grammar_structure", "sentence_syntax", "Sintaxe de orações e sentenças", _subs("sintaxe;orações;coordenação;subordinação;argumentos;adjuntos;ordem de palavras")),
    CommunicationBranch("grammar_structure", "agreement_word_order", "Concordância, regência e ordem", _subs("concordância;regência;caso;ordem de constituintes;marcação;restrições gramaticais")),
    CommunicationBranch("grammar_structure", "grammar_variation", "Variação gramatical", _subs("gramática normativa;gramática descritiva;variação;mudança;uso;adequação contextual")),

    CommunicationBranch("meaning_pragmatics", "lexical_semantics", "Semântica lexical", _subs("semântica;sentido;referência;polissemia;sinonímia;antonímia;campos semânticos")),
    CommunicationBranch("meaning_pragmatics", "compositional_semantics", "Semântica composicional", _subs("composição de significado;escopo;negação;quantificação;ambiguidade estrutural;relações semânticas")),
    CommunicationBranch("meaning_pragmatics", "pragmatics_context", "Pragmática e contexto", _subs("pragmática;contexto;uso;atos de fala;inferência;conhecimento compartilhado;adequação")),
    CommunicationBranch("meaning_pragmatics", "implicature_presupposition", "Implicatura, pressuposição e subentendido", _subs("implicatura;pressuposição;subentendido;inferência pragmática;cooperação;cancelabilidade;ambiguidade")),
    CommunicationBranch("meaning_pragmatics", "reference_deixis", "Referência, dêixis e anáfora", _subs("referência;dêixis;anáfora;pronomes;tempo;espaço;pessoa;contexto discursivo")),

    CommunicationBranch("writing_conventions", "orthography", "Ortografia", _subs("ortografia;grafia;acentuação;maiúsculas;hífen;convenções;variação ortográfica")),
    CommunicationBranch("writing_conventions", "punctuation", "Pontuação", _subs("pontuação;vírgula;ponto;ponto e vírgula;dois-pontos;travessão;aspas;efeitos pragmáticos")),
    CommunicationBranch("writing_conventions", "writing_cohesion", "Coesão e coerência textual", _subs("coesão;coerência;referenciação;conectores;progressão temática;parágrafos;organização textual")),
    CommunicationBranch("writing_conventions", "spelling_style_variation", "Convenções e estilos de escrita", _subs("normas editoriais;abreviações;capitalização;estilo;formatação;variação histórica e regional")),

    CommunicationBranch("variation_register", "formal_register", "Linguagem formal", _subs("linguagem formal;registro culto;institucional;acadêmico;profissional;adequação;polidez")),
    CommunicationBranch("variation_register", "informal_register", "Linguagem informal", _subs("linguagem informal;coloquialidade;conversa cotidiana;reduções;marcadores discursivos;proximidade")),
    CommunicationBranch("variation_register", "slang", "Gírias", _subs("gírias;vocabulário de grupo;renovação lexical;marcadores identitários;contexto geracional;apropriação")),
    CommunicationBranch("variation_register", "dialects_regionalisms", "Dialetos e regionalismos", _subs("dialetos;regionalismos;sotaques;variedades;geografia linguística;prestígio;estigma linguístico")),
    CommunicationBranch("variation_register", "code_switching", "Alternância de código e repertórios", _subs("code-switching;code-mixing;repertórios multilíngues;empréstimos;acomodação;identidade")),

    CommunicationBranch("figurative_humor", "irony", "Ironia", _subs("ironia;contraste entre forma e sentido;contexto;tom;expectativas;ambiguidade;interpretações alternativas")),
    CommunicationBranch("figurative_humor", "sarcasm", "Sarcasmo", _subs("sarcasmo;ironia avaliativa;prosódia;contexto relacional;marcadores;risco de interpretação equivocada")),
    CommunicationBranch("figurative_humor", "humor", "Humor", _subs("humor;incongruência;timing;piadas;jogos de palavras;referências culturais;contexto social")),
    CommunicationBranch("figurative_humor", "metaphor", "Metáfora e linguagem figurada", _subs("metáfora;metonímia;analogia;hipérbole;personificação;sentido figurado;convencionalização")),
    CommunicationBranch("figurative_humor", "idioms_figures", "Expressões idiomáticas e figuras de linguagem", _subs("idiomas;expressões fixas;provérbios;figuras de linguagem;equivalência pragmática;não literalidade")),

    CommunicationBranch("narrative_discourse", "narrative_structure", "Estrutura narrativa", _subs("narrativa;enredo;tempo narrativo;personagens;causalidade;conflito;resolução")),
    CommunicationBranch("narrative_discourse", "storytelling_voice", "Voz narrativa e ponto de vista", _subs("narrador;ponto de vista;focalização;voz;estilo;confiabilidade narrativa;perspectiva")),
    CommunicationBranch("narrative_discourse", "discourse_cohesion", "Discurso, tópicos e coerência", _subs("discurso;tópico;foco;coesão;coerência;estrutura informacional;continuidade")),
    CommunicationBranch("narrative_discourse", "conversation_turntaking", "Conversação e turnos", _subs("turnos de fala;pares adjacentes;interrupções;sobreposição;reparo;feedback;marcadores conversacionais")),

    CommunicationBranch("indirect_communication", "indirect_communication", "Comunicação indireta", _subs("comunicação indireta;pedidos indiretos;insinuação;evasão;subtexto;polidez;contexto")),
    CommunicationBranch("indirect_communication", "politeness_face", "Polidez, face e mitigação", _subs("polidez;face social;mitigação;atenuação;honoríficos;distância social;relações de poder")),
    CommunicationBranch("indirect_communication", "ambiguity_repair", "Ambiguidade, mal-entendido e reparo", _subs("ambiguidade;mal-entendido;clarificação;reparo;paráfrase;confirmação;desambiguação")),
    CommunicationBranch("indirect_communication", "intent_interpretation", "Intenção comunicativa e limites de inferência", _subs("intenção;objetivo comunicativo;atos de fala;subtexto;evidência contextual;interpretações alternativas;incerteza")),

    CommunicationBranch("multimodal_nonverbal", "gestures", "Gestos", _subs("gestos;emblemas;gesticulação;apontamento;ritmo;contexto cultural;multimodalidade")),
    CommunicationBranch("multimodal_nonverbal", "facial_body_signals", "Expressões faciais, olhar e postura", _subs("expressões faciais;olhar;postura;orientação corporal;distância;sincronia;contexto")),

    CommunicationBranch("speech_voice", "voice_prosody", "Voz e prosódia", _subs("voz;prosódia;entonação;ritmo;volume;velocidade;qualidade vocal;ênfase")),
    CommunicationBranch("speech_voice", "silence_pauses", "Silêncio e pausas", _subs("silêncio;pausas;hesitação;tempo de resposta;turn-taking;ênfase;contexto cultural;ambiguidade")),
    CommunicationBranch("speech_voice", "speech_fluency", "Fluência, hesitação e planejamento da fala", _subs("fluência;disfluência;repetição;autocorreção;planejamento;marcadores de hesitação;fala espontânea")),

    CommunicationBranch("digital_language", "internet_language", "Internetês", _subs("internetês;abreviações;ortografia criativa;repetição;capitalização;pontuação expressiva;velocidade;comunidade")),
    CommunicationBranch("digital_language", "memes_emojis", "Emojis, memes e sinais digitais", _subs("emojis;memes;GIFs;reações;stickers;marcadores paralinguísticos;contexto de plataforma")),
    CommunicationBranch("digital_language", "digital_conversation", "Conversação em plataformas digitais", _subs("mensagens;DMs;grupos;threads;assíncrono;respostas;quoting;context collapse")),

    CommunicationBranch("culture_sociolinguistics", "sociolinguistics_culture", "Sociolinguística e cultura", _subs("sociolinguística;cultura;comunidades de fala;normas;prestígio;variação;contexto social")),
    CommunicationBranch("culture_sociolinguistics", "language_identity", "Linguagem, identidade e pertencimento", _subs("identidade linguística;pertencimento;estilo;acomodação;autenticidade;grupo;estigma")),
    CommunicationBranch("culture_sociolinguistics", "language_change", "Mudança linguística", _subs("mudança linguística;gramaticalização;mudança semântica;mudança sonora;difusão;gerações;contato")),
    CommunicationBranch("culture_sociolinguistics", "cross_cultural_communication", "Comunicação intercultural", _subs("comunicação intercultural;normas;polidez;gestos;silêncio;registro;mal-entendidos;adaptação")),

    CommunicationBranch("translation_multilingualism", "translation_equivalence", "Tradução e equivalência", _subs("tradução;equivalência semântica;equivalência pragmática;literalidade;adaptação;perdas e ganhos;contexto")),
    CommunicationBranch("translation_multilingualism", "multilingual_comparison", "Comparação entre idiomas e multilinguismo", _subs("português;inglês;espanhol;francês;italiano;alemão;mandarim;japonês;tipologia;multilinguismo;idiomas futuros")),
)

COMMUNICATION_LENSES = (
    ("concept", "conceito", "definir o fenômeno e distinguir termos próximos"),
    ("form", "forma", "descrever formas possíveis sem assumir significado fora do contexto"),
    ("function", "função", "explicar funções comunicativas possíveis"),
    ("grammar", "gramática", "relacionar regras, padrões, usos e variação gramatical"),
    ("syntax", "sintaxe", "examinar estrutura, constituintes e dependências"),
    ("semantics", "semântica", "distinguir sentido lexical, composicional e ambiguidades"),
    ("pragmatics", "pragmática", "interpretar uso em contexto, implicaturas e atos de fala"),
    ("orthography", "ortografia e pontuação", "observar grafia, pontuação e seus efeitos sem confundi-los com intenção certa"),
    ("variation", "variação", "comparar dialetos, regionalismos, gírias e mudança"),
    ("register", "registro", "distinguir formalidade, informalidade, proximidade e adequação"),
    ("culture", "cultura", "preservar normas culturais, históricas e comunitárias"),
    ("intention", "intenção", "tratar intenção comunicativa como hipótese dependente de contexto e evidência"),
    ("context", "contexto", "considerar situação, participantes, canal e conhecimento compartilhado"),
    ("meaning", "significado", "mapear significados literais, contextuais, figurados e implícitos"),
    ("structure", "estrutura", "analisar da palavra ao discurso e à composição multimodal"),
    ("situation", "situação", "comparar comunicação síncrona, assíncrona e condições de uso"),
    ("evidence", "evidência e interpretação", "separar sinal observado, inferência e evidência corroborante"),
    ("exceptions", "exceções e limites", "registrar exceções, casos-limite e leituras alternativas"),
    ("contrast", "contraste entre idiomas", "comparar estruturas e usos sem forçar equivalência literal"),
    ("application", "aplicação comunicativa", "aplicar o conhecimento preservando audiência, objetivo e contexto"),
)

LANGUAGE_VARIANTS = (
    "portuguese",
    "english",
    "spanish",
    "french",
    "italian",
    "german",
    "mandarin_chinese",
    "japanese",
    "multilingual_comparative",
    "future_language_extension",
)
DIALECT_VARIANTS = ("reference_standard", "regional_variant", "urban_colloquial", "contact_diaspora", "community_specific")
CONTEXT_VARIANTS = ("everyday", "professional", "education", "digital", "artistic_media")
INTENTION_VARIANTS = ("inform", "request_coordinate", "persuade_negotiate", "express_relate", "imply_play")
REGISTER_VARIANTS = ("formal", "neutral", "informal", "intimate_internet")
CULTURE_VARIANTS = ("local_community", "national_regional", "intercultural", "historical_generational")
MEANING_VARIANTS = ("literal", "contextual", "figurative", "ambiguous_polysemous", "implicature_inferred")
STRUCTURE_VARIANTS = ("word", "phrase", "clause_sentence", "discourse_conversation", "multimodal_turn")
SITUATION_VARIANTS = ("synchronous", "asynchronous")

VARIANT_AXES = (
    ("language", LANGUAGE_VARIANTS),
    ("dialect", DIALECT_VARIANTS),
    ("context", CONTEXT_VARIANTS),
    ("intention", INTENTION_VARIANTS),
    ("register", REGISTER_VARIANTS),
    ("culture", CULTURE_VARIANTS),
    ("meaning", MEANING_VARIANTS),
    ("structure", STRUCTURE_VARIANTS),
    ("situation", SITUATION_VARIANTS),
)

CANONICAL_NODES = len(COMMUNICATION_BRANCHES) * len(COMMUNICATION_LENSES)
VARIANTS_PER_NODE = 1
for _axis_name, _axis_values in VARIANT_AXES:
    VARIANTS_PER_NODE *= len(_axis_values)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE

if len(COMMUNICATION_DOMAINS) != 13:
    raise RuntimeError("BLOCO 8 deve manter exatamente 13 domínios")
if len(COMMUNICATION_BRANCHES) != 50:
    raise RuntimeError(f"BLOCO 8 deve manter exatamente 50 ramos; encontrados {len(COMMUNICATION_BRANCHES)}")
if len(COMMUNICATION_LENSES) != 20:
    raise RuntimeError("BLOCO 8 deve manter exatamente 20 lentes")
if CANONICAL_NODES != 1_000:
    raise RuntimeError("BLOCO 8 deve manter exatamente 1.000 nós canônicos")
if VARIANTS_PER_NODE != 1_000_000:
    raise RuntimeError(f"BLOCO 8 deve manter exatamente 1.000.000 variações por nó; encontradas {VARIANTS_PER_NODE}")
if ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("BLOCO 8 deve manter exatamente 1B de representações endereçáveis")

REQUESTED_LANGUAGES = (
    "português", "inglês", "espanhol", "francês", "italiano", "alemão", "mandarim", "japonês",
)
REQUESTED_TOPICS = (
    "gramática", "sintaxe", "semântica", "pragmática", "ortografia", "pontuação", "gírias", "dialetos",
    "regionalismos", "internetês", "linguagem formal", "linguagem informal", "ironia", "sarcasmo", "humor",
    "metáfora", "narrativa", "comunicação indireta", "gestos", "voz", "silêncio",
)

INTERPRETATION_POLICY = {
    "surface_form_is_single_meaning": False,
    "expression_is_certain_intention": False,
    "gesture_is_certain_intention": False,
    "prosody_is_certain_intention": False,
    "silence_is_certain_intention": False,
    "irony_sarcasm_requires_context": True,
    "cultural_context_required": True,
    "alternative_interpretations_required": True,
    "automatic_mind_reading": False,
    "rule": "FORMA OU SINAL ISOLADO ≠ SIGNIFICADO ÚNICO, INTENÇÃO OU CERTEZA",
}

LANGUAGE_PROFILES = {
    "portuguese": {"label": "Português", "codes": ("pt-BR",)},
    "english": {"label": "Inglês", "codes": ("en-US", "en-GB")},
    "spanish": {"label": "Espanhol", "codes": ("es-ES",)},
    "french": {"label": "Francês", "codes": ("fr-FR",)},
    "italian": {"label": "Italiano", "codes": ("it-IT",)},
    "german": {"label": "Alemão", "codes": ("de-DE",)},
    "mandarin_chinese": {"label": "Mandarim", "codes": ("zh-CN",)},
    "japanese": {"label": "Japonês", "codes": ("ja-JP",)},
    "multilingual_comparative": {"label": "Comparação multilíngue", "codes": ()},
    "future_language_extension": {"label": "Demais idiomas futuramente", "codes": ()},
}

CROSS_DOMAIN_RELATIONS = {
    "psychology": ("intenção", "teoria da mente", "relações", "emoção", "comportamento"),
    "human_life": ("voz", "audição", "sistema nervoso", "desenvolvimento"),
    "knowledge": ("semântica", "conceitos", "aliases", "contextos", "proveniência"),
}


def _decode_axes(index: int) -> dict[str, str]:
    if not 0 <= int(index) < VARIANTS_PER_NODE:
        raise IndexError(index)
    remainder = int(index)
    decoded: dict[str, str] = {}
    for name, values in reversed(VARIANT_AXES):
        remainder, offset = divmod(remainder, len(values))
        decoded[name] = values[offset]
    if remainder:
        raise RuntimeError("falha ao decodificar variante B08")
    return {name: decoded[name] for name, _ in VARIANT_AXES}


class CommunicationCatalog:
    NAMESPACE = "B08"
    PREFIX = "LANG-B08"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "domains": len(COMMUNICATION_DOMAINS),
            "branches": len(COMMUNICATION_BRANCHES),
            "lenses_per_branch": len(COMMUNICATION_LENSES),
            "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS,
            "variant_axes": {name: len(values) for name, values in VARIANT_AXES},
            "materialization": "on-demand",
            "prepopulated_knowledge_rows": 0,
            "truthfulness_note": (
                "1B são representações linguísticas/comunicacionais determinísticas endereçáveis; "
                "não 1B de frases, traduções ou fatos independentes pré-carregados"
            ),
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        node_index = int(node_index)
        variant_index = int(variant_index)
        if not 0 <= node_index < CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= variant_index < VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = node_index * VARIANTS_PER_NODE + variant_index + 1
        return f"LANG-B08-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"LANG-B08-(\d{10})", str(identifier or "").strip().upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, len(COMMUNICATION_LENSES))
        branch = COMMUNICATION_BRANCHES[branch_index]
        lens_key, lens_label, instruction = COMMUNICATION_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {
            "id": f"LANG-B08-{absolute:010d}",
            "namespace": self.NAMESPACE,
            "domain": branch.domain,
            "domain_label": DOMAIN_LABELS[branch.domain],
            "branch": branch.key,
            "branch_label": branch.label,
            "subtopics": branch.subtopics,
            "lens": lens_key,
            "lens_label": lens_label,
            **axes,
            "prompt": (
                f"{DOMAIN_LABELS[branch.domain]} / {branch.label} / {lens_label}: {instruction}. "
                f"Idioma={axes['language']}; dialeto={axes['dialect']}; contexto={axes['context']}; "
                f"intenção={axes['intention']}; registro={axes['register']}; cultura={axes['culture']}; "
                f"significado={axes['meaning']}; estrutura={axes['structure']}; situação={axes['situation']}. "
                "Preservar variação, polissemia, contexto cultural e leituras alternativas; "
                "forma, gesto, voz ou silêncio isolados não provam intenção."
            ),
        }


class LanguageCommunicationFoundations:
    NAMESPACE = "B08"
    TAXONOMY_ROOT_ID = "LANG-TAX-ROOT"

    def __init__(self, knowledge: UniversalKnowledgeArchitecture, *, language_manager=None, human_psychology=None):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.language_manager = language_manager
        self.human_psychology = human_psychology
        self.catalog = CommunicationCatalog()
        self._providers: dict[str, Any] = {}
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 8 — LINGUAGEM E COMUNICAÇÃO",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/language_communication.py",
            metadata={
                "materialization": "on-demand",
                "canonical_gate": "BLOCO 2 -> BLOCO 3",
                "knowledge_graph": "shared",
                "runtime_language_manager": "reused",
                "parallel_translation_runtime": False,
                "knowledge_languages": list(REQUESTED_LANGUAGES),
                "future_languages_extensible": True,
                "communication_intent_certainty": False,
            },
        )

    @staticmethod
    def _domain_key(value: str) -> str:
        normalized = _norm(value)
        aliases = {
            "gramatica": "grammar_structure", "sintaxe": "grammar_structure", "estrutura": "grammar_structure",
            "semantica": "meaning_pragmatics", "pragmatica": "meaning_pragmatics", "significado": "meaning_pragmatics",
            "ortografia": "writing_conventions", "pontuacao": "writing_conventions", "escrita": "writing_conventions",
            "girias": "variation_register", "dialetos": "variation_register", "regionalismos": "variation_register", "registro": "variation_register",
            "ironia": "figurative_humor", "sarcasmo": "figurative_humor", "humor": "figurative_humor", "metafora": "figurative_humor",
            "narrativa": "narrative_discourse", "discurso": "narrative_discourse", "conversacao": "narrative_discourse",
            "comunicacao_indireta": "indirect_communication", "intencao": "indirect_communication",
            "gestos": "multimodal_nonverbal", "nao_verbal": "multimodal_nonverbal",
            "voz": "speech_voice", "silencio": "speech_voice", "prosodia": "speech_voice",
            "internetes": "digital_language", "internet": "digital_language", "emojis": "digital_language",
            "cultura": "culture_sociolinguistics", "sociolinguistica": "culture_sociolinguistics",
            "traducao": "translation_multilingualism", "idiomas": "translation_multilingualism", "multilinguismo": "translation_multilingualism",
            "linguagem": "language_systems", "fonologia": "language_systems", "morfologia": "language_systems",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _branch(key: str) -> CommunicationBranch:
        for branch in COMMUNICATION_BRANCHES:
            if branch.key == key:
                return branch
        raise KeyError(key)

    @staticmethod
    def _domain_node_id(domain: str) -> str:
        return f"LANG-DOM-{domain.upper()}"

    @staticmethod
    def _branch_node_id(branch: str) -> str:
        return f"LANG-BR-{branch.upper()}"

    @staticmethod
    def _subtopic_node_id(branch: str, subtopic: str) -> str:
        return f"LANG-SUB-{branch.upper()}-{_norm(subtopic).upper()[:80]}"

    def runtime_language_support(self) -> dict:
        from core.language_catalog import LOCALES

        operational_codes = set(LOCALES)
        languages = []
        for key in LANGUAGE_VARIANTS:
            profile = LANGUAGE_PROFILES[key]
            codes = tuple(profile["codes"])
            operational = bool(codes) and any(code in operational_codes for code in codes)
            languages.append({
                "key": key,
                "label": profile["label"],
                "knowledge_supported": True,
                "operational_runtime": operational,
                "runtime_locale_codes": [code for code in codes if code in operational_codes],
                "planned_or_extensible": not operational,
            })
        return {
            "knowledge_languages": languages,
            "operational_locales": sorted(operational_codes),
            "rule": "conhecimento linguístico B08 não implica suporte operacional completo de locale/tradução",
        }

    def taxonomy_snapshot(self, domain: str | None = None) -> dict:
        key = self._domain_key(domain) if domain else None
        if key and key not in COMMUNICATION_DOMAINS:
            raise KeyError(domain)
        selected = [b for b in COMMUNICATION_BRANCHES if key is None or b.domain == key]
        return {
            "root": "Linguagem e Comunicação",
            "domain": key,
            "branches": [
                {"domain": b.domain, "domain_label": DOMAIN_LABELS[b.domain], "branch": b.key, "branch_label": b.label, "subtopics": list(b.subtopics)}
                for b in selected
            ],
            "cross_domain_relations": deepcopy(CROSS_DOMAIN_RELATIONS),
            "interpretation_policy": deepcopy(INTERPRETATION_POLICY),
        }

    def _ensure_taxonomy_path(self, branch: CommunicationBranch, *, include_subtopics: bool = True) -> dict:
        root = self.graph.add_entity(
            "language_communication_taxonomy",
            "Linguagem e Comunicação",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B08", "source_of_truth": "core/language_communication.py"},
        )
        psychology_root = "PSY-TAX-ROOT"
        self.graph.add_entity("human_psychology_taxonomy", "Mente Humana e Psicologia", node_id=psychology_root, data={"block": "B07"})
        self.graph.relate(root, psychology_root, "related_to", metadata={"block": "B08", "communication_psychology_context": True})
        self.graph.relate(psychology_root, root, "related_to", metadata={"block": "B08", "language_context": True})

        domain_id = self._domain_node_id(branch.domain)
        self.graph.add_entity("communication_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id, data={"block": "B08", "domain": branch.domain})
        self.graph.relate(root, domain_id, "has_part", metadata={"block": "B08", "taxonomy": True})
        self.graph.relate(domain_id, root, "part_of", metadata={"block": "B08", "taxonomy": True})

        branch_id = self._branch_node_id(branch.key)
        self.graph.add_entity("communication_branch", branch.label, node_id=branch_id, data={"block": "B08", "domain": branch.domain, "branch": branch.key})
        self.graph.relate(domain_id, branch_id, "has_part", metadata={"block": "B08", "taxonomy": True})
        self.graph.relate(branch_id, domain_id, "part_of", metadata={"block": "B08", "taxonomy": True})

        sub_ids = []
        if include_subtopics:
            for subtopic in branch.subtopics:
                sub_id = self._subtopic_node_id(branch.key, subtopic)
                self.graph.add_entity("communication_subtopic", subtopic, node_id=sub_id, data={"block": "B08", "domain": branch.domain, "branch": branch.key})
                self.graph.relate(branch_id, sub_id, "has_part", metadata={"block": "B08", "taxonomy": True})
                self.graph.relate(sub_id, branch_id, "part_of", metadata={"block": "B08", "taxonomy": True})
                sub_ids.append(sub_id)
        return {"root_id": root, "domain_id": domain_id, "branch_id": branch_id, "subtopic_ids": sub_ids}

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        key = self._domain_key(domain) if domain else None
        if key and key not in COMMUNICATION_DOMAINS:
            raise KeyError(domain)
        selected = [b for b in COMMUNICATION_BRANCHES if key is None or b.domain == key]
        paths = [self._ensure_taxonomy_path(branch) for branch in selected]
        return {"domain": key, "branches_materialized": len(paths), "knowledge_graph": "shared", "parallel_language_graph_created": False, "paths": paths}

    def interpret_communication(
        self,
        message: str,
        *,
        context: str = "",
        language: str = "",
        dialect: str = "",
        register: str = "",
        signals: tuple[str, ...] | list[str] | None = None,
    ) -> dict:
        message = _clean(message)
        if not message:
            raise ValueError("mensagem vazia")
        observed_signals = [_clean(item) for item in (signals or ()) if _clean(item)]
        possibilities = [
            "leitura literal compatível com as palavras usadas",
            "significado pragmático dependente da situação e do conhecimento compartilhado",
            "uso figurado, metafórico ou idiomático",
            "ironia ou sarcasmo somente se houver marcadores e contexto compatíveis",
            "humor, brincadeira ou exagero",
            "comunicação indireta, mitigação ou pedido implícito",
            "ambiguidade lexical, sintática ou referencial",
            "variação dialetal, regional, geracional, cultural ou de plataforma",
        ]
        if observed_signals:
            possibilities.append("gestos, prosódia, pausas ou silêncio podem contextualizar, mas não provar intenção")
        return {
            "message": message,
            "context": _clean(context),
            "language": _clean(language),
            "dialect": _clean(dialect),
            "register": _clean(register),
            "signals": observed_signals,
            "epistemic_kind": "inference",
            "certainty": "underdetermined",
            "possible_interpretations": possibilities,
            "alternative_interpretations_required": True,
            "intention": None,
            "intention_certainty": False,
            "single_signal_proves_meaning": False,
            "policy": deepcopy(INTERPRETATION_POLICY),
            "missing_context": [
                "relação entre participantes e objetivo declarado",
                "situação anterior e posterior à mensagem",
                "dialeto, registro e convenções da comunidade",
                "normas culturais e geracionais",
                "canal, timing, prosódia e sinais não verbais quando disponíveis",
                "possibilidade de ironia, humor, metáfora ou ambiguidade",
            ],
        }

    def operational_equivalent(self, text: str, target_locale: str) -> dict:
        if self.language_manager is None:
            return {"available": False, "reason": "LanguageManager não conectado", "canonicalized": False}
        outcome = self.language_manager.translate_with_report(text, target_locale)
        return {
            "available": bool(outcome.complete),
            "text": outcome.text,
            "source_locale": outcome.source_locale,
            "target_locale": outcome.target_locale,
            "backend": outcome.backend,
            "complete": outcome.complete,
            "canonicalized": False,
            "note": "tradução operacional reutiliza LanguageManager; não vira conhecimento canônico automaticamente",
        }

    def promote_canonical_language_knowledge(
        self,
        record_id: str,
        canonical_label: str,
        *,
        domain: str,
        branch: str,
        knowledge_type: str = "concept",
        aliases=None,
        properties=None,
        subtopics=None,
        contexts=None,
        rules=None,
        exceptions=None,
        summary: str = "",
    ) -> dict:
        domain_key = self._domain_key(domain)
        if domain_key not in COMMUNICATION_DOMAINS:
            raise ValueError(f"domínio B08 inválido: {domain}")
        branch_obj = self._branch(branch)
        if branch_obj.domain != domain_key:
            raise ValueError(f"ramo {branch} não pertence a {domain_key}")
        props = dict(properties or {})
        props.update({
            "communication_intent_certainty": False,
            "single_signal_proves_meaning": False,
            "runtime_translation_support_implied": False,
            "knowledge_scope": "language_and_communication",
        })
        result = self.knowledge.promote_canonical(
            record_id,
            canonical_label,
            knowledge_type=knowledge_type,
            namespace=self.NAMESPACE,
            summary=summary,
            aliases=aliases,
            properties=props,
            categories=["language", "communication", domain_key, branch_obj.key],
            subtopics=subtopics,
            contexts=contexts,
            rules=rules,
            exceptions=exceptions,
            provenance={
                "language_communication_block": "B08",
                "domain": domain_key,
                "branch": branch_obj.key,
                "source_record_id": record_id,
                "runtime_translation_support_implied": False,
            },
        )
        taxonomy = self._ensure_taxonomy_path(branch_obj, include_subtopics=False)
        self.graph.relate(result["knowledge_id"], taxonomy["branch_id"], "is_a", metadata={"block": "B08", "language_taxonomy": True})
        self.graph.relate(taxonomy["branch_id"], result["knowledge_id"], "has_part", metadata={"block": "B08", "language_taxonomy": True})
        return result

    def relate(self, source_id: str, target_id: str, relation: str, *, weight: float = 1.0) -> dict:
        return self.knowledge.relate(source_id, target_id, relation, weight=weight, metadata={"block": "B08", "language_communication": True})

    def policy(self) -> dict:
        return deepcopy(INTERPRETATION_POLICY)

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "domains": [{"key": key, "label": DOMAIN_LABELS[key]} for key in COMMUNICATION_DOMAINS],
            "lenses": [{"key": key, "label": label} for key, label, _ in COMMUNICATION_LENSES],
            "requested_languages": list(REQUESTED_LANGUAGES),
            "requested_topics": list(REQUESTED_TOPICS),
            "runtime_support": self.runtime_language_support(),
            "knowledge_graph": "shared knowledge_nodes/knowledge_edges",
            "canonical_knowledge": "BLOCO 2 gate -> BLOCO 3 -> B08",
            "runtime_language_manager": "reused, not duplicated",
            "interpretation_policy": self.policy(),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {
            "status bloco 8", "status linguagem", "status comunicacao", "status comunicação",
            "linguagem e comunicacao", "linguagem e comunicação", "fundamentos linguisticos", "fundamentos linguísticos",
        }:
            stats = self.stats()
            runtime = stats["runtime_support"]
            operational = sum(1 for item in runtime["knowledge_languages"] if item["operational_runtime"])
            return (
                f"🗣️ BLOCO 8 — LINGUAGEM E COMUNICAÇÃO: {stats['catalog']['addressable_contents']} conteúdos endereçáveis em B08 | "
                f"{stats['catalog']['domains']} domínios × {stats['catalog']['branches']} ramos × {stats['catalog']['lenses_per_branch']} lentes = "
                f"{stats['catalog']['canonical_nodes']} nós | Knowledge Graph=COMPARTILHADO | idiomas de conhecimento={len(REQUESTED_LANGUAGES)} + expansão futura | "
                f"famílias atualmente operacionais no runtime={operational}."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"🗣️ {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        taxonomy = re.match(r"^(?:taxonomia linguagem|taxonomia comunicacao|taxonomia comunicação)(?:\s+(.+))?$", raw, re.I)
        if taxonomy:
            snapshot = self.taxonomy_snapshot(taxonomy.group(1))
            labels = ", ".join(item["branch_label"] for item in snapshot["branches"][:12])
            return f"🗣️ Taxonomia B08: {len(snapshot['branches'])} ramos. {labels}{'…' if len(snapshot['branches']) > 12 else ''}"
        if low in {"idiomas bloco 8", "idiomas b08", "suporte idiomas bloco 8"}:
            support = self.runtime_language_support()
            operational = [item["label"] for item in support["knowledge_languages"] if item["operational_runtime"]]
            planned = [item["label"] for item in support["knowledge_languages"] if item["planned_or_extensible"]]
            return f"🗣️ B08 conhecimento: Português, Inglês, Espanhol, Francês, Italiano, Alemão, Mandarim e Japonês + expansão futura. Runtime operacional atual: {', '.join(operational)}. Ainda não declarados como runtime completo: {', '.join(planned)}."
        if low in {"limites interpretacao comunicacao", "limites interpretação comunicação", "intencao comunicativa automatica", "intenção comunicativa automática"}:
            return "🛡️ BLOCO 8 não trata forma, palavra, gesto, voz, pausa ou silêncio isolados como significado único ou prova de intenção. Ironia, sarcasmo, humor e comunicação indireta permanecem hipóteses contextuais."
        return None
