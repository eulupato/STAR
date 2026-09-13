"""Catálogo local de Química da STAR: 500 tópicos x 1.000 = 500.000 conteúdos.

Os 500 mil conteúdos são variações determinísticas/endereçáveis construídas a
partir de 500 núcleos científicos canônicos. A materialização é sob demanda;
nenhuma lista de meio milhão de objetos é criada no startup.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
import unicodedata
from collections import Counter

from core.chemistry_topics_01 import CHEMISTRY_ROWS_01
from core.chemistry_topics_05 import CHEMISTRY_ROWS_05
from core.chemistry_topics_06 import CHEMISTRY_ROWS_06
from core.chemistry_topics_07 import CHEMISTRY_ROWS_07
from core.chemistry_topics_08 import CHEMISTRY_ROWS_08
from core.chemistry_topics_09 import CHEMISTRY_ROWS_09
from core.chemistry_topics_10 import CHEMISTRY_ROWS_10
from core.chemistry_topics_11 import CHEMISTRY_ROWS_11
from core.chemistry_topics_12 import CHEMISTRY_ROWS_12
from core.chemistry_topics_13 import CHEMISTRY_ROWS_13
from core.chemistry_topics_14 import CHEMISTRY_ROWS_14
from core.chemistry_topics_15 import CHEMISTRY_ROWS_15
from core.chemistry_topics_16 import CHEMISTRY_ROWS_16
from core.chemistry_topics_17 import CHEMISTRY_ROWS_17
from core.chemistry_topics_18 import CHEMISTRY_ROWS_18
from core.chemistry_topics_19 import CHEMISTRY_ROWS_19
from core.chemistry_topics_20 import CHEMISTRY_ROWS_20

SOURCES = {
    "IUPAC": "IUPAC Compendium of Chemical Terminology (Gold Book), 5th ed., online 5.0.0 (2025)",
    "OPENSTAX": "OpenStax Chemistry 2e",
    "NIST_WEBBOOK": "NIST Chemistry WebBook, SRD 69 (data updated 2025)",
    "PUBCHEM": "NIH/NLM PubChem",
    "MIT_5111": "MIT OpenCourseWare 5.111 Principles of Chemical Science",
    "MIT_560": "MIT OpenCourseWare 5.60 Thermodynamics & Kinetics",
    "MIT_561": "MIT OpenCourseWare 5.61 Physical Chemistry",
    "MIT_ORG": "MIT OpenCourseWare 5.12 Organic Chemistry I",
    "MIT_ADV_ORG": "MIT OpenCourseWare 5.43 Advanced Organic Chemistry",
    "MIT_INORG": "MIT OpenCourseWare inorganic/chemical science references",
    "MIT_EXPERIMENTAL": "MIT OpenCourseWare 5.35 Introduction to Experimental Chemistry",
    "NIST_CCCBDB": "NIST Computational Chemistry Comparison and Benchmark Database, SRD 101",
    "LIBRE_ANALYTICAL": "Chemistry LibreTexts Analytical and Instrumental Chemistry",
    "IAEA": "International Atomic Energy Agency radiochemistry and nuclear chemistry references",
}

FAMILIES = (
    "conceito", "formula", "variaveis_unidades", "hipoteses_validade", "derivacao",
    "calculo", "aplicacao", "erros_comuns", "limites", "conexoes",
)
STYLES = (
    "direto", "intuitivo", "didatico", "tecnico", "vestibular", "graduacao",
    "laboratorio", "engenharia", "pesquisa", "revisao",
)
CONTEXTS = (
    "definicao", "interpretacao", "simbolico", "dimensional", "experimental",
    "comparativo", "estimativa", "caso_limite", "aplicado", "checagem",
)
VARIANTS_PER_TOPIC = 1000
TOTAL_TOPICS = 500
TOTAL_DOMAINS = 20
TOPICS_PER_DOMAIN = 25
TOTAL_VARIANTS = TOTAL_TOPICS * VARIANTS_PER_TOPIC

_SEARCH_STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "e",
    "qual", "quais", "me", "diga", "explique", "explica", "sobre", "formula",
    "equacao", "expressao", "conceito", "como", "funciona", "na", "no", "para",
    "quimica", "quimico", "quimica", "relacao", "lei",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("_", " ")
    text = re.sub(r"[^a-z0-9+\- ]+", " ", text)
    return " ".join(text.split())


@dataclass(frozen=True)
class ChemistryTopic:
    id: str
    domain: str
    level: int
    title: str
    formula: str
    summary: str
    aliases: tuple[str, ...]
    source: str


_RAW_BLOCKS = (
    CHEMISTRY_ROWS_01, CHEMISTRY_ROWS_05, CHEMISTRY_ROWS_06, CHEMISTRY_ROWS_07,
    CHEMISTRY_ROWS_08, CHEMISTRY_ROWS_09, CHEMISTRY_ROWS_10, CHEMISTRY_ROWS_11,
    CHEMISTRY_ROWS_12, CHEMISTRY_ROWS_13, CHEMISTRY_ROWS_14, CHEMISTRY_ROWS_15,
    CHEMISTRY_ROWS_16, CHEMISTRY_ROWS_17, CHEMISTRY_ROWS_18, CHEMISTRY_ROWS_19,
    CHEMISTRY_ROWS_20,
)


def _load_topics() -> tuple[ChemistryTopic, ...]:
    topics: list[ChemistryTopic] = []
    for block in _RAW_BLOCKS:
        for line in block.strip().splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) != 8:
                raise ValueError(f"chemistry row inválida: {len(parts)} campos em {line[:80]!r}")
            topic_id, domain, level, title, formula, summary, aliases, source = parts
            if source not in SOURCES:
                raise ValueError(f"fonte de Química desconhecida: {source}")
            topics.append(ChemistryTopic(
                topic_id, domain, int(level), title, formula, summary,
                tuple(a.strip() for a in aliases.split(";") if a.strip()), source,
            ))

    if len(topics) != TOTAL_TOPICS:
        raise ValueError(f"Esperados {TOTAL_TOPICS} tópicos de Química; encontrados {len(topics)}")
    if len({t.id for t in topics}) != TOTAL_TOPICS:
        raise ValueError("IDs canônicos de Química devem ser únicos")
    counts = Counter(t.domain for t in topics)
    if len(counts) != TOTAL_DOMAINS:
        raise ValueError(f"Esperados {TOTAL_DOMAINS} domínios; encontrados {len(counts)}")
    bad = {domain: n for domain, n in counts.items() if n != TOPICS_PER_DOMAIN}
    if bad:
        raise ValueError(f"Cada domínio deve ter {TOPICS_PER_DOMAIN} tópicos: {bad}")
    if set(t.level for t in topics) != {1, 2, 3, 4, 5}:
        raise ValueError("Catálogo de Química deve cobrir níveis 1..5")
    return tuple(topics)


TOPICS = _load_topics()


class ChemistryKnowledgeEngine:
    """Engine offline de Química com 500k conteúdos determinísticos."""

    def __init__(self):
        self.topics = TOPICS
        self._search: list[tuple[str, ...]] = []
        for topic in self.topics:
            values = (topic.id, topic.domain, topic.title, *topic.aliases)
            self._search.append(tuple(dict.fromkeys(_normalize(v) for v in values if v)))

    def stats(self) -> dict:
        counts = Counter(t.domain for t in self.topics)
        return {
            "canonical_topics": TOTAL_TOPICS,
            "domains": TOTAL_DOMAINS,
            "topics_per_domain": TOPICS_PER_DOMAIN,
            "variants_per_topic": VARIANTS_PER_TOPIC,
            "content_variations": TOTAL_VARIANTS,
            "levels": [1, 2, 3, 4, 5],
            "families": len(FAMILIES),
            "styles": len(STYLES),
            "contexts": len(CONTEXTS),
            "domain_counts": dict(counts),
        }

    @staticmethod
    def content_id(topic_index: int, variant_index: int) -> str:
        if not 0 <= topic_index < TOTAL_TOPICS or not 0 <= variant_index < VARIANTS_PER_TOPIC:
            raise IndexError("índice fora do catálogo CHEM-000001..CHEM-500000")
        n = topic_index * VARIANTS_PER_TOPIC + variant_index + 1
        return f"CHEM-{n:06d}"

    def get_variant(self, content_id: str):
        match = re.fullmatch(r"CHEM-(\d{6})", str(content_id or "").upper())
        if not match:
            return None
        n = int(match.group(1))
        if not 1 <= n <= TOTAL_VARIANTS:
            return None
        topic_index, local = divmod(n - 1, VARIANTS_PER_TOPIC)
        family_i, within = divmod(local, 100)
        style_i, context_i = divmod(within, 10)
        topic = self.topics[topic_index]
        family, style, context = FAMILIES[family_i], STYLES[style_i], CONTEXTS[context_i]
        return {
            "id": f"CHEM-{n:06d}",
            "topic_id": topic.id,
            "domain": topic.domain,
            "level": topic.level,
            "title": topic.title,
            "family": family,
            "style": style,
            "context": context,
            "prompt": self._prompt(topic, family, style, context),
            "answer": self._render(topic, family, style, context),
            "source": SOURCES[topic.source],
        }

    def match(self, query: str):
        q = _normalize(query)
        if not q:
            return None
        query_tokens = {t for t in q.split() if t not in _SEARCH_STOPWORDS} or set(q.split())
        best = None
        best_score = 0.0
        best_specificity = -1
        for topic, candidates in zip(self.topics, self._search):
            for candidate in candidates:
                candidate_tokens = {t for t in candidate.split() if t not in _SEARCH_STOPWORDS} or set(candidate.split())
                if candidate == q:
                    score = 3.0
                elif len(candidate.split()) >= 2 and candidate in q:
                    score = 2.0 + min(len(candidate_tokens), 10) / 100.0
                else:
                    intersection = len(query_tokens & candidate_tokens)
                    if not intersection:
                        continue
                    coverage = intersection / max(1, len(candidate_tokens))
                    precision = intersection / max(1, len(query_tokens))
                    score = 0.72 * coverage + 0.28 * precision
                    if candidate_tokens <= query_tokens:
                        score += 0.12
                specificity = len(candidate_tokens)
                if score > best_score or (score == best_score and specificity > best_specificity):
                    best, best_score, best_specificity = topic, score, specificity
        return best if best_score >= 0.58 else None

    def answer(self, query: str):
        topic = self.match(query)
        if topic is None:
            return None
        q = _normalize(query)
        if any(k in q for k in ("formula", "equacao", "expressao", "relacao matematica")):
            family = "formula"
        elif any(k in q for k in ("calcule", "calculo", "resolver", "conta", "passo a passo")):
            family = "calculo"
        elif any(k in q for k in ("unidade", "unidades", "variavel", "simbolo", "dimensao")):
            family = "variaveis_unidades"
        elif any(k in q for k in ("hipotese", "validade", "vale quando", "condicao", "assuncao")):
            family = "hipoteses_validade"
        elif any(k in q for k in ("deriv", "demonstr", "de onde vem")):
            family = "derivacao"
        elif any(k in q for k in ("aplic", "serve para", "uso", "exemplo")):
            family = "aplicacao"
        elif any(k in q for k in ("erro", "pegadinha", "confus", "cuidado")):
            family = "erros_comuns"
        elif any(k in q for k in ("limite", "aproxim", "quando nao", "falha")):
            family = "limites"
        elif any(k in q for k in ("conecta", "ligacao com", "correlacion", "relaciona com")):
            family = "conexoes"
        else:
            family = "conceito"
        digest = hashlib.sha256(q.encode("utf-8")).digest()
        return self._render(topic, family, STYLES[digest[0] % 10], CONTEXTS[digest[1] % 10])

    @staticmethod
    def _prompt(topic: ChemistryTopic, family: str, style: str, context: str) -> str:
        verb = {
            "conceito": "Explique", "formula": "Apresente a relação/fórmula de",
            "variaveis_unidades": "Detalhe símbolos, unidades e convenções de",
            "hipoteses_validade": "Liste hipóteses e domínio de validade de",
            "derivacao": "Dê um roteiro de derivação de", "calculo": "Monte um cálculo com",
            "aplicacao": "Dê aplicações de", "erros_comuns": "Aponte erros comuns em",
            "limites": "Explique limites de", "conexoes": "Conecte a outras áreas:",
        }[family]
        return f"{verb} {topic.title} — estilo {style}, contexto {context}."

    @staticmethod
    def _render(topic: ChemistryTopic, family: str, style: str, context: str) -> str:
        ref = SOURCES[topic.source]
        if family == "formula":
            body = f"Relação-base: {topic.formula}. {topic.summary}"
        elif family == "variaveis_unidades":
            body = (
                f"Use {topic.formula}. Identifique símbolos, estados físicos, base de concentração/atividade, "
                "unidades e estado padrão quando aplicável; converta os dados antes do cálculo."
            )
        elif family == "hipoteses_validade":
            body = (
                f"Antes de usar {topic.formula}, cheque idealidade, regime de concentração/pressão, "
                f"temperatura, estado padrão, equilíbrio versus cinética e aproximações do modelo. {topic.summary}"
            )
        elif family == "derivacao":
            body = (
                f"Roteiro: declare espécies e hipóteses; aplique balanços de massa/carga/energia e a lei química "
                f"adequada; derive simbolicamente; confira unidades, sinais, limites e conservação. Referência: {topic.formula}."
            )
        elif family == "calculo":
            body = (
                f"Cálculo: parta de {topic.formula}; liste dados e unidades; converta quantidades de matéria e "
                "concentrações; aplique estequiometria/balanços e, se necessário, equilíbrio ou cinética; isole a "
                "incógnita; calcule; confira algarismos significativos, sinal, ordem de grandeza e plausibilidade química."
            )
        elif family == "aplicacao":
            body = f"{topic.summary} Relação operacional: {topic.formula}."
        elif family == "erros_comuns":
            body = (
                f"Evite aplicar {topic.formula} fora das hipóteses, confundir concentração com atividade, trocar "
                "coeficiente estequiométrico por expoente indevido, ignorar carga/estado físico, misturar unidades, "
                "confundir equilíbrio com velocidade ou arredondar cedo demais."
            )
        elif family == "limites":
            body = (
                f"Teste {topic.formula} em diluição/concentração, temperatura, pressão e composição relevantes; "
                f"identifique idealizações e não extrapole além do regime em que o modelo é válido. {topic.summary}"
            )
        elif family == "conexoes":
            body = (
                f"{topic.summary} Conecte com conservação de massa/carga/energia, estrutura eletrônica, "
                f"termodinâmica, cinética, equilíbrio, espectroscopia ou materiais conforme o caso. Relação-base: {topic.formula}."
            )
        else:
            body = f"{topic.summary} Relação central: {topic.formula}."
        return f"{topic.title} — nível {topic.level}. {body} [Fonte técnica: {ref}; modo {style}/{context}]"
