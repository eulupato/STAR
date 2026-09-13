"""Conhecimento multidisciplinar local da STAR: 13 × 500k = 6,5 milhões.

O catálogo é composicional e auditável: 25 macroáreas × 20 lentes = 500 nós
por matéria; cada nó possui 10 famílias × 10 estilos × 10 contextos = 1.000
variações. Os milhões de conteúdos não são materializados no startup.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
import unicodedata

from core.multidisciplinary_taxonomy import (
    CONTENTS_PER_SUBJECT,
    CROSS_DOMAIN_BRIDGES,
    DECODING_SAFETY_POLICY,
    HISTORY_EVIDENCE_POLICY,
    LENSES,
    NODES_PER_SUBJECT,
    PSYCHOLOGY_POLICY,
    SUBJECT_ORDER,
    SUBJECTS,
    TOTAL_CONTENTS,
    VARIANTS_PER_NODE,
)

FAMILIES = (
    "explicacao", "pergunta_resposta", "procedimento", "exemplo_guiado", "comparacao",
    "checagem", "erros_e_armadilhas", "fontes_e_evidencias", "conexoes", "desafio",
)
STYLES = (
    "direto", "intuitivo", "didatico", "tecnico", "escolar", "graduacao",
    "profissional", "pesquisa", "socratico", "revisao",
)
CONTEXTS = (
    "definicao", "interpretacao", "problema", "caso_real", "historico",
    "comparativo", "interdisciplinar", "aplicado", "fronteira", "checagem",
)

_STOP = {
    "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "e", "ou",
    "qual", "quais", "que", "me", "diga", "fale", "explique", "explica", "sobre", "como",
    "funciona", "funcionam", "na", "no", "nas", "nos", "para", "por", "favor", "tema",
    "assunto", "conceito", "materia", "matéria", "estude", "ensine", "ensina",
}

_LENS_HINTS = {
    "calculo": ("calcule", "calculo", "cálculo", "resolver", "resolva", "conta", "passo a passo"),
    "curiosidades": ("curiosidade", "curiosidades", "pouco conhecido", "pouco ensin", "detalhe escondido", "fato interessante"),
    "evidencias": ("evidencia", "evidência", "fonte", "fontes", "prova", "documento", "registro"),
    "controversias": ("controversia", "controvérsia", "debate", "disputa", "discordam", "consenso"),
    "comparacao": ("compare", "comparacao", "comparação", "diferenca", "diferença", "versus", " vs "),
    "limites": ("limite", "limitacao", "limitação", "incerteza", "quando falha", "hipotese", "hipótese"),
    "metodos": ("metodo", "método", "ferramenta", "tecnica", "técnica", "como pesquisar", "como medir"),
    "historia": ("historia de", "história de", "origem", "surgiu", "desenvolvimento historico", "desenvolvimento histórico"),
    "aplicacoes": ("aplicacao", "aplicação", "serve para", "uso", "usar na pratica", "usar na prática"),
    "avancado": ("avancado", "avançado", "nivel pesquisa", "nível pesquisa", "fronteira", "estado da arte"),
    "revisao": ("revisao", "revisão", "resumo", "quiz", "perguntas", "teste meu conhecimento"),
}

_FAMILY_HINTS = {
    "pergunta_resposta": ("pergunta", "quiz", "teste", "questionario", "questionário"),
    "procedimento": ("como fazer", "procedimento", "passo a passo", "resolva", "calcule"),
    "exemplo_guiado": ("exemplo", "caso", "mostre na pratica", "mostre na prática"),
    "comparacao": ("compare", "versus", " vs ", "diferenca", "diferença"),
    "checagem": ("verifique", "cheque", "confira", "validar", "valide"),
    "erros_e_armadilhas": ("erro", "erros", "pegadinha", "armadilha", "confusao", "confusão"),
    "fontes_e_evidencias": ("fonte", "fontes", "evidencia", "evidência", "referencia", "referência"),
    "conexoes": ("relacione", "conecte", "interdisciplin", "tem a ver com"),
    "desafio": ("desafio", "dificil", "difícil", "extremo", "olimpiada", "olimpíada"),
}

_HISTORY_HIDDEN_ANGLES = {
    "Pré-história e arqueologia": "vestígios de dieta, mobilidade, tecnologia lítica, sepultamentos e arqueologia experimental ajudam a reconstruir vidas sem textos escritos",
    "Mesopotâmia e Crescente Fértil": "tábuas administrativas registram rações, salários, dívidas, cerveja, trabalho e disputas locais, não apenas reis e guerras",
    "Egito antigo e nordeste africano": "papiros, ostraca e aldeias de trabalhadores preservam faltas ao trabalho, pagamentos, cartas e conflitos cotidianos",
    "Mediterrâneo antigo": "naufrágios, ânforas, moedas e inscrições revelam redes de comércio e mobilidade que textos literários não mostram sozinhos",
    "Grécia antiga": "inscrições, cerâmica e arqueologia permitem estudar estrangeiros, mulheres, escravizados e práticas locais além do cânone filosófico",
    "Roma e mundo romano": "grafites, tábuas de cera, diplomas militares, latrinas, ânforas e lixo arqueológico registram linguagem, consumo e circulação",
    "África pré-colonial": "arqueologia urbana, metalurgia, tradição oral e redes transaarianas contestam narrativas antigas de isolamento tecnológico ou comercial",
    "Sul e Sudeste Asiático históricos": "inscrições, portos, moedas e circulação religiosa mostram conexões marítimas densas entre sociedades muito distantes",
    "China e Leste Asiático históricos": "registros burocráticos, manuais técnicos, túmulos e objetos cotidianos complementam as grandes crônicas dinásticas",
    "Povos indígenas das Américas": "paisagens manejadas, agricultura, queimadas controladas, redes de troca e tradição oral mostram engenharia ambiental e política diversa",
    "Américas pré-colombianas": "estradas, terraços, chinampas, quipus, mercados e obras hidráulicas revelam infraestruturas sofisticadas sem modelos europeus",
    "Europa medieval": "contas domésticas, registros de tribunais, marginalia, pólen e ossos ajudam a estudar clima, dieta, trabalho e alfabetização cotidiana",
    "Mundo islâmico medieval": "manuscritos científicos, contratos, redes mercantis e instituições urbanas mostram circulação de conhecimento em várias línguas",
    "Impérios e rotas euro-asiáticas": "logística, estações de correio, animais de carga, moedas e intermediários locais foram tão decisivos quanto exércitos",
    "Renascimentos e reformas": "oficinas, impressores, tradutores, patronos e censores moldaram a circulação de ideias tanto quanto autores famosos",
    "Expansões marítimas e contatos": "pilotos, intérpretes, cartógrafos, marinheiros comuns e conhecimentos locais foram essenciais para navegação e conquista",
    "Colonização e escravidão atlântica": "registros de portos, anúncios, irmandades, quilombos, cartas e objetos revelam agência, resistência e redes familiares",
    "Revoluções dos séculos XVII-XIX": "preços do pão, boatos, panfletos, clubes, milícias e redes de correspondência ajudam a explicar mobilização política",
    "Industrialização e trabalho": "relógios, disciplina fabril, acidentes, habitação, trabalho infantil e associações operárias mostram o custo social da produtividade",
    "Imperialismos do século XIX": "levantamentos, mapas, ferrovias, medicina tropical e exposições foram instrumentos materiais de administração imperial",
    "Guerras mundiais": "logística, racionamento, manutenção, meteorologia, ferrovias, enfermagem e trabalho colonial sustentaram operações além das batalhas",
    "Guerra Fria e descolonização": "rádio, bolsas de estudo, assistência técnica, cultura popular e inteligência coexistiram com diplomacia e conflitos armados",
    "História do Brasil": "alianças indígenas, rotas internas, escravidão urbana, comunidades africanas, fronteiras e cultura material ampliam a narrativa além das capitais",
    "História da ciência e tecnologia": "instrumentos, técnicos, artesãos, tabelas, padrões e falhas experimentais fizeram parte das descobertas atribuídas a poucos nomes",
    "História social, cotidiana e material": "inventários, roupas, utensílios, alimentação, cartas, fotografias e espaços domésticos permitem reconstruir experiências comuns",
}


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).lower()
    value = value.replace("_", " ").replace("-", " ").replace("–", " ").replace("—", " ")
    value = re.sub(r"[^a-z0-9+#./ ]+", " ", value)
    return " ".join(value.split())


@dataclass(frozen=True)
class KnowledgeNode:
    subject: str
    prefix: str
    subject_label: str
    area_index: int
    lens_index: int
    area: str
    lens: str
    lens_label: str
    instruction: str
    source: str

    @property
    def node_index(self) -> int:
        return self.area_index * 20 + self.lens_index

    @property
    def title(self) -> str:
        return f"{self.area} — {self.lens_label}"


class MultidisciplinaryKnowledgeEngine:
    def __init__(self):
        self.subjects = SUBJECTS
        self._areas: list[tuple[str, int, str, tuple[str, ...]]] = []
        for subject in SUBJECT_ORDER:
            spec = SUBJECTS[subject]
            for area_index, area in enumerate(spec["areas"]):
                candidates = {_norm(area), _norm(subject), _norm(spec["label"]), *(_norm(a) for a in spec["aliases"])}
                self._areas.append((subject, area_index, area, tuple(sorted(x for x in candidates if x))))

    def stats(self) -> dict:
        return {
            "subjects": len(SUBJECT_ORDER),
            "subject_keys": list(SUBJECT_ORDER),
            "macro_areas_per_subject": 25,
            "lenses_per_area": 20,
            "canonical_nodes_per_subject": NODES_PER_SUBJECT,
            "canonical_nodes": len(SUBJECT_ORDER) * NODES_PER_SUBJECT,
            "variants_per_node": VARIANTS_PER_NODE,
            "contents_per_subject": CONTENTS_PER_SUBJECT,
            "total_content_variations": TOTAL_CONTENTS,
            "families": len(FAMILIES),
            "styles": len(STYLES),
            "contexts": len(CONTEXTS),
            "cross_domain_bridges": CROSS_DOMAIN_BRIDGES,
        }

    @staticmethod
    def _subject_from_prefix(prefix: str) -> str | None:
        prefix = str(prefix or "").upper()
        for key, spec in SUBJECTS.items():
            if spec["prefix"] == prefix:
                return key
        return None

    @staticmethod
    def content_id(subject: str, node_index: int, variant_index: int) -> str:
        if subject not in SUBJECTS:
            raise KeyError(subject)
        if not 0 <= node_index < NODES_PER_SUBJECT or not 0 <= variant_index < VARIANTS_PER_NODE:
            raise IndexError("índice fora do catálogo multidisciplinar")
        return f"{SUBJECTS[subject]['prefix']}-{node_index * VARIANTS_PER_NODE + variant_index + 1:06d}"

    def get_node(self, subject: str, node_index: int) -> KnowledgeNode:
        if subject not in SUBJECTS or not 0 <= node_index < NODES_PER_SUBJECT:
            raise IndexError("nó multidisciplinar inválido")
        spec = SUBJECTS[subject]
        area_i, lens_i = divmod(node_index, 20)
        lens, lens_label, instruction = LENSES[lens_i]
        return KnowledgeNode(
            subject=subject,
            prefix=spec["prefix"],
            subject_label=spec["label"],
            area_index=area_i,
            lens_index=lens_i,
            area=spec["areas"][area_i],
            lens=lens,
            lens_label=lens_label,
            instruction=instruction,
            source=spec["sources"][(area_i + lens_i) % len(spec["sources"])],
        )

    def get_variant(self, content_id: str) -> dict | None:
        m = re.fullmatch(r"([A-Z]+)-(\d{6})", str(content_id or "").upper())
        if not m:
            return None
        subject = self._subject_from_prefix(m.group(1))
        n = int(m.group(2))
        if subject is None or not 1 <= n <= CONTENTS_PER_SUBJECT:
            return None
        node_i, local = divmod(n - 1, VARIANTS_PER_NODE)
        family_i, rest = divmod(local, 100)
        style_i, context_i = divmod(rest, 10)
        node = self.get_node(subject, node_i)
        family, style, context = FAMILIES[family_i], STYLES[style_i], CONTEXTS[context_i]
        return {
            "id": f"{node.prefix}-{n:06d}",
            "subject": subject,
            "subject_label": node.subject_label,
            "area": node.area,
            "lens": node.lens,
            "lens_label": node.lens_label,
            "family": family,
            "style": style,
            "context": context,
            "prompt": self._prompt(node, family, style, context),
            "answer": self._render(node, family, style, context),
            "source": node.source,
            "bridges": CROSS_DOMAIN_BRIDGES.get(subject, ()),
        }

    @staticmethod
    def _explicit_subjects(q: str) -> set[str]:
        found = set()
        padded = f" {q} "
        for subject, spec in SUBJECTS.items():
            terms = (_norm(spec["label"]), *(_norm(a) for a in spec["aliases"]))
            if any(term and (q == term or f" {term} " in padded or (len(term.split()) >= 2 and term in q)) for term in terms):
                found.add(subject)
        return found

    def resolve(self, query: str) -> dict | None:
        q = _norm(query)
        if not q:
            return None
        qt = {t for t in q.split() if t not in _STOP} or set(q.split())
        explicit = self._explicit_subjects(q)
        ranked: list[tuple[float, int, str, int, str]] = []
        for subject, area_i, area, candidates in self._areas:
            best = 0.0
            specificity = 0
            area_norm = _norm(area)
            area_tokens = {t for t in area_norm.split() if t not in _STOP} or set(area_norm.split())
            if area_norm == q:
                best = 3.0
            elif len(area_tokens) >= 2 and area_norm in q:
                best = 2.15 + min(len(area_tokens), 10) / 100
            else:
                inter = len(qt & area_tokens)
                if inter:
                    coverage = inter / max(1, len(area_tokens))
                    precision = inter / max(1, len(qt))
                    best = 0.70 * coverage + 0.30 * precision
                    if area_tokens <= qt:
                        best += 0.12
            if subject in explicit:
                best += 0.85
            elif explicit:
                best -= 0.20
            specificity = len(area_tokens)
            if best > 0:
                ranked.append((best, specificity, subject, area_i, area))
        if not ranked:
            return None
        ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
        top = ranked[0]
        if top[0] < 0.58:
            return None
        competitors = [r for r in ranked[1:] if r[2] != top[2] and r[0] >= max(0.58, top[0] - 0.07)]
        ambiguous = not explicit and bool(competitors)
        lens_i = self._select_lens(q)
        node_i = top[3] * 20 + lens_i
        return {
            "subject": top[2], "subject_label": SUBJECTS[top[2]]["label"], "area": top[4],
            "area_index": top[3], "lens_index": lens_i, "node_index": node_i,
            "score": top[0], "explicit_subject": top[2] in explicit, "ambiguous": ambiguous,
            "alternatives": tuple(dict.fromkeys(SUBJECTS[r[2]]["label"] for r in competitors[:3])),
        }

    @staticmethod
    def _select_lens(q: str) -> int:
        for lens, hints in _LENS_HINTS.items():
            if any(_norm(h) in q for h in hints):
                return next(i for i, item in enumerate(LENSES) if item[0] == lens)
        return 0

    @staticmethod
    def _select_family(q: str) -> str:
        for family, hints in _FAMILY_HINTS.items():
            if any(_norm(h) in q for h in hints):
                return family
        return "explicacao"

    def answer(self, query: str) -> str | None:
        resolution = self.resolve(query)
        if resolution is None:
            return None
        if resolution["ambiguous"]:
            alts = ", ".join((resolution["subject_label"], *resolution["alternatives"]))
            return f"Esse termo cruza mais de uma matéria ({alts}). Diga a área ou acrescente contexto para eu não misturar domínios."
        node = self.get_node(resolution["subject"], resolution["node_index"])
        q = _norm(query)
        family = self._select_family(q)
        digest = hashlib.sha256(q.encode()).digest()
        return self._render(node, family, STYLES[digest[0] % 10], CONTEXTS[digest[1] % 10])

    @staticmethod
    def _prompt(node: KnowledgeNode, family: str, style: str, context: str) -> str:
        return (
            f"{node.subject_label}: {node.area}. Aborde {node.lens_label}; {node.instruction}. "
            f"Formato {family}, estilo {style}, contexto {context}."
        )

    @staticmethod
    def _render(node: KnowledgeNode, family: str, style: str, context: str) -> str:
        spec = SUBJECTS[node.subject]
        bridges = ", ".join(CROSS_DOMAIN_BRIDGES.get(node.subject, ())) or "nenhuma"
        base = (
            f"{node.subject_label} — {node.area} — {node.lens_label}. "
            f"Eixo: {spec['focus']}. Objetivo desta lente: {node.instruction}."
        )
        if family == "pergunta_resposta":
            body = "Organize a resposta como pergunta central, resposta curta, explicação e duas checagens de compreensão."
        elif family == "procedimento":
            body = "Declare dados e objetivo; escolha método; execute etapas; verifique hipóteses, unidades/evidências e resultado."
        elif family == "exemplo_guiado":
            body = "Use um exemplo representativo e caminhe do contexto à interpretação, explicitando o que o exemplo prova e o que não prova."
        elif family == "comparacao":
            body = "Compare por definição, mecanismo/estrutura, evidência, aplicação e limite; preserve fronteiras entre matérias."
        elif family == "checagem":
            body = "Cheque consistência interna, definições, fontes, pressupostos e possíveis interpretações alternativas."
        elif family == "erros_e_armadilhas":
            body = "Destaque equívocos frequentes, generalizações indevidas, confusão de correlação/causalidade e extrapolações fora do domínio."
        elif family == "fontes_e_evidencias":
            body = "Diferencie fonte primária/secundária quando aplicável, evidência observacional/experimental e nível de confiança."
        elif family == "conexoes":
            body = f"Conecte somente quando útil aos domínios-ponte: {bridges}; diga qual parte pertence a cada área."
        elif family == "desafio":
            body = "Eleve a dificuldade, exija justificativa e inclua um caso-limite, contraexemplo ou questão de fronteira."
        else:
            body = "Explique do essencial ao avançado, defina termos e termine com uma síntese verificável."

        special = ""
        if node.subject == "history":
            special = " " + HISTORY_EVIDENCE_POLICY
            if node.lens == "curiosidades":
                special += " Ângulo micro-histórico: " + _HISTORY_HIDDEN_ANGLES.get(node.area, "use cultura material, arquivos e experiências de grupos pouco representados") + "."
        elif node.subject == "decoding":
            special = " " + DECODING_SAFETY_POLICY
        elif node.subject == "psychology_sociology":
            special = " " + PSYCHOLOGY_POLICY
        return f"{base} {body}{special} [Fonte-base: {node.source}; modo {style}/{context}]"
