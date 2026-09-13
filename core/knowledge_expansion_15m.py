"""STAR Knowledge PLUS: +1M de conteúdos por cada uma das 15 bases de conhecimento.

A expansão é aditiva e não altera IDs legados. Cada domínio recebe 1.000 novos
nós canônicos e cada nó gera 1.000 variações determinísticas (10 famílias ×
10 estilos × 10 contextos). Total: 15.000.000 novas unidades endereçáveis.

Multidisciplinar: 25 macroáreas existentes × 40 novas lentes = 1.000 nós.
Física/Química: 50 eixos avançados × 20 lentes de pesquisa = 1.000 nós.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from core.multidisciplinary_taxonomy import SUBJECT_ORDER, SUBJECTS

VARIANTS_PER_NODE = 1000
PLUS_NODES_PER_DOMAIN = 1000
PLUS_CONTENTS_PER_DOMAIN = 1_000_000

FAMILIES = (
    "explicacao_profunda", "problema_resolvido", "derivacao_ou_argumento", "interpretacao_de_dados",
    "analise_de_fontes", "comparacao", "validacao", "falhas_e_limites", "conexoes", "pergunta_de_pesquisa",
)
STYLES = (
    "direto", "intuitivo", "didatico", "tecnico", "graduacao", "pos_graduacao",
    "profissional", "pesquisa", "socratico", "revisao",
)
CONTEXTS = (
    "fundamentos", "quantitativo", "experimental", "historico", "caso_real",
    "comparativo", "interdisciplinar", "aplicado", "fronteira", "checagem",
)

RESEARCH_LENSES = (
    ("derivacao", "derivação rigorosa", "derive relações, deixe hipóteses explícitas e cheque consistência"),
    ("dimensional", "análise dimensional e escalas", "identifique escalas, unidades, números adimensionais e regimes"),
    ("numerico", "métodos numéricos", "explique discretização, convergência, estabilidade e custo computacional"),
    ("medicao", "medição e instrumentação", "descreva observáveis, sensores, resolução e limitações instrumentais"),
    ("incerteza", "incerteza e propagação de erro", "quantifique fontes de incerteza e como elas se propagam"),
    ("calibracao", "calibração e rastreabilidade", "mostre referência, calibração, rastreabilidade e controle metrológico"),
    ("dados", "dados de referência", "indique quais dados, constantes, tabelas ou bancos são relevantes e como avaliar qualidade"),
    ("assintotico", "aproximações e limites assintóticos", "compare regimes limite e quando aproximações deixam de funcionar"),
    ("contorno", "condições iniciais e de contorno", "mostre como condições iniciais/de contorno mudam soluções e interpretação"),
    ("sensibilidade", "sensibilidade a parâmetros", "discuta parâmetros dominantes, sensibilidade e identificabilidade"),
    ("inverso", "problemas inversos", "explique inferência de parâmetros a partir de observações e regularização"),
    ("simulacao", "simulação", "estruture modelo, algoritmo, validação e comparação com dados"),
    ("validacao", "verificação e validação", "separe erro de implementação, erro numérico, adequação do modelo e validação empírica"),
    ("benchmark", "benchmarks e resultados de referência", "compare contra casos analíticos, dados certificados ou experimentos de referência"),
    ("falhas", "modos de falha", "mostre singularidades, instabilidades, degenerescências e interpretações erradas comuns"),
    ("experimento", "experimentos históricos decisivos", "conecte teoria a experimentos que mudaram ou restringiram o modelo"),
    ("aplicacao", "aplicação científica e tecnológica", "ligue o conceito a instrumentos, engenharia, indústria ou pesquisa real"),
    ("fronteira", "fronteira de pesquisa", "separe consenso, questões abertas, resultados recentes e limites de evidência"),
    ("interdisciplinar", "conexões entre áreas", "mostre dependências e pontes sem duplicar o domínio vizinho"),
    ("desafio", "problema avançado", "formule um problema difícil, estratégia de resolução e verificações finais"),
)

MULTI_PLUS_LENSES = (
    ("fontes_primarias", "fontes primárias e evidência direta", "priorize documentos, medições, artefatos, registros ou dados primários"),
    ("datasets", "datasets e bases de dados", "aponte tipos de dataset, metadados, cobertura, resolução e limitações"),
    ("padroes", "padrões e terminologia", "organize normas, convenções, taxonomias e vocabulário técnico relevante"),
    ("medicao", "medição e operacionalização", "explique como conceitos abstratos viram variáveis observáveis e mensuráveis"),
    ("incerteza", "incerteza e margem de erro", "separe variabilidade, erro de medição, incerteza de modelo e inferência"),
    ("causalidade", "causalidade e mecanismos", "diferencie associação, mecanismo, causalidade e explicações concorrentes"),
    ("casos_comparados", "casos comparados", "compare casos mantendo contexto, escala, período e critérios equivalentes"),
    ("variacao_contextual", "variação regional, cultural ou contextual", "mostre como contexto altera padrões e interpretação"),
    ("cronologia_fina", "cronologia fina e sequência", "organize precedentes, transições, dependências temporais e consequências"),
    ("escalas", "escalas e níveis de análise", "compare micro, meso, macro e mudanças de escala"),
    ("fronteiras_sistema", "fronteiras do sistema", "declare o que está dentro/fora do modelo e efeitos dessa escolha"),
    ("classificacao", "classificações concorrentes", "compare taxonomias e critérios de classificação sem tratá-los como naturais"),
    ("indicadores", "indicadores quantitativos", "explique métricas, denominadores, normalização e leitura correta"),
    ("visualizacao", "visualização e representação", "discuta mapas, gráficos, diagramas, tabelas e vieses de representação"),
    ("simulacao", "simulação e cenários", "explique premissas, parâmetros, validação e limites de cenários"),
    ("computacao", "métodos computacionais", "mostre como algoritmos, software ou automação apoiam a área"),
    ("algoritmos", "algoritmos e procedimentos", "decomponha o processo em passos, entradas, saídas e critérios de parada"),
    ("campo", "trabalho de campo", "trate amostragem, protocolo, registro, contexto e segurança"),
    ("laboratorio_arquivo", "laboratório, arquivo ou coleção", "explique preparação, proveniência, preservação, catalogação ou cadeia de custódia"),
    ("benchmark", "benchmarks e referências", "compare resultados contra padrões, corpus, casos-base ou séries históricas"),
    ("validacao", "validação", "mostre como testar afirmações, modelos, instrumentos ou classificações"),
    ("reprodutibilidade", "reprodutibilidade e replicação", "separe repetição, replicação, documentação e independência de evidência"),
    ("vieses", "vieses e confundidores", "identifique seleção, medição, sobrevivência, disponibilidade e variáveis confundidoras"),
    ("etica", "ética e impactos", "avalie consentimento, justiça, representação, riscos e consequências"),
    ("seguranca", "segurança e uso responsável", "discuta ameaças, controles, limites operacionais e uso seguro"),
    ("politicas", "políticas e instituições", "relacione regras, incentivos, governança, capacidade institucional e resultados"),
    ("tradeoffs", "trade-offs de projeto ou decisão", "compare ganhos, custos, riscos e objetivos incompatíveis"),
    ("otimizacao", "otimização", "defina objetivo, restrições, métricas e efeitos colaterais"),
    ("falhas", "análise de falhas", "estude causas-raiz, cascatas, sinais precursores e mitigação"),
    ("casos_limite", "casos-limite e exceções", "teste definições e modelos em situações extremas ou ambíguas"),
    ("contraexemplos", "contraexemplos", "use contraexemplos para delimitar regras e evitar generalizações excessivas"),
    ("mitos", "mitos e simplificações", "corrija versões populares que apagam contexto, condições ou evidências"),
    ("historiografia", "mudanças de interpretação", "mostre como escolas, fontes e métodos alteraram interpretações ao longo do tempo"),
    ("cenarios", "cenários futuros", "separe projeção, previsão, especulação e condições necessárias"),
    ("problemas_abertos", "problemas abertos", "liste questões não resolvidas e por que continuam difíceis"),
    ("perguntas_pesquisa", "perguntas de pesquisa", "transforme lacunas em perguntas testáveis ou investigáveis"),
    ("qualidade_dados", "qualidade e proveniência dos dados", "avalie origem, atualização, completude, resolução e transformações"),
    ("interoperabilidade", "interoperabilidade", "explique compatibilidade entre formatos, sistemas, conceitos e classificações"),
    ("workflow", "workflow prático", "organize um fluxo reproduzível com entradas, etapas, verificações e saída"),
    ("decisao", "estrutura de decisão", "organize critérios, evidências, incertezas e alternativas sem substituir julgamento especializado"),
)

PHYSICS_AREAS = tuple(x.strip() for x in """
Analytical mechanics and variational principles;Hamiltonian mechanics;Canonical transformations;Hamilton-Jacobi theory;Nonlinear dynamics and deterministic chaos;Continuum mechanics;Elasticity and constitutive models;Turbulence;Boundary-layer theory;Acoustics and wave propagation;Nonlinear waves and solitons;Statistical ensembles;Critical phenomena and renormalization group;Stochastic processes in physics;Transport phenomena;Non-equilibrium statistical mechanics;Plasma physics;Magnetohydrodynamics;Radiation from accelerated charges;Waveguides and resonant cavities;Antennas and electromagnetic radiation;Photonics;Nonlinear optics;Quantum information and entanglement;Open quantum systems;Quantum many-body physics;Quantum field theory;Gauge theories;Quantum electrodynamics;Quantum chromodynamics;Standard Model phenomenology;Neutrino physics;Nuclear structure;Nuclear reactions;Particle detectors;Accelerator physics;Electronic band structure;Superconductivity;Topological phases of matter;Magnetism and spintronics;Semiconductor physics;Nanoscale and mesoscopic physics;Differential geometry for relativity;Black-hole physics;Physical cosmology;Gravitational-wave physics;Astrophysical fluids and plasmas;Stellar structure and evolution;Exoplanet physics and atmospheres;Metrology, constants and computational physics
""".split(";") if x.strip())

CHEMISTRY_AREAS = tuple(x.strip() for x in """
Post-Hartree-Fock electronic structure;Density functional theory in chemistry;Multireference and excited-state methods;High-resolution molecular spectroscopy;Statistical thermodynamics of molecules;Non-equilibrium chemical thermodynamics;Activity-coefficient models;Electrolyte solution theories;Multicomponent phase equilibria;Interfacial chemistry;Surface science;Electrochemical kinetics;Battery chemistry;Fuel-cell chemistry;Corrosion science;Homogeneous catalysis;Heterogeneous catalysis;Organometallic reaction mechanisms;Photochemistry;Photoredox chemistry;Physical organic chemistry;Pericyclic reactions;Stereoelectronic effects;Asymmetric synthesis;Retrosynthetic analysis;C-H activation and functionalization;Polymerization kinetics;Polymer physics and rheology;Supramolecular chemistry;Host-guest chemistry;Crystal engineering;Solid-state chemistry;Functional materials chemistry;Nanochemistry;Colloid and interface science;Analytical method validation;Advanced chromatography;High-resolution mass spectrometry;Advanced NMR spectroscopy;X-ray and neutron structural methods;Bioinorganic chemistry;Chemical biology;Enzyme chemistry;Metabolomics and chemical profiling;Environmental chemistry;Atmospheric chemistry;Nuclear and radiochemistry;Process chemistry and scale-up;Green and sustainable chemistry;Cheminformatics and machine learning for chemistry
""".split(";") if x.strip())

DOMAIN_ORDER = ("physics", "chemistry", *SUBJECT_ORDER)
PREFIXES = {"physics": "PHYSX", "chemistry": "CHEMX", **{k: f"{SUBJECTS[k]['prefix']}X" for k in SUBJECT_ORDER}}
LABELS = {"physics": "Física", "chemistry": "Química", **{k: SUBJECTS[k]["label"] for k in SUBJECT_ORDER}}
EXISTING_CONTENTS = {"physics": 150_000, "chemistry": 500_000, **{k: 500_000 for k in SUBJECT_ORDER}}
SOURCE_FAMILIES = {
    "physics": ("NIST Standard Reference Data", "CODATA", "MIT OpenCourseWare", "NASA Science Data", "CERN/PDG/LIGO references"),
    "chemistry": ("NIST Standard Reference Data", "IUPAC", "NIST Chemistry WebBook", "PubChem/NCBI", "MIT OpenCourseWare"),
    **{k: SUBJECTS[k]["sources"] for k in SUBJECT_ORDER},
}
ALIASES = {
    "physics": ("fisica", "physics", "quantic", "quantica", "relatividade", "cosmologia", "particulas", "eletromagnetismo"),
    "chemistry": ("quimica", "chemistry", "molecular", "molecula", "catalise", "eletroquimica", "organica", "inorganica"),
    **{k: SUBJECTS[k]["aliases"] for k in SUBJECT_ORDER},
}

PLUS_TOTAL = len(DOMAIN_ORDER) * PLUS_CONTENTS_PER_DOMAIN
COMBINED_KNOWLEDGE_TOTAL = sum(EXISTING_CONTENTS.values()) + PLUS_TOTAL

_DEPTH_HINTS = (
    "aprofund", "avanc", "nivel pesquisa", "nível pesquisa", "pos gradu", "pós gradu", "benchmark", "dataset",
    "incerteza", "validacao", "validação", "reprodut", "simulacao", "simulação", "fonte primaria", "fonte primária",
    "estado da arte", "fronteira", "problema aberto", "plus", "extremo", "rigoroso", "derivacao", "derivação",
)

_LENS_HINTS = {
    "incerteza": ("incerteza", "erro", "margem"), "dados": ("dataset", "dados", "tabela", "constante"),
    "simulacao": ("simulacao", "simulação", "simule"), "validacao": ("validacao", "validação", "verifique"),
    "benchmark": ("benchmark", "referencia", "referência"), "fronteira": ("fronteira", "estado da arte", "aberto"),
    "problemas_abertos": ("problema aberto", "questao aberta", "questão aberta"), "fontes_primarias": ("fonte primaria", "fonte primária", "documento original"),
    "vieses": ("vies", "viés", "confundidor"), "workflow": ("workflow", "passo a passo", "procedimento"),
    "etica": ("etica", "ética"), "seguranca": ("seguranca", "segurança"), "interoperabilidade": ("interoperabilidade", "compatibilidade"),
}


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).lower()
    value = value.replace("_", " ").replace("-", " ").replace("–", " ").replace("—", " ")
    value = re.sub(r"[^a-z0-9+#./ ]+", " ", value)
    return " ".join(value.split())


def _tokens(text: str) -> set[str]:
    stop = {"de", "da", "do", "das", "dos", "e", "em", "a", "o", "as", "os", "the", "and", "of", "in"}
    return {t for t in _norm(text).split() if len(t) > 2 and t not in stop}


@dataclass(frozen=True)
class PlusNode:
    domain: str
    label: str
    prefix: str
    area_index: int
    lens_index: int
    area: str
    lens: str
    lens_label: str
    instruction: str
    source: str

    @property
    def node_index(self) -> int:
        multiplier = 20 if self.domain in {"physics", "chemistry"} else 40
        return self.area_index * multiplier + self.lens_index


class KnowledgeExpansion15MEngine:
    def __init__(self):
        self._catalog: list[tuple[str, int, str, set[str]]] = []
        for domain in DOMAIN_ORDER:
            areas = self._areas(domain)
            for i, area in enumerate(areas):
                self._catalog.append((domain, i, area, _tokens(area)))

    @staticmethod
    def _areas(domain: str) -> tuple[str, ...]:
        if domain == "physics":
            return PHYSICS_AREAS
        if domain == "chemistry":
            return CHEMISTRY_AREAS
        return SUBJECTS[domain]["areas"]

    @staticmethod
    def _lenses(domain: str):
        return RESEARCH_LENSES if domain in {"physics", "chemistry"} else MULTI_PLUS_LENSES

    def stats(self) -> dict:
        combined = {d: EXISTING_CONTENTS[d] + PLUS_CONTENTS_PER_DOMAIN for d in DOMAIN_ORDER}
        return {
            "domains": len(DOMAIN_ORDER),
            "domain_keys": list(DOMAIN_ORDER),
            "added_canonical_nodes_per_domain": PLUS_NODES_PER_DOMAIN,
            "added_content_variations_per_domain": PLUS_CONTENTS_PER_DOMAIN,
            "added_content_variations": PLUS_TOTAL,
            "variants_per_node": VARIANTS_PER_NODE,
            "existing_content_variations": sum(EXISTING_CONTENTS.values()),
            "combined_content_variations": COMBINED_KNOWLEDGE_TOTAL,
            "combined_by_domain": combined,
            "prefixes": dict(PREFIXES),
        }

    @staticmethod
    def prefers(text: str) -> bool:
        q = _norm(text)
        return any(_norm(h) in q for h in _DEPTH_HINTS)

    def content_id(self, domain: str, node_index: int, variant_index: int) -> str:
        if domain not in DOMAIN_ORDER:
            raise KeyError(domain)
        if not 0 <= node_index < PLUS_NODES_PER_DOMAIN or not 0 <= variant_index < VARIANTS_PER_NODE:
            raise IndexError("índice fora do catálogo PLUS")
        n = node_index * VARIANTS_PER_NODE + variant_index + 1
        return f"{PREFIXES[domain]}-{n:07d}"

    def get_node(self, domain: str, node_index: int) -> PlusNode:
        if domain not in DOMAIN_ORDER or not 0 <= node_index < PLUS_NODES_PER_DOMAIN:
            raise IndexError("nó PLUS inválido")
        lenses = self._lenses(domain)
        area_count = 50 if domain in {"physics", "chemistry"} else 25
        lens_count = 20 if domain in {"physics", "chemistry"} else 40
        if area_count * lens_count != PLUS_NODES_PER_DOMAIN:
            raise RuntimeError("taxonomia PLUS inconsistente")
        area_i, lens_i = divmod(node_index, lens_count)
        lens, lens_label, instruction = lenses[lens_i]
        sources = SOURCE_FAMILIES[domain]
        return PlusNode(
            domain=domain, label=LABELS[domain], prefix=PREFIXES[domain], area_index=area_i, lens_index=lens_i,
            area=self._areas(domain)[area_i], lens=lens, lens_label=lens_label, instruction=instruction,
            source=sources[(area_i + lens_i) % len(sources)],
        )

    def get_variant(self, content_id: str) -> dict | None:
        m = re.fullmatch(r"([A-Z]+X)-(\d{7})", str(content_id or "").upper())
        if not m:
            return None
        domain = next((d for d, p in PREFIXES.items() if p == m.group(1)), None)
        n = int(m.group(2))
        if domain is None or not 1 <= n <= PLUS_CONTENTS_PER_DOMAIN:
            return None
        node_i, local = divmod(n - 1, VARIANTS_PER_NODE)
        family_i, rest = divmod(local, 100)
        style_i, context_i = divmod(rest, 10)
        node = self.get_node(domain, node_i)
        family, style, context = FAMILIES[family_i], STYLES[style_i], CONTEXTS[context_i]
        return {
            "id": f"{node.prefix}-{n:07d}", "domain": domain, "domain_label": node.label,
            "area": node.area, "lens": node.lens, "lens_label": node.lens_label,
            "family": family, "style": style, "context": context, "source": node.source,
            "prompt": self._prompt(node, family, style, context),
            "answer": self._render(node, family, style, context),
        }

    def _explicit_domains(self, q: str) -> set[str]:
        found = set()
        padded = f" {q} "
        for domain in DOMAIN_ORDER:
            terms = (_norm(LABELS[domain]), *(_norm(a) for a in ALIASES[domain]))
            if any(t and (q == t or f" {t} " in padded) for t in terms):
                found.add(domain)
        return found

    def resolve(self, text: str) -> dict | None:
        q = _norm(text)
        if not q:
            return None
        q_tokens = _tokens(q)
        explicit = self._explicit_domains(q)
        best = None
        for domain, area_i, area, area_tokens in self._catalog:
            if explicit and domain not in explicit:
                continue
            phrase = _norm(area)
            overlap = len(q_tokens & area_tokens) / max(1, len(area_tokens))
            score = overlap
            if phrase and phrase in q:
                score += 1.2
            if domain in explicit:
                score += 0.75
            if len(q_tokens & area_tokens) >= 2:
                score += 0.25
            candidate = (score, len(area_tokens), domain, area_i, area)
            if best is None or candidate > best:
                best = candidate
        if best is None or best[0] < (0.62 if explicit else 0.72):
            return None
        _, _, domain, area_i, area = best
        lenses = self._lenses(domain)
        lens_i = 0
        for wanted, hints in _LENS_HINTS.items():
            if any(_norm(h) in q for h in hints):
                match_i = next((i for i, item in enumerate(lenses) if item[0] == wanted), None)
                if match_i is not None:
                    lens_i = match_i
                    break
        lens_count = len(lenses)
        node_i = area_i * lens_count + lens_i
        return {"domain": domain, "area": area, "node_index": node_i, "score": best[0]}

    def answer(self, text: str) -> str | None:
        resolved = self.resolve(text)
        if resolved is None:
            return None
        node = self.get_node(resolved["domain"], resolved["node_index"])
        family = self._family_from_query(text)
        style = self._style_from_query(text)
        context = self._context_from_query(text)
        return self._render(node, family, style, context)

    @staticmethod
    def _family_from_query(text: str) -> str:
        q = _norm(text)
        if any(x in q for x in ("calcule", "resolva", "exemplo")):
            return "problema_resolvido"
        if any(x in q for x in ("fonte", "evidencia", "evidência", "documento")):
            return "analise_de_fontes"
        if any(x in q for x in ("compare", "diferenca", "diferença", "versus")):
            return "comparacao"
        if any(x in q for x in ("limite", "falha", "erro")):
            return "falhas_e_limites"
        return "explicacao_profunda"

    @staticmethod
    def _style_from_query(text: str) -> str:
        q = _norm(text)
        if any(x in q for x in ("pesquisa", "estado da arte", "fronteira")):
            return "pesquisa"
        if any(x in q for x in ("pos gradu", "pós gradu", "mestrado", "doutorado")):
            return "pos_graduacao"
        if "graduacao" in q or "graduação" in q:
            return "graduacao"
        if "tecnico" in q or "técnico" in q:
            return "tecnico"
        return "didatico"

    @staticmethod
    def _context_from_query(text: str) -> str:
        q = _norm(text)
        for context, hints in {
            "quantitativo": ("calculo", "cálculo", "quantit"), "experimental": ("experimento", "medicao", "medição"),
            "historico": ("historia", "história", "origem"), "comparativo": ("compare", "versus"),
            "interdisciplinar": ("interdisciplin", "conecte"), "aplicado": ("aplicacao", "aplicação", "pratica", "prática"),
            "fronteira": ("fronteira", "estado da arte", "aberto"), "checagem": ("verifique", "valide", "confira"),
        }.items():
            if any(_norm(h) in q for h in hints):
                return context
        return "fundamentos"

    @staticmethod
    def _prompt(node: PlusNode, family: str, style: str, context: str) -> str:
        return (
            f"Em {node.label}, trate '{node.area}' pela lente '{node.lens_label}'. "
            f"Família={family}; estilo={style}; contexto={context}. {node.instruction}. "
            f"Diferencie fato, modelo, hipótese, incerteza e limite. Fonte-guia: {node.source}."
        )

    @staticmethod
    def _render(node: PlusNode, family: str, style: str, context: str) -> str:
        policy = ""
        if node.domain == "history":
            policy = " Em História, diferencie fonte primária, interpretação historiográfica, controvérsia e grau de certeza."
        elif node.domain == "psychology_sociology":
            policy = " Em Psicologia/Sociologia, trate como conteúdo educacional e de pesquisa, não como diagnóstico individual."
        elif node.domain == "decoding":
            policy = " Em Decodificação, mantenha o uso educacional/defensivo e não transforme o conteúdo em bypass ou quebra de credenciais."
        return (
            f"📚 PLUS — {node.label} | {node.area} — {node.lens_label}. "
            f"Foco: {node.instruction}. Modo: {family}, estilo {style}, contexto {context}. "
            f"Ao responder, explicite pressupostos, evidência, incerteza, limitações e como verificar o resultado. "
            f"Fonte de referência da trilha: {node.source}.{policy}"
        )
