"""Knowledge engine cultural da STAR: religiões, magia, folclore e esoterismo.

O engine materializa 5.000 nós canônicos (125 assuntos x 40 aspectos) e 1.000
perspectivas de estudo por nó = 5.000.000 conteúdos/visões endereçáveis.
Essas variações NÃO são cinco milhões de fatos pesquisados individualmente.
"""
from __future__ import annotations

from dataclasses import asdict
import re
import unicodedata

from core.religion_magic_taxonomy import ASPECTS, SUBJECTS, CulturalSubject


VARIATIONS_PER_NODE = 1_000
CANONICAL_NODES = len(SUBJECTS) * len(ASPECTS)
TOTAL_ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIATIONS_PER_NODE
RELIGION_SUBJECTS = sum(1 for item in SUBJECTS if item.family != "magic")
MAGIC_SUBJECTS = sum(1 for item in SUBJECTS if item.family == "magic")

LENSES = (
    "histórico", "comparativo", "autodescrição/praticantes", "antropológico", "sociológico",
    "textual", "material/arqueológico", "geográfico", "historiográfico/crítico", "contemporâneo",
)
DEPTHS = (
    "visão geral", "básico", "intermediário", "avançado", "acadêmico",
    "fontes primárias", "estado da pesquisa", "comparação", "estudo de caso", "revisão crítica",
)
FORMATS = (
    "explicação", "linha do tempo", "glossário", "tabela", "guia geográfico",
    "guia de fontes", "comparação", "perguntas de estudo", "matriz de evidências", "plano de pesquisa",
)

assert len(LENSES) * len(DEPTHS) * len(FORMATS) == VARIATIONS_PER_NODE
assert CANONICAL_NODES == 5_000
assert TOTAL_ADDRESSABLE_CONTENTS == 5_000_000

BASE_SOURCES = (
    "Database of Religious History (University of British Columbia)",
    "OpenAlex",
    "Crossref",
    "Library of Congress Religion Collections",
)

SOURCE_FAMILIES = {
    "christian": ("Harvard Pluralism Project", "Library of Congress", "OpenAlex/Crossref"),
    "jewish": ("Sefaria open textual library", "Harvard Pluralism Project", "Library of Congress"),
    "abrahamic": ("Harvard Pluralism Project", "Library of Congress", "OpenAlex/Crossref"),
    "islamic": ("Harvard Pluralism Project", "Library of Congress African and Middle Eastern collections", "OpenAlex/Crossref"),
    "west_asian": ("Database of Religious History", "Library of Congress", "OpenAlex/Crossref"),
    "iranian": ("Database of Religious History", "Library of Congress", "OpenAlex/Crossref"),
    "south_asian": ("Database of Religious History", "Harvard Pluralism Project", "Library of Congress Asian collections"),
    "buddhist": ("SuttaCentral structured Buddhist texts", "Database of Religious History", "Harvard Pluralism Project"),
    "himalayan": ("Database of Religious History", "Library of Congress Asian collections", "OpenAlex/Crossref"),
    "east_asian": ("Database of Religious History", "Harvard Pluralism Project", "Library of Congress Asian collections"),
    "southeast_asian": ("Database of Religious History", "UNESCO Intangible Cultural Heritage", "OpenAlex/Crossref"),
    "central_asian": ("Database of Religious History", "Smithsonian Anthropology", "OpenAlex/Crossref"),
    "ancient": ("Database of Religious History", "Smithsonian Anthropology", "museum/archaeological scholarship", "OpenAlex/Crossref"),
    "historical": ("Database of Religious History", "Library of Congress", "OpenAlex/Crossref"),
    "african": ("Smithsonian Anthropology", "UNESCO Intangible Cultural Heritage", "Library of Congress Folklife", "OpenAlex/Crossref"),
    "afro_diasporic": ("Library of Congress American Folklife Center", "Smithsonian Anthropology", "community scholarship", "OpenAlex/Crossref"),
    "indigenous": ("Smithsonian Anthropology", "UNESCO Intangible Cultural Heritage", "Library of Congress Folklife", "community-authored sources"),
    "indigenous_historical": ("Smithsonian Anthropology", "archaeological scholarship", "community-authored sources", "OpenAlex/Crossref"),
    "magic": ("Library of Congress Folklife and historical collections", "Smithsonian Anthropology", "Database of Religious History", "OpenAlex/Crossref"),
}


def _norm(text: str) -> str:
    value = str(text or "").lower().strip()
    value = "".join(ch for ch in unicodedata.normalize("NFD", value) if unicodedata.category(ch) != "Mn")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _tokens(text: str) -> set[str]:
    stop = {"a", "o", "e", "de", "da", "do", "das", "dos", "em", "para", "por", "com", "um", "uma", "the", "of", "and"}
    return {token for token in _norm(text).split() if len(token) > 1 and token not in stop}


def _decode_variation(variation_id: int) -> dict[str, str]:
    number = int(variation_id)
    if number < 1 or number > VARIATIONS_PER_NODE:
        raise ValueError(f"variation_id deve estar entre 1 e {VARIATIONS_PER_NODE}")
    value = number - 1
    value, fmt = divmod(value, 10)
    value, depth = divmod(value, 10)
    _, lens = divmod(value, 10)
    return {"lens": LENSES[lens], "depth": DEPTHS[depth], "format": FORMATS[fmt]}


def _sources(subject: CulturalSubject) -> tuple[str, ...]:
    specific = SOURCE_FAMILIES.get(subject.family, ())
    seen = []
    for source in (*specific, *BASE_SOURCES):
        if source not in seen:
            seen.append(source)
    return tuple(seen)


def _framing(subject: CulturalSubject) -> str:
    if subject.family == "magic":
        return (
            "Trate magia/esoterismo como história cultural, religião, prática, literatura e crença. "
            "Alegações de eficácia sobrenatural devem ser atribuídas à tradição ou ao relato, não apresentadas como mecanismo físico estabelecido."
        )
    return (
        "Separe autodescrição de praticantes, análise histórica/antropológica e evidência externa. "
        "Não presuma que uma escola, denominação ou comunidade represente toda a tradição."
    )


def _access_guidance(subject: CulturalSubject) -> str:
    if subject.access_policy == "restricted-community-knowledge":
        return (
            "Use somente informação pública e consensualmente compartilhada. Não reconstrua cerimônias fechadas, "
            "conhecimento iniciático, nomes/objetos restritos ou detalhes que comunidades tratem como privados."
        )
    if subject.access_policy == "community-sensitive":
        return "Priorize fontes da própria comunidade e evite generalizações, exotização ou reconstrução de práticas não públicas."
    return "Priorize fontes primárias públicas, autodescrição da comunidade e pesquisa acadêmica com proveniência."


class ReligionMagicKnowledgeEngine:
    def __init__(self):
        self.subjects = SUBJECTS
        self.aspects = ASPECTS
        self._subject_catalog = [
            (index, subject, _norm(subject.label), _tokens(subject.label) | set(subject.key.split("_")))
            for index, subject in enumerate(self.subjects, 1)
        ]
        self._aspect_catalog = [(index, label, _norm(label), _tokens(label)) for index, label in enumerate(self.aspects, 1)]

    def stats(self) -> dict:
        return {
            "status": "active-local-cultural",
            "subjects": len(self.subjects),
            "religion_subjects": RELIGION_SUBJECTS,
            "magic_esotericism_subjects": MAGIC_SUBJECTS,
            "aspects_per_subject": len(self.aspects),
            "canonical_nodes": CANONICAL_NODES,
            "variations_per_node": VARIATIONS_PER_NODE,
            "total_addressable_contents": TOTAL_ADDRESSABLE_CONTENTS,
            "materialization": "on-demand",
            "claims_supernatural_as_science": False,
            "restricted_knowledge_reconstruction": False,
        }

    def canonical_node(self, canonical_id: int) -> dict:
        node = int(canonical_id)
        if node < 1 or node > CANONICAL_NODES:
            raise ValueError(f"canonical_id deve estar entre 1 e {CANONICAL_NODES}")
        zero = node - 1
        subject_index, aspect_index = divmod(zero, len(self.aspects))
        subject = self.subjects[subject_index]
        return {
            "canonical_id": node,
            "subject_index": subject_index + 1,
            "subject": asdict(subject),
            "aspect_index": aspect_index + 1,
            "aspect": self.aspects[aspect_index],
            "sources": list(_sources(subject)),
            "framing": _framing(subject),
            "access_guidance": _access_guidance(subject),
        }

    def materialize(self, canonical_id: int, variation_id: int) -> dict:
        node = self.canonical_node(canonical_id)
        axes = _decode_variation(variation_id)
        subject = node["subject"]
        return {
            "id": f"RCM-{int(canonical_id):04d}-{int(variation_id):04d}",
            **node,
            **axes,
            "research_prompt": (
                f"Estude {node['aspect']} em {subject['label']} pela lente {axes['lens']}, "
                f"nível {axes['depth']} e formato {axes['format']}. Diferencie fontes internas à tradição, "
                "pesquisa acadêmica, registro histórico/etnográfico e alegações sem comprovação independente."
            ),
            "truthfulness_note": "visão de estudo endereçável; não equivale a um fato independente",
        }

    def resolve_subject(self, query: str) -> tuple[int, CulturalSubject, float] | None:
        normalized = _norm(query)
        query_tokens = _tokens(query)
        if not normalized:
            return None
        best = None
        best_score = 0.0
        for index, subject, label_norm, tokens in self._subject_catalog:
            if label_norm and label_norm in normalized:
                # Matches explícitos são fortes, mas consultas que contêm uma
                # tradição mais específica também podem conter o nome da tradição
                # pai (ex.: "budismo theravada"). Desempate por especificidade
                # lexical para que o assunto mais preciso vença.
                score = 1.0 if normalized == label_norm else 0.96
                specificity = (len(label_norm.split()), len(label_norm))
            else:
                specificity = (0, 0)
                overlap = len(query_tokens & tokens)
                score = overlap / max(1, len(tokens))
                # Evita resolver termos curtos/genéricos por coincidência fraca.
                if overlap == 1 and len(tokens) > 2:
                    score *= 0.65
            current_specificity = best[3] if best and len(best) > 3 else (-1, -1)
            if score > best_score or (score == best_score and specificity > current_specificity):
                best_score = score
                best = (index, subject, score, specificity)
        if not best or best_score < 0.45:
            return None
        index, subject, score, _specificity = best
        return index, subject, score

    def resolve_aspect(self, query: str) -> tuple[int, str, float]:
        query_tokens = _tokens(query)
        best = (1, self.aspects[0], 0.0)
        for index, label, _label_norm, tokens in self._aspect_catalog:
            overlap = len(query_tokens & tokens)
            score = overlap / max(1, len(tokens))
            if score > best[2]:
                best = (index, label, score)
        return best

    def answer(self, query: str) -> str | None:
        normalized = _norm(query)
        if normalized in {"religiao", "religioes", "religions", "religion"}:
            return (
                f"Minha base cultural organiza {RELIGION_SUBJECTS} tradições/relações religiosas e "
                f"{len(ASPECTS)} eixos de estudo, preservando diversidade interna e fontes de praticantes. "
                "Posso aprofundar uma tradição específica por história, textos, rituais, ética, demografia, política, arte e outros eixos."
            )
        if normalized in {"magia", "magic", "ocultismo", "esoterismo"}:
            return (
                f"Minha base de história da magia/esoterismo cobre {MAGIC_SUBJECTS} campos comparativos dentro de uma taxonomia cultural maior. "
                "Eu separo crença e relato tradicional de evidência científica e posso estudar períodos, regiões, textos, rituais, objetos, "
                "divinação, alquimia, astrologia, grimórios, bruxaria histórica e movimentos modernos sem tratar alegações sobrenaturais como fatos físicos."
            )
        resolved = self.resolve_subject(query)
        if resolved is None:
            return None
        subject_index, subject, score = resolved
        aspect_index, aspect, aspect_score = self.resolve_aspect(query)
        canonical_id = (subject_index - 1) * len(self.aspects) + aspect_index
        sources = ", ".join(_sources(subject)[:5])
        return (
            f"📚 {subject.label} — eixo: {aspect}. Região/escopo: {subject.region}. "
            f"Enquadramento: {_framing(subject)} {_access_guidance(subject)} "
            f"Fontes-base: {sources}. ID canônico: RCM-{canonical_id:04d}. "
            f"Confiança de resolução: {score:.2f}; aspecto: {aspect_score:.2f}."
        )

    def research_queries(self, query: str) -> list[str]:
        resolved = self.resolve_subject(query)
        if resolved is None:
            return []
        _, subject, _ = resolved
        _, aspect, _ = self.resolve_aspect(query)
        return [
            f'"{subject.label}" {aspect}',
            f'"{subject.label}" history anthropology religion',
            f'"{subject.label}" primary sources historiography',
        ]
