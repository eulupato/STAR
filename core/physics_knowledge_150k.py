"""Catálogo expandido de Física da STAR: 150 tópicos x 1.000 = 150.000.

Preserva os 50 tópicos/50k IDs já existentes e adiciona 100 tópicos canônicos
novos. A materialização continua sob demanda; nenhuma lista de 150 mil objetos
é criada durante o startup.
"""
from __future__ import annotations

import re

from core.physics_knowledge import (
    CONTEXTS,
    FAMILIES,
    SOURCES as BASE_SOURCES,
    STYLES,
    TOPICS as BASE_TOPICS,
    VARIANTS_PER_TOPIC,
    PhysicsKnowledgeEngine as BasePhysicsKnowledgeEngine,
    PhysicsTopic,
    _normalize,
)
from core.physics_topics_extended import EXTENDED_ROWS, EXTENDED_SOURCES

SOURCES = {**BASE_SOURCES, **EXTENDED_SOURCES}
TOTAL_TOPICS = 150
ADDED_TOPICS = 100
ADDED_VARIANTS = 100000
TOTAL_VARIANTS = TOTAL_TOPICS * VARIANTS_PER_TOPIC

_SEARCH_STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "e",
    "qual", "quais", "me", "diga", "explique", "explica", "sobre", "formula",
    "equacao", "expressao", "conceito", "como", "funciona", "na", "no", "para",
}


def _extended_topics() -> tuple[PhysicsTopic, ...]:
    result = []
    for line in EXTENDED_ROWS.strip().splitlines():
        p = line.split("\t")
        if len(p) != 8:
            raise ValueError(f"physics extended row inválida: {len(p)} campos")
        topic_id, domain, level, title, formula, summary, aliases, source = p
        if source not in SOURCES:
            raise ValueError(f"fonte desconhecida no catálogo expandido: {source}")
        result.append(
            PhysicsTopic(
                topic_id,
                domain,
                int(level),
                title,
                formula,
                summary,
                tuple(a.strip() for a in aliases.split(";") if a.strip()),
                source,
            )
        )
    if len(result) != ADDED_TOPICS:
        raise ValueError(f"Esperados {ADDED_TOPICS} tópicos adicionais; encontrados {len(result)}")
    return tuple(result)


EXTENDED_TOPICS = _extended_topics()
TOPICS = BASE_TOPICS + EXTENDED_TOPICS

if len(TOPICS) != TOTAL_TOPICS:
    raise ValueError(f"Esperados {TOTAL_TOPICS} tópicos totais; encontrados {len(TOPICS)}")
if len({topic.id for topic in TOPICS}) != TOTAL_TOPICS:
    raise ValueError("IDs de tópicos de Física devem ser únicos")


class PhysicsKnowledgeEngine(BasePhysicsKnowledgeEngine):
    """Engine compatível com a API anterior, agora com 150k conteúdos."""

    def __init__(self):
        self.topics = TOPICS
        self._search = []
        for topic in self.topics:
            values = (topic.id, topic.domain, topic.title, *topic.aliases)
            self._search.append(tuple(dict.fromkeys(_normalize(v) for v in values if v)))

    def stats(self):
        return {
            "canonical_topics": TOTAL_TOPICS,
            "base_topics": len(BASE_TOPICS),
            "added_topics": ADDED_TOPICS,
            "variants_per_topic": VARIANTS_PER_TOPIC,
            "base_content_variations": len(BASE_TOPICS) * VARIANTS_PER_TOPIC,
            "added_content_variations": ADDED_VARIANTS,
            "content_variations": TOTAL_VARIANTS,
            "domains": len({t.domain for t in self.topics}),
            "levels": [1, 2, 3, 4, 5],
            "families": len(FAMILIES),
            "styles": len(STYLES),
            "contexts": len(CONTEXTS),
        }

    @staticmethod
    def content_id(topic_index: int, variant_index: int) -> str:
        if not 0 <= topic_index < TOTAL_TOPICS or not 0 <= variant_index < VARIANTS_PER_TOPIC:
            raise IndexError("índice fora do catálogo PHYS-00001..PHYS-150000")
        return f"PHYS-{topic_index * VARIANTS_PER_TOPIC + variant_index + 1:05d}"

    def get_variant(self, content_id: str):
        m = re.fullmatch(r"PHYS-(\d{5,6})", str(content_id or "").upper())
        if not m:
            return None
        n = int(m.group(1))
        if not 1 <= n <= TOTAL_VARIANTS:
            return None
        topic_index, local = divmod(n - 1, VARIANTS_PER_TOPIC)
        family_i, within = divmod(local, 100)
        style_i, context_i = divmod(within, 10)
        topic = self.topics[topic_index]
        family, style, context = FAMILIES[family_i], STYLES[style_i], CONTEXTS[context_i]
        return {
            "id": f"PHYS-{n:05d}",
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
        """Prioriza títulos/aliases específicos sobre coincidências genéricas.

        A base de 150 tópicos torna sobreposição lexical inevitável (ex.: "ondas"
        versus "ondas gravitacionais"). Stopwords e cobertura do candidato evitam
        que um tópico curto/genérico vença uma frase científica mais específica.
        """
        q = _normalize(query).replace("_", " ")
        if not q:
            return None
        query_tokens = {t for t in q.split() if t not in _SEARCH_STOPWORDS}
        if not query_tokens:
            query_tokens = set(q.split())

        best = None
        best_score = 0.0
        best_specificity = -1

        for topic, candidates in zip(self.topics, self._search):
            for raw_candidate in candidates:
                candidate = raw_candidate.replace("_", " ")
                candidate_tokens = {t for t in candidate.split() if t not in _SEARCH_STOPWORDS}
                if not candidate_tokens:
                    candidate_tokens = set(candidate.split())

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
                    best = topic
                    best_score = score
                    best_specificity = specificity

        return best if best_score >= 0.58 else None

    @staticmethod
    def _render(topic, family, style, context):
        ref = SOURCES[topic.source]
        if family == "formula":
            body = f"Fórmula-base: {topic.formula}. {topic.summary}"
        elif family == "variaveis_unidades":
            body = f"Use {topic.formula}. Identifique símbolos, unidades e convenções; converta dados para um sistema coerente e cheque dimensões."
        elif family == "hipoteses_validade":
            body = f"Antes de usar {topic.formula}, cheque regime físico, aproximações, condições iniciais/contorno, simetrias e domínio de validade. {topic.summary}"
        elif family == "derivacao":
            body = f"Roteiro: declare hipóteses; escolha princípios e simetrias; escreva as grandezas; derive simbolicamente; teste dimensões e casos-limite. Resultado de referência: {topic.formula}."
        elif family == "calculo":
            body = f"Cálculo: parta de {topic.formula}; liste dados e unidades; isole a incógnita; substitua; calcule; cheque dimensão, sinal, ordem de grandeza, aproximações e regime físico."
        elif family == "aplicacao":
            body = f"{topic.summary} Relação operacional: {topic.formula}."
        elif family == "erros_comuns":
            body = f"Evite aplicar {topic.formula} fora das hipóteses, misturar unidades, perder sinais/vetores/fases, confundir aproximação com identidade ou ignorar limites do modelo."
        elif family == "limites":
            body = f"Teste {topic.formula} em regimes assintóticos e casos-limite; identifique quais termos dominam e não extrapole além do modelo em que foi derivada. {topic.summary}"
        elif family == "conexoes":
            body = f"{topic.summary} Compare com conservação, simetrias, escalas, análise dimensional, formulações equivalentes e áreas vizinhas. Fórmula-base: {topic.formula}."
        else:
            body = f"{topic.summary} Relação central: {topic.formula}."
        return f"{topic.title} — nível {topic.level}. {body} [Fonte técnica: {ref}; modo {style}/{context}]"