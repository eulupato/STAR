"""Catálogo operacional e fundação cognitiva da STAR MIND.

A camada legada de 15 capacidades permanece compatível com a STAR V1.9.
A fundação cognitiva adicional carrega a matriz WORLD (200 domínios) e a
arquitetura cognitiva contínua (85 domínios) a partir de dados canônicos.

Cada nó da fundação possui conteúdo canônico materializado e um espaço de
1.000.000.000 de views semânticas derivadas (9 eixos × 10 valores). As views
não são contadas como fatos independentes: fatos/claims exigem proveniência.
"""
from __future__ import annotations

from dataclasses import dataclass
import gzip
import json
from pathlib import Path
import re
import unicodedata


VARIANTS_PER_NODE = 1_000
NODES_PER_THEME = 1_000
CONTENTS_PER_THEME = 1_000_000
FOUNDATION_VIEWS_PER_NODE = 1_000_000_000

FAMILIES = (
    "fundamento", "procedimento", "exemplo_guiado", "diagnostico", "comparacao",
    "validacao", "falhas_e_limites", "fontes_e_evidencias", "integracao", "desafio",
)
STYLES = (
    "direto", "intuitivo", "didatico", "tecnico", "graduacao",
    "profissional", "pesquisa", "socratico", "checklist", "revisao",
)
CONTEXTS = (
    "definicao", "planejamento", "execucao", "caso_real", "quantitativo",
    "interdisciplinar", "seguranca", "performance", "fronteira", "checagem",
)
LENSES = (
    ("objetivo", "objetivo e critério de sucesso"),
    ("entradas", "entradas, pré-condições e contexto"),
    ("saidas", "saídas e artefatos esperados"),
    ("decomposicao", "decomposição em partes verificáveis"),
    ("dependencias", "dependências e ordem causal"),
    ("restricoes", "restrições duras e flexíveis"),
    ("hipoteses", "hipóteses explícitas"),
    ("alternativas", "alternativas e espaço de solução"),
    ("criterios", "critérios de decisão"),
    ("prioridade", "prioridade e saliência"),
    ("dados", "dados necessários"),
    ("proveniencia", "proveniência e rastreabilidade"),
    ("qualidade", "qualidade dos dados"),
    ("incerteza", "incerteza e confiança"),
    ("causalidade", "causalidade e mecanismos"),
    ("contradicoes", "contradições e inconsistências"),
    ("contraexemplos", "contraexemplos e casos-limite"),
    ("vieses", "vieses e confundidores"),
    ("medicao", "medição e operacionalização"),
    ("benchmark", "benchmark e referência"),
    ("validacao", "verificação e validação"),
    ("reprodutibilidade", "reprodutibilidade"),
    ("teste", "teste mínimo representativo"),
    ("regressao", "regressão e preservação do que funciona"),
    ("falhas", "modos de falha"),
    ("causa_raiz", "causa raiz"),
    ("recuperacao", "recuperação e rollback"),
    ("seguranca", "segurança e permissões"),
    ("privacidade", "privacidade e minimização de dados"),
    ("etica", "ética e impactos"),
    ("custo", "custo computacional e operacional"),
    ("latencia", "latência e responsividade"),
    ("memoria", "uso de memória e persistência"),
    ("cache", "cache e reutilização"),
    ("paralelismo", "paralelismo seguro"),
    ("observabilidade", "métricas e observabilidade"),
    ("interoperabilidade", "interoperabilidade e formatos"),
    ("portabilidade", "portabilidade"),
    ("versionamento", "versionamento e compatibilidade"),
    ("documentacao", "documentação e explicabilidade"),
    ("fontes", "fontes e referências"),
    ("atualizacao", "atualização e frescor"),
    ("deduplicacao", "deduplicação"),
    ("escalabilidade", "escalabilidade"),
    ("simulacao", "simulação antes da execução"),
    ("sensibilidade", "sensibilidade a parâmetros"),
    ("tradeoffs", "trade-offs"),
    ("integracao", "integração com o STAR Core"),
    ("fronteira", "fronteira e problemas abertos"),
    ("workflow", "workflow reproduzível"),
)


def _areas(raw: str) -> tuple[str, ...]:
    values = tuple(x.strip() for x in raw.split(";") if x.strip())
    if len(values) != 20:
        raise ValueError(f"cada tema precisa de 20 áreas; recebido {len(values)}")
    return values


THEMES = {
    "reasoning": {"prefix": "REASON", "label": "Raciocínio", "areas": _areas("interpretação de problemas;representação de estados;dedução;indução;abdução;raciocínio causal;raciocínio contrafactual;raciocínio probabilístico;raciocínio por restrições;raciocínio temporal;raciocínio espacial;raciocínio analógico;argumentação;detecção de inconsistências;geração de hipóteses;seleção de hipóteses;explicação;decisão sob incerteza;metacognição;verificação de conclusão")},
    "planning": {"prefix": "PLAN", "label": "Planejamento", "areas": _areas("definição de objetivos;decomposição hierárquica;grafo de tarefas;dependências;pré-condições;pós-condições;recursos;restrições;priorização;estimativa de esforço;sequenciamento;planejamento paralelo;planos condicionais;planos de contingência;replanejamento;critérios de parada;milestones;validação por etapa;gestão de risco;encerramento e retrospectiva")},
    "memory": {"prefix": "MEMCOG", "label": "Memória Cognitiva", "areas": _areas("working memory;memória episódica;memória semântica;memória de conversa;memória de projetos;memória de decisões;memória de erros;memória temporal;memória de pessoas;memória de objetos;preferências;eventos;consolidação;recuperação;associação;esquecimento controlado;importância;proveniência;conflitos de memória;retenção e arquivamento")},
    "knowledge_graph": {"prefix": "KGRAPH", "label": "Knowledge Graph", "areas": _areas("entidades;relações;tipos de entidade;tipos de relação;propriedades;identidade e aliases;normalização;proveniência;temporalidade;confiança;arestas ponderadas;vizinhança;caminhos;subgrafos;componentes;detecção de ciclos;inferência relacional;fusão de entidades;conflitos;exportação e interoperabilidade")},
    "scientific_reasoning": {"prefix": "SCIREAS", "label": "Raciocínio Científico", "areas": _areas("pergunta científica;hipótese;previsão;variáveis;controles;desenho experimental;amostragem;medição;instrumentação;incerteza;estatística;causalidade;falsificabilidade;replicação;reprodutibilidade;comparação de modelos;evidência convergente;revisão crítica;limitações;comunicação científica")},
    "mathematics": {"prefix": "MATHLAB", "label": "Laboratório Matemático", "areas": _areas("expressões simbólicas;equações;sistemas de equações;inequações;derivadas;integrais;limites;séries;álgebra linear;matrizes;autovalores;vetores;equações diferenciais;otimização;probabilidade;estatística;combinatória;teoria dos números;métodos numéricos;análise dimensional")},
    "simulation": {"prefix": "SIMLAB", "label": "Simulation Lab", "areas": _areas("modelo matemático;estado inicial;parâmetros;passo temporal;integração numérica;Monte Carlo;dinâmica discreta;decaimento e crescimento;movimento;oscilações;sistemas lineares;sensibilidade;varredura paramétrica;cenários;propagação de incerteza;estabilidade;convergência;calibração;validação com dados;relatório de simulação")},
    "coding": {"prefix": "CODELAB", "label": "Code Lab", "areas": _areas("especificação;design de API;algoritmos;estruturas de dados;implementação;tipagem;tratamento de erros;testes unitários;testes de integração;property testing;debugging;profiling;performance;segurança de código;sandbox;dependências;compatibilidade;refatoração;documentação;revisão de diff")},
    "verification": {"prefix": "VERIFY", "label": "Verificação e Confiança", "areas": _areas("afirmações;suporte de evidência;evidência contrária;qualidade de fonte;fonte primária;fonte secundária;consenso;controvérsia;recência;proveniência;corroboração;contradição;incerteza;calibração de confiança;fato versus hipótese;fato versus opinião;inferência;desinformação;checagem cruzada;relatório de confiança")},
    "document_rag": {"prefix": "RAGDOC", "label": "RAG Documental", "areas": _areas("ingestão;extração de texto;normalização;segmentação;overlap;metadados;hashing;deduplicação;indexação FTS5;BM25;consulta;reranking;recuperação;context window;citações;grounding;atualização incremental;remoção;coleções;avaliação de retrieval")},
    "research": {"prefix": "RESEARCH", "label": "Pesquisa", "areas": _areas("formulação de pergunta;estratégia de busca;palavras-chave;sinônimos;Crossref;DOI;metadados bibliográficos;autores;periódicos;datas;abstracts;referências;retrações;triagem de resultados;priorização de fontes;síntese;lacunas;atualização temporal;registro de fontes;relatório de pesquisa")},
    "projects": {"prefix": "PROJECT", "label": "Projetos", "areas": _areas("objetivo;escopo;requisitos;stakeholders;restrições;workstreams;tarefas;dependências;milestones;riscos;decisões;experimentos;artefatos;versões;status;bloqueios;retomada;histórico;conclusão;retrospectiva")},
    "user_model": {"prefix": "USERMOD", "label": "Modelo do Usuário", "areas": _areas("preferências declaradas;preferências observadas;nível de conhecimento;objetivos;projetos ativos;formato de resposta;idioma;unidades;ferramentas preferidas;restrições;permissões;hábitos de trabalho;feedback;correções do usuário;incerteza de perfil;proveniência;atualização;expiração;conflitos;privacidade")},
    "multi_agent": {"prefix": "MULTIAG", "label": "Multiagente", "areas": _areas("registro de agentes;capabilidades;seleção;roteamento;delegação;mensagens;contratos de entrada;contratos de saída;paralelismo;dependências;timeouts;falhas;retry;consenso;crítica;agregação;proveniência de resultado;permissões;observabilidade;encerramento")},
    "self_improvement": {"prefix": "SELFEVAL", "label": "Autoavaliação", "areas": _areas("métricas;baselines;benchmarks;testes de regressão;feedback do usuário;erros;falhas recorrentes;latência;uso de recursos;qualidade de resposta;precisão;recall;calibração;segurança;manutenibilidade;dívida técnica;duplicação;experimentos A/B;propostas de melhoria;validação pós-mudança")},
}
THEME_ORDER = tuple(THEMES)
TOTAL_CONTENTS = len(THEME_ORDER) * CONTENTS_PER_THEME


@dataclass(frozen=True)
class CognitiveNode:
    theme: str
    prefix: str
    label: str
    area_index: int
    lens_index: int
    area: str
    lens: str
    lens_label: str

    @property
    def node_index(self) -> int:
        return self.area_index * len(LENSES) + self.lens_index


class CognitiveFoundationCatalog:
    """Matriz canônica WORLD + cognição contínua, com 1B views por nó."""

    DATA_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "cognitive_foundation.json.gz"

    def __init__(self, data_path: str | Path | None = None):
        self.data_path = Path(data_path) if data_path else self.DATA_PATH
        with gzip.open(self.data_path, "rt", encoding="utf-8") as fh:
            self.data = json.load(fh)
        self.axes = self.data["axes"]
        self.axis_names = tuple(self.axes)
        if len(self.axis_names) != 9 or any(len(self.axes[name]) != 10 for name in self.axis_names):
            raise ValueError("fundação 1B exige exatamente 9 eixos com 10 valores cada")
        self._nodes = {}
        self._aliases = {}
        for group_name in ("world", "cognition"):
            for row in self.data[group_name]:
                node_id, number, title, key, kind, content, subtopics = row
                node = {"id": node_id, "number": number, "title": title, "canonical_key": key, "kind": kind, "canonical_content": content, "parent_id": None, "subtopics": [x[0] for x in subtopics]}
                self._register(node)
                for sid, label, skey in subtopics:
                    self._register({"id": sid, "number": number, "title": label, "canonical_key": skey, "kind": f"{kind}_subtopic", "canonical_content": "", "parent_id": node_id, "subtopics": []})

    @staticmethod
    def _norm(value: str) -> str:
        value = unicodedata.normalize("NFKD", str(value or ""))
        value = "".join(c for c in value if not unicodedata.combining(c))
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    def _register(self, node: dict):
        self._nodes[node["id"]] = node
        for alias in {node["canonical_key"], self._norm(node["title"])}:
            if alias:
                self._aliases.setdefault(alias, []).append(node["id"])

    def stats(self) -> dict:
        c = self.data["counts"]
        return {**c, "views_per_node": FOUNDATION_VIEWS_PER_NODE, "five_models": list(self.data["five_models"]), "quarantine_states": list(self.data["quarantine"]), "materialization": "on-demand-with-canonical-content", "consciousness_claim": False}

    def get_node(self, node_id: str) -> dict:
        try:
            return dict(self._nodes[str(node_id).upper()])
        except KeyError as exc:
            raise KeyError(f"nó da fundação não encontrado: {node_id}") from exc

    def resolve(self, text: str, *, scope: str | None = None) -> dict | None:
        query = self._norm(text)
        if not query:
            return None
        candidates = []
        for alias, ids in self._aliases.items():
            if query == alias or (len(alias) >= 4 and alias in query):
                for node_id in ids:
                    node = self._nodes[node_id]
                    if scope and not node["kind"].startswith(scope):
                        continue
                    score = 1000 if query == alias else len(alias)
                    candidates.append((score, -len(query.replace(alias, "")), node_id))
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return self.get_node(candidates[0][2])

    def _decode_view(self, view_index: int) -> dict:
        if not 1 <= int(view_index) <= FOUNDATION_VIEWS_PER_NODE:
            raise IndexError("view_index deve estar entre 1 e 1.000.000.000")
        digits = f"{int(view_index) - 1:09d}"
        return {axis: self.axes[axis][int(digit)] for axis, digit in zip(self.axis_names, digits)}

    def corrections_for(self, node_id: str) -> list[dict]:
        target = str(node_id).upper()
        parent = self._nodes.get(target, {}).get("parent_id")
        ids = {target}
        if parent:
            ids.add(parent)
        return [dict(item) for item in self.data.get("corrections", []) if ids.intersection(item.get("applies_to", []))]

    def materialize(self, node_id: str, view_index: int = 1) -> dict:
        node = self.get_node(node_id)
        parent = self._nodes.get(node.get("parent_id") or "")
        canonical = node["canonical_content"]
        if not canonical and parent:
            parent_context = parent["canonical_content"]
            if not parent_context:
                related = [self._nodes[sid]["title"] for sid in parent.get("subtopics", [])[:24]]
                parent_context = f"{parent['title']} é um domínio canônico da STAR. Subtemas relacionados: {', '.join(related)}."
            canonical = f"{node['title']} é um subtema canônico de {parent['title']}. Contexto do domínio:\n{parent_context}"
        elif not canonical:
            related = [self._nodes[sid]["title"] for sid in node.get("subtopics", [])[:24]]
            canonical = f"{node['title']} é um domínio canônico da fundação cognitiva da STAR. Subtemas relacionados: {', '.join(related)}."
        corrections = self.corrections_for(node["id"])
        axes = self._decode_view(view_index)
        return {"id": f"{node['id']}-{int(view_index):010d}", "node_id": node["id"], "kind": node["kind"], "title": node["title"], "parent_id": node.get("parent_id"), "canonical_content": canonical, "corrections": corrections, "view": axes, "epistemic_status": "project_canonical_seed", "requires_external_provenance_for_new_facts": True, "derived_view_is_independent_fact": False}


class CognitiveContentCatalog:
    def __init__(self):
        self.foundation = CognitiveFoundationCatalog()

    def stats(self) -> dict:
        return {"themes": len(THEME_ORDER), "areas_per_theme": 20, "lenses_per_area": len(LENSES), "canonical_nodes_per_theme": NODES_PER_THEME, "variants_per_node": VARIANTS_PER_NODE, "contents_per_theme": CONTENTS_PER_THEME, "total_content_variations": TOTAL_CONTENTS, "theme_keys": list(THEME_ORDER), "foundation": self.foundation.stats()}

    def get_node(self, theme: str, node_index: int) -> CognitiveNode:
        if theme not in THEMES or not 0 <= node_index < NODES_PER_THEME:
            raise IndexError("nó cognitivo inválido")
        area_i, lens_i = divmod(node_index, len(LENSES))
        lens, lens_label = LENSES[lens_i]
        spec = THEMES[theme]
        return CognitiveNode(theme, spec["prefix"], spec["label"], area_i, lens_i, spec["areas"][area_i], lens, lens_label)

    @staticmethod
    def content_id(theme: str, node_index: int, variant_index: int) -> str:
        if theme not in THEMES:
            raise KeyError(theme)
        if not 0 <= node_index < NODES_PER_THEME or not 0 <= variant_index < VARIANTS_PER_NODE:
            raise IndexError("índice fora do catálogo cognitivo")
        number = node_index * VARIANTS_PER_NODE + variant_index + 1
        return f"{THEMES[theme]['prefix']}-{number:07d}"

    @staticmethod
    def _theme_from_prefix(prefix: str) -> str | None:
        p = str(prefix or "").upper()
        for theme, spec in THEMES.items():
            if spec["prefix"] == p:
                return theme
        return None

    def get_variant(self, content_id: str) -> dict | None:
        m = re.fullmatch(r"([A-Z]+)-(\d{7})", str(content_id or "").upper())
        if not m:
            return None
        theme = self._theme_from_prefix(m.group(1))
        number = int(m.group(2))
        if theme is None or not 1 <= number <= CONTENTS_PER_THEME:
            return None
        node_i, local = divmod(number - 1, VARIANTS_PER_NODE)
        family_i, rest = divmod(local, 100)
        style_i, context_i = divmod(rest, 10)
        node = self.get_node(theme, node_i)
        family = FAMILIES[family_i]
        style = STYLES[style_i]
        context = CONTEXTS[context_i]
        return {"id": f"{node.prefix}-{number:07d}", "theme": theme, "theme_label": node.label, "area": node.area, "lens": node.lens, "lens_label": node.lens_label, "family": family, "style": style, "context": context, "prompt": f"No contexto de {node.label}, trabalhe '{node.area}' pela lente '{node.lens_label}'. Use família {family}, estilo {style} e contexto {context}. Declare entradas, suposições, evidências, verificações e limites; não invente fatos ausentes."}


assert len(THEME_ORDER) == 15
assert len(LENSES) == 50
assert all(len(spec["areas"]) == 20 for spec in THEMES.values())
assert NODES_PER_THEME == 20 * len(LENSES)
assert TOTAL_CONTENTS == 15_000_000
