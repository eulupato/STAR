"""STAR Chemistry: 500 tópicos canônicos × 1.000 variações = 500.000 conteúdos."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import re
import unicodedata

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
    "IUPAC": "IUPAC Gold Book, 5th ed. (2025)",
    "OPENSTAX": "OpenStax Chemistry 2e",
    "NIST_WEBBOOK": "NIST Chemistry WebBook SRD 69 (data updated 2025)",
    "PUBCHEM": "NIH/NLM PubChem",
    "MIT_5111": "MIT OCW 5.111 Principles of Chemical Science",
    "MIT_560": "MIT OCW 5.60 Thermodynamics & Kinetics",
    "MIT_561": "MIT OCW 5.61 Physical Chemistry",
    "MIT_ORG": "MIT OCW 5.12 Organic Chemistry I",
    "MIT_ADV_ORG": "MIT OCW 5.43 Advanced Organic Chemistry",
    "MIT_INORG": "MIT OCW inorganic chemistry references",
    "MIT_EXPERIMENTAL": "MIT OCW 5.35 Experimental Chemistry",
    "NIST_CCCBDB": "NIST CCCBDB SRD 101",
    "LIBRE_ANALYTICAL": "Chemistry LibreTexts Analytical/Instrumental Chemistry",
    "IAEA": "IAEA radiochemistry/nuclear chemistry references",
}
FAMILIES = ("conceito", "formula", "variaveis_unidades", "hipoteses_validade", "derivacao", "calculo", "aplicacao", "erros_comuns", "limites", "conexoes")
STYLES = ("direto", "intuitivo", "didatico", "tecnico", "vestibular", "graduacao", "laboratorio", "engenharia", "pesquisa", "revisao")
CONTEXTS = ("definicao", "interpretacao", "simbolico", "dimensional", "experimental", "comparativo", "estimativa", "caso_limite", "aplicado", "checagem")
TOTAL_TOPICS = 500
TOTAL_DOMAINS = 20
TOPICS_PER_DOMAIN = 25
VARIANTS_PER_TOPIC = 1000
TOTAL_VARIANTS = 500000
_BLOCKS = (CHEMISTRY_ROWS_01, CHEMISTRY_ROWS_05, CHEMISTRY_ROWS_06, CHEMISTRY_ROWS_07, CHEMISTRY_ROWS_08, CHEMISTRY_ROWS_09, CHEMISTRY_ROWS_10, CHEMISTRY_ROWS_11, CHEMISTRY_ROWS_12, CHEMISTRY_ROWS_13, CHEMISTRY_ROWS_14, CHEMISTRY_ROWS_15, CHEMISTRY_ROWS_16, CHEMISTRY_ROWS_17, CHEMISTRY_ROWS_18, CHEMISTRY_ROWS_19, CHEMISTRY_ROWS_20)
_STOP = {"a","o","as","os","um","uma","de","da","do","das","dos","e","qual","quais","me","diga","explique","explica","sobre","formula","equacao","expressao","conceito","como","funciona","na","no","para","quimica","quimico","relacao","lei"}


def _norm(text):
    text = str(text or "").replace("-", " ").replace("–", " ").replace("—", " ")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower().replace("_", " ")
    return " ".join(re.sub(r"[^a-z0-9+ ]+", " ", text).split())


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


def _load_topics():
    out = []
    for block in _BLOCKS:
        for line in block.strip().splitlines():
            stripped = line.strip()
            if not stripped or stripped == "\\":
                continue
            parts = line.split("\t")
            if len(parts) != 8:
                raise ValueError(f"chemistry row inválida: {len(parts)} campos em {line[:80]!r}")
            tid, domain, level, title, formula, summary, aliases, source = parts
            if source not in SOURCES:
                raise ValueError(f"fonte de Química desconhecida: {source}")
            out.append(ChemistryTopic(tid, domain, int(level), title, formula, summary, tuple(a.strip() for a in aliases.split(";") if a.strip()), source))
    if len(out) != TOTAL_TOPICS:
        raise ValueError(f"Esperados 500 tópicos de Química; encontrados {len(out)}")
    if len({t.id for t in out}) != TOTAL_TOPICS:
        raise ValueError("IDs canônicos de Química devem ser únicos")
    counts = Counter(t.domain for t in out)
    if len(counts) != TOTAL_DOMAINS or set(counts.values()) != {TOPICS_PER_DOMAIN}:
        raise ValueError(f"Domínios de Química inválidos: {dict(counts)}")
    if set(t.level for t in out) != {1,2,3,4,5}:
        raise ValueError("Catálogo de Química deve cobrir níveis 1..5")
    return tuple(out)


TOPICS = _load_topics()


class ChemistryKnowledgeEngine:
    def __init__(self):
        self.topics = TOPICS
        self._search = []
        for t in self.topics:
            vals = (t.id, t.domain, t.title, *t.aliases)
            self._search.append(tuple(dict.fromkeys(_norm(v) for v in vals if v)))

    def stats(self):
        counts = Counter(t.domain for t in self.topics)
        return {"canonical_topics":500,"domains":20,"topics_per_domain":25,"variants_per_topic":1000,"content_variations":500000,"levels":[1,2,3,4,5],"families":10,"styles":10,"contexts":10,"domain_counts":dict(counts)}

    @staticmethod
    def content_id(topic_index, variant_index):
        if not 0 <= topic_index < 500 or not 0 <= variant_index < 1000:
            raise IndexError("índice fora do catálogo CHEM-000001..CHEM-500000")
        return f"CHEM-{topic_index*1000+variant_index+1:06d}"

    def get_variant(self, content_id):
        m = re.fullmatch(r"CHEM-(\d{6})", str(content_id or "").upper())
        if not m or not 1 <= int(m.group(1)) <= 500000:
            return None
        n = int(m.group(1)); topic_i, local = divmod(n-1, 1000); family_i, rest = divmod(local,100); style_i, context_i = divmod(rest,10)
        t = self.topics[topic_i]; family=FAMILIES[family_i]; style=STYLES[style_i]; context=CONTEXTS[context_i]
        return {"id":f"CHEM-{n:06d}","topic_id":t.id,"domain":t.domain,"level":t.level,"title":t.title,"family":family,"style":style,"context":context,"prompt":self._prompt(t,family,style,context),"answer":self._render(t,family,style,context),"source":SOURCES[t.source]}

    def match(self, query):
        q = _norm(query)
        if not q: return None
        qt = {x for x in q.split() if x not in _STOP} or set(q.split())
        best=None; best_score=0.0; best_spec=-1
        for topic, candidates in zip(self.topics, self._search):
            for candidate in candidates:
                ct = {x for x in candidate.split() if x not in _STOP} or set(candidate.split())
                if candidate == q: score=3.0
                elif len(candidate.split()) >= 2 and candidate in q: score=2.0+min(len(ct),10)/100
                else:
                    inter=len(qt & ct)
                    if not inter: continue
                    score=.72*(inter/max(1,len(ct)))+.28*(inter/max(1,len(qt)))
                    if ct <= qt: score += .12
                spec=len(ct)
                if score > best_score or (score == best_score and spec > best_spec): best,best_score,best_spec=topic,score,spec
        return best if best_score >= .58 else None

    def answer(self, query):
        t=self.match(query)
        if t is None: return None
        q=_norm(query)
        rules=(("formula",("formula","equacao","expressao","relacao matematica")),("calculo",("calcule","calculo","resolver","conta","passo a passo")),("variaveis_unidades",("unidade","unidades","variavel","simbolo","dimensao")),("hipoteses_validade",("hipotese","validade","vale quando","condicao","assuncao")),("derivacao",("deriv","demonstr","de onde vem")),("aplicacao",("aplic","serve para","uso","exemplo")),("erros_comuns",("erro","pegadinha","confus","cuidado")),("limites",("limite","aproxim","quando nao","falha")),("conexoes",("conecta","ligacao com","correlacion","relaciona com")))
        family="conceito"
        for fam, keys in rules:
            if any(k in q for k in keys): family=fam; break
        d=hashlib.sha256(q.encode()).digest()
        return self._render(t,family,STYLES[d[0]%10],CONTEXTS[d[1]%10])

    @staticmethod
    def _prompt(t,family,style,context):
        return f"{family}: {t.title} — estilo {style}, contexto {context}."

    @staticmethod
    def _render(t,family,style,context):
        if family=="formula": body=f"Relação-base: {t.formula}. {t.summary}"
        elif family=="variaveis_unidades": body=f"Use {t.formula}. Identifique símbolos, estados físicos, base de concentração/atividade, unidades e estado padrão quando aplicável; converta os dados antes do cálculo."
        elif family=="hipoteses_validade": body=f"Antes de usar {t.formula}, cheque idealidade, concentração/pressão, temperatura, estado padrão, equilíbrio versus cinética e aproximações. {t.summary}"
        elif family=="derivacao": body=f"Roteiro: declare espécies e hipóteses; aplique balanços de massa/carga/energia e a lei apropriada; derive simbolicamente; confira unidades, sinais, limites e conservação. Referência: {t.formula}."
        elif family=="calculo": body=f"Cálculo: parta de {t.formula}; liste dados/unidades; converta quantidade de matéria e concentrações; aplique estequiometria/balanços e, quando necessário, equilíbrio ou cinética; isole a incógnita; calcule; confira algarismos significativos e plausibilidade química."
        elif family=="aplicacao": body=f"{t.summary} Relação operacional: {t.formula}."
        elif family=="erros_comuns": body=f"Evite aplicar {t.formula} fora das hipóteses, confundir concentração com atividade, ignorar carga/estado físico, misturar unidades, confundir equilíbrio com velocidade ou arredondar cedo demais."
        elif family=="limites": body=f"Teste {t.formula} no regime relevante de composição, temperatura e pressão; identifique idealizações e não extrapole além do modelo. {t.summary}"
        elif family=="conexoes": body=f"{t.summary} Conecte com conservação, estrutura eletrônica, termodinâmica, cinética, equilíbrio, espectroscopia ou materiais conforme o caso. Relação-base: {t.formula}."
        else: body=f"{t.summary} Relação central: {t.formula}."
        return f"{t.title} — nível {t.level}. {body} [Fonte técnica: {SOURCES[t.source]}; modo {style}/{context}]"
