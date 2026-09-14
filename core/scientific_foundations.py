"""BLOCO 5 — Fundamentos Científicos da STAR.

Esta camada unifica a organização científica sem duplicar os motores locais já
existentes. Conhecimento científico persistente continua obedecendo ao BLOCO 2
(epistemologia) e ao BLOCO 3 (conhecimento universal), e todas as relações usam o
Knowledge Graph oficial da MIND.

Escala lógica:
- 50 ramos científicos × 20 lentes = 1.000 nós canônicos;
- 10 profundidades × 10 contextos de método × 10 modos de evidência ×
  10 representações × 10 contextos de aplicação × 10 verificações =
  1.000.000 variações por nó;
- 1.000 × 1.000.000 = 1.000.000.000 representações endereçáveis em B05.

As representações são materializadas sob demanda. O número 1B não representa um
bilhão de fatos independentes pesquisados nem um bilhão de linhas no SQLite.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
import unicodedata
from typing import Any

from core.universal_knowledge import UniversalKnowledgeArchitecture


@dataclass(frozen=True)
class ScientificBranch:
    domain: str
    key: str
    label: str
    subbranches: tuple[str, ...]


SCIENTIFIC_DOMAINS = (
    "logic",
    "mathematics",
    "statistics",
    "scientific_method",
    "physics",
    "chemistry",
    "biology",
    "geology",
    "astronomy",
    "climatology",
    "ecology",
    "fauna",
    "flora",
)

DOMAIN_LABELS = {
    "logic": "Lógica",
    "mathematics": "Matemática",
    "statistics": "Estatística",
    "scientific_method": "Método científico",
    "physics": "Física",
    "chemistry": "Química",
    "biology": "Biologia",
    "geology": "Geologia",
    "astronomy": "Astronomia",
    "climatology": "Climatologia",
    "ecology": "Ecologia",
    "fauna": "Fauna",
    "flora": "Flora",
}


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


SCIENTIFIC_BRANCHES = (
    # Lógica — 3
    ScientificBranch("logic", "formal_logic", "Lógica formal", _subs(
        "lógica proposicional;lógica de predicados;lógica booleana;lógica modal;lógica temporal;lógica epistêmica;lógica deôntica;lógica intuicionista;lógica paraconsistente;lógica multivalorada;lógica fuzzy"
    )),
    ScientificBranch("logic", "proof_models_computation", "Provas, modelos e computação", _subs(
        "dedução natural;sistemas axiomáticos;teoria da prova;teoria de modelos;correção;completude;decidibilidade;computabilidade;lógica matemática"
    )),
    ScientificBranch("logic", "inference_argumentation", "Inferência e argumentação", _subs(
        "dedução;indução;abdução;raciocínio bayesiano;argumentação;contraexemplos;falácias formais;falácias informais"
    )),
    # Matemática — 5
    ScientificBranch("mathematics", "numbers_algebra", "Números e álgebra", _subs(
        "aritmética;sistemas numéricos;álgebra elementar;equações;inequações;polinômios;teoria dos números;grupos;anéis;corpos;álgebra abstrata"
    )),
    ScientificBranch("mathematics", "geometry_topology", "Geometria e topologia", _subs(
        "geometria euclidiana;geometria analítica;trigonometria;geometria diferencial;topologia;variedades;geometria algébrica"
    )),
    ScientificBranch("mathematics", "calculus_analysis", "Cálculo e análise", _subs(
        "limites;derivadas;integrais;séries;cálculo multivariável;cálculo vetorial;análise real;análise complexa;análise funcional;teoria da medida"
    )),
    ScientificBranch("mathematics", "linear_discrete", "Álgebra linear e matemática discreta", _subs(
        "vetores;matrizes;autovalores;autovetores;transformações lineares;combinatória;matemática discreta;teoria dos grafos"
    )),
    ScientificBranch("mathematics", "differential_numerical_optimization", "Equações diferenciais, métodos numéricos e otimização", _subs(
        "EDO;EDP;sistemas dinâmicos;cálculo variacional;métodos numéricos;otimização convexa;otimização não linear;problemas inversos"
    )),
    # Estatística — 4
    ScientificBranch("statistics", "probability_stochastic", "Probabilidade e processos estocásticos", _subs(
        "axiomas de probabilidade;variáveis aleatórias;distribuições;processos estocásticos;cadeias de Markov;Monte Carlo"
    )),
    ScientificBranch("statistics", "descriptive_inferential", "Estatística descritiva e inferencial", _subs(
        "estatística descritiva;amostragem;estimadores;intervalos de confiança;testes de hipótese;poder estatístico;tamanho de efeito"
    )),
    ScientificBranch("statistics", "regression_multivariate_bayesian", "Regressão, multivariada e Bayes", _subs(
        "regressão linear;modelos lineares generalizados;estatística multivariada;inferência bayesiana;modelos hierárquicos"
    )),
    ScientificBranch("statistics", "experimental_data_science", "Estatística experimental e ciência de dados", _subs(
        "desenho de experimentos;séries temporais;análise de sobrevivência;inferência causal;meta-análise;propagação de incerteza;validação cruzada"
    )),
    # Método científico — 4
    ScientificBranch("scientific_method", "scientific_reasoning", "Raciocínio científico", _subs(
        "perguntas científicas;hipóteses;falseabilidade;operacionalização;modelos;previsões;inferência científica"
    )),
    ScientificBranch("scientific_method", "experiment_measurement", "Experimento e medição", _subs(
        "variáveis;controles;protocolos;calibração;metrologia;rastreabilidade;erro de medição;incerteza experimental"
    )),
    ScientificBranch("scientific_method", "evidence_reproducibility", "Evidência e reprodutibilidade", _subs(
        "hierarquia de evidências;replicação;reprodutibilidade;revisão por pares;pré-registro;dados abertos;meta-análise"
    )),
    ScientificBranch("scientific_method", "scientific_inference_ethics", "Inferência, vieses e ética científica", _subs(
        "correlação e causalidade;seleção de modelos;análise de sensibilidade;vieses;publicação científica;ética em pesquisa;limites de inferência"
    )),
    # Física — 6
    ScientificBranch("physics", "classical_mechanics", "Mecânica clássica", _subs(
        "cinemática;dinâmica;estática;leis de Newton;energia;momento;corpos rígidos;gravitação;oscilações;mecânica analítica"
    )),
    ScientificBranch("physics", "thermodynamics_statistical", "Termodinâmica e física estatística", _subs(
        "temperatura;calor;trabalho;entropia;potenciais termodinâmicos;transições de fase;mecânica estatística;não equilíbrio"
    )),
    ScientificBranch("physics", "fluids_waves_optics", "Fluidos, ondas e óptica", _subs(
        "hidrostática;hidrodinâmica;aerodinâmica;viscosidade;turbulência;ondas;acústica;óptica geométrica;óptica física;fótons"
    )),
    ScientificBranch("physics", "electromagnetism", "Eletromagnetismo", _subs(
        "eletrostática;magnetostática;indução;equações de Maxwell;ondas eletromagnéticas;antenas;materiais eletromagnéticos"
    )),
    ScientificBranch("physics", "relativity_gravity", "Relatividade e gravitação", _subs(
        "relatividade especial;espaço-tempo;transformações de Lorentz;relatividade geral;geodésicas;curvatura;buracos negros;ondas gravitacionais"
    )),
    ScientificBranch("physics", "quantum_particles_fields", "Física quântica, atômica, nuclear e de partículas", _subs(
        "mecânica quântica;átomos;moléculas;física nuclear;partículas elementares;Modelo Padrão;teoria quântica de campos;matéria condensada"
    )),
    # Química — 5
    ScientificBranch("chemistry", "general_physical", "Química geral e físico-química", _subs(
        "estrutura atômica;ligações;estequiometria;termoquímica;termodinâmica química;cinética;equilíbrio;eletroquímica;química quântica"
    )),
    ScientificBranch("chemistry", "organic", "Química orgânica", _subs(
        "estrutura orgânica;estereoquímica;mecanismos;grupos funcionais;síntese;química medicinal;polímeros orgânicos"
    )),
    ScientificBranch("chemistry", "inorganic", "Química inorgânica", _subs(
        "elementos;coordenação;organometálicos;estado sólido;química bioinorgânica;catálise inorgânica"
    )),
    ScientificBranch("chemistry", "analytical", "Química analítica", _subs(
        "análise qualitativa;análise quantitativa;espectroscopia;cromatografia;eletroanálise;quimiometria;metrologia química"
    )),
    ScientificBranch("chemistry", "biochemistry_materials_environmental", "Bioquímica, materiais e química ambiental", _subs(
        "bioquímica;química de materiais;nanomateriais;química ambiental;radioquímica;química computacional;química supramolecular"
    )),
    # Biologia — 5
    ScientificBranch("biology", "molecular_cellular", "Biologia molecular e celular", _subs(
        "biomoléculas;células;membranas;metabolismo;sinalização;expressão gênica;proteômica;biologia estrutural"
    )),
    ScientificBranch("biology", "genetics_genomics", "Genética e genômica", _subs(
        "genética mendeliana;genética molecular;genômica;epigenética;genética de populações;bioinformática"
    )),
    ScientificBranch("biology", "evolution_systematics", "Evolução e sistemática", _subs(
        "seleção natural;deriva genética;especiação;filogenia;sistemática;macroevolução;paleobiologia"
    )),
    ScientificBranch("biology", "physiology_development", "Fisiologia e desenvolvimento", _subs(
        "fisiologia animal;fisiologia vegetal;neurobiologia;endocrinologia;desenvolvimento;homeostase;biologia reprodutiva"
    )),
    ScientificBranch("biology", "microbiology_immunology_biotech", "Microbiologia, imunologia e biotecnologia", _subs(
        "bacteriologia;virologia;micologia;parasitologia;imunologia;biotecnologia;engenharia genética;biologia sintética"
    )),
    # Geologia — 3
    ScientificBranch("geology", "earth_materials_geochemistry", "Materiais terrestres e geoquímica", _subs(
        "mineralogia;petrologia;cristalografia;geoquímica;meteoritos;geocronologia"
    )),
    ScientificBranch("geology", "geodynamics_tectonics", "Geodinâmica e tectônica", _subs(
        "estrutura interna da Terra;tectônica de placas;sismologia;vulcanologia;geofísica;orogênese"
    )),
    ScientificBranch("geology", "surface_history_resources", "Superfície, história da Terra e recursos", _subs(
        "geomorfologia;sedimentologia;estratigrafia;paleontologia;hidrogeologia;pedologia;recursos minerais;riscos geológicos"
    )),
    # Astronomia — 3
    ScientificBranch("astronomy", "solar_planetary", "Astronomia planetária", _subs(
        "Sistema Solar;planetas;luas;asteroides;cometas;exoplanetas;ciência planetária;astrobiologia"
    )),
    ScientificBranch("astronomy", "stellar_galactic", "Astronomia estelar e galáctica", _subs(
        "estrelas;evolução estelar;meio interestelar;aglomerados;Via Láctea;galáxias;objetos compactos;altas energias"
    )),
    ScientificBranch("astronomy", "cosmology_observational", "Cosmologia e astronomia observacional", _subs(
        "cosmologia;expansão do Universo;CMB;estrutura em grande escala;telescópios;fotometria;espectroscopia;astrometria;radioastronomia"
    )),
    # Climatologia — 2
    ScientificBranch("climatology", "atmosphere_climate_system", "Atmosfera e sistema climático", _subs(
        "física atmosférica;circulação;radiação;termodinâmica atmosférica;nuvens;precipitação;interação oceano-atmosfera;modelagem climática"
    )),
    ScientificBranch("climatology", "climate_variability_change", "Variabilidade e mudança climática", _subs(
        "paleoclima;ENSO;variabilidade natural;forçantes;atribuição;extremos climáticos;projeções;incerteza climática"
    )),
    # Ecologia — 3
    ScientificBranch("ecology", "populations_communities", "Ecologia de populações e comunidades", _subs(
        "dinâmica populacional;metapopulações;competição;predação;mutualismo;redes tróficas;biodiversidade"
    )),
    ScientificBranch("ecology", "ecosystems_biogeochemistry", "Ecossistemas e biogeoquímica", _subs(
        "fluxo de energia;ciclos biogeoquímicos;produção primária;decomposição;ecologia aquática;ecologia terrestre;ecologia microbiana"
    )),
    ScientificBranch("ecology", "landscape_conservation_global_change", "Paisagem, conservação e mudança global", _subs(
        "ecologia de paisagem;biogeografia;fragmentação;conservação;restauração;invasões biológicas;mudança global"
    )),
    # Fauna — 3
    ScientificBranch("fauna", "zoological_diversity", "Diversidade zoológica", _subs(
        "invertebrados;vertebrados;entomologia;ictiologia;herpetologia;ornitologia;mastozoologia;taxonomia animal"
    )),
    ScientificBranch("fauna", "animal_form_function_behavior", "Forma, função e comportamento animal", _subs(
        "anatomia comparada;fisiologia animal;locomoção;alimentação;reprodução;etologia;ecologia sensorial;cognição animal"
    )),
    ScientificBranch("fauna", "animal_ecology_conservation", "Ecologia e conservação da fauna", _subs(
        "populações animais;migração;ecologia trófica;ecologia da vida selvagem;zoogeografia;conservação animal"
    )),
    # Flora — 4
    ScientificBranch("flora", "plant_diversity_systematics", "Diversidade e sistemática vegetal", _subs(
        "algas;briófitas;pteridófitas;gimnospermas;angiospermas;taxonomia vegetal;filogenia vegetal"
    )),
    ScientificBranch("flora", "plant_anatomy_physiology", "Anatomia e fisiologia vegetal", _subs(
        "tecidos vegetais;raízes;caules;folhas;fotossíntese;respiração;transporte;hormônios;estresse vegetal"
    )),
    ScientificBranch("flora", "plant_reproduction_evolution", "Reprodução e evolução vegetal", _subs(
        "reprodução vegetal;polinização;dispersão;sementes;coevolução;domesticação;evolução vegetal"
    )),
    ScientificBranch("flora", "plant_ecology_conservation", "Ecologia e conservação da flora", _subs(
        "vegetação;fitogeografia;sucessão;relações planta-solo;restauração;etnobotânica;conservação vegetal"
    )),
)

SCIENTIFIC_LENSES = (
    ("concept", "conceito", "definir terminologia, escopo e condições de uso"),
    ("law", "lei", "explicitar enunciado, domínio de validade e limites"),
    ("theory", "teoria", "descrever modelo explicativo, previsões e evidências"),
    ("formula", "fórmula", "registrar símbolos, unidades, hipóteses e dimensionalidade"),
    ("equation", "equação", "ligar variáveis, solução, condições iniciais/de contorno e interpretação"),
    ("experiment", "experimento", "descrever hipótese, variáveis, controles, protocolo, medição e replicação"),
    ("property", "propriedade", "caracterizar propriedade, método de medição e dependências"),
    ("unit", "unidade", "definir grandeza, sistema de unidades, conversões e rastreabilidade"),
    ("constant", "constante", "registrar valor, unidade, incerteza, versão e fonte metrológica"),
    ("relation", "relação", "explicar relação causal, funcional, estatística ou estrutural"),
    ("discovery", "descoberta", "preservar contexto histórico, evidência original e revisões posteriores"),
    ("method", "método", "descrever procedimento, instrumentos, pressupostos e validação"),
    ("evidence", "evidência", "distinguir suporte, refutação, qualidade, independência e incerteza"),
    ("exception", "exceção", "registrar contraexemplos, regimes especiais e falhas do modelo"),
    ("application", "aplicação", "conectar teoria a uso real sem extrapolar o domínio válido"),
    ("problem", "problema", "formular dados, incógnitas, restrições e critério de solução"),
    ("solution", "solução", "resolver com método verificável, unidades, checagens e casos limite"),
    ("subdiscipline", "subdisciplina", "organizar taxonomia, escopo, interfaces e subvertentes"),
    ("history", "história científica", "situar evolução conceitual sem confundir prioridade histórica com validade"),
    ("frontier", "fronteira", "separar consenso, hipótese ativa, resultado preliminar e especulação"),
)

DEPTHS = (
    "fundamental", "basic", "intermediate", "advanced", "undergraduate",
    "graduate", "professional", "research", "specialist", "review",
)
METHOD_CONTEXTS = (
    "deductive", "inductive", "abductive", "experimental", "observational",
    "comparative", "computational", "theoretical", "field", "laboratory",
)
EVIDENCE_MODES = (
    "primary_measurement", "controlled_experiment", "observational_data", "replication",
    "systematic_review", "meta_analysis", "validated_model", "reference_standard",
    "historical_record", "uncertain_or_frontier",
)
REPRESENTATIONS = (
    "explanation", "symbolic", "equations", "table", "graph", "diagram_schema",
    "worked_example", "experiment_protocol", "case_study", "taxonomy",
)
APPLICATION_CONTEXTS = (
    "theory", "education", "laboratory", "field", "engineering", "technology",
    "environment", "health_biology", "earth_space", "interdisciplinary",
)
VERIFICATIONS = (
    "logic", "units", "dimensional_analysis", "numerical", "uncertainty",
    "source_trace", "independent_confirmation", "boundary_cases", "reproducibility", "falsifiability",
)

REQUESTED_SCIENTIFIC_CONTENT = tuple(item[0] for item in SCIENTIFIC_LENSES[:18])
SCIENTIFIC_CANONICAL_NODES = len(SCIENTIFIC_BRANCHES) * len(SCIENTIFIC_LENSES)
SCIENTIFIC_VARIANTS_PER_NODE = (
    len(DEPTHS) * len(METHOD_CONTEXTS) * len(EVIDENCE_MODES) *
    len(REPRESENTATIONS) * len(APPLICATION_CONTEXTS) * len(VERIFICATIONS)
)
SCIENTIFIC_ADDRESSABLE_CONTENTS = SCIENTIFIC_CANONICAL_NODES * SCIENTIFIC_VARIANTS_PER_NODE

assert len(SCIENTIFIC_DOMAINS) == 13
assert len(SCIENTIFIC_BRANCHES) == 50
assert len(SCIENTIFIC_LENSES) == 20
assert SCIENTIFIC_CANONICAL_NODES == 1_000
assert SCIENTIFIC_VARIANTS_PER_NODE == 1_000_000
assert SCIENTIFIC_ADDRESSABLE_CONTENTS == 1_000_000_000
assert {branch.domain for branch in SCIENTIFIC_BRANCHES} == set(SCIENTIFIC_DOMAINS)

CROSS_DOMAIN_BRIDGES = {
    "logic": ("mathematics", "statistics", "scientific_method"),
    "mathematics": ("logic", "statistics", "physics"),
    "statistics": ("mathematics", "scientific_method", "biology", "ecology", "climatology"),
    "scientific_method": ("logic", "statistics"),
    "physics": ("mathematics", "chemistry", "astronomy", "climatology", "geology"),
    "chemistry": ("physics", "biology", "geology", "ecology"),
    "biology": ("chemistry", "ecology", "fauna", "flora"),
    "geology": ("physics", "chemistry", "climatology", "ecology"),
    "astronomy": ("physics", "mathematics", "geology"),
    "climatology": ("physics", "statistics", "geology", "ecology"),
    "ecology": ("biology", "statistics", "climatology", "fauna", "flora"),
    "fauna": ("biology", "ecology"),
    "flora": ("biology", "ecology"),
}


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return "_".join(re.findall(r"[a-z0-9]+", text))


def _decode_axes(variant_index: int) -> dict[str, str]:
    axes = (
        ("depth", DEPTHS),
        ("method_context", METHOD_CONTEXTS),
        ("evidence_mode", EVIDENCE_MODES),
        ("representation", REPRESENTATIONS),
        ("application_context", APPLICATION_CONTEXTS),
        ("verification", VERIFICATIONS),
    )
    remainder = int(variant_index)
    decoded: dict[str, str] = {}
    for name, values in reversed(axes):
        remainder, index = divmod(remainder, len(values))
        decoded[name] = values[index]
    if remainder:
        raise IndexError(variant_index)
    return decoded


class ScientificCatalog:
    """Catálogo B05 de 1B representações científicas, decodificado sob demanda."""

    NAMESPACE = "B05"

    def stats(self) -> dict:
        counts = {domain: 0 for domain in SCIENTIFIC_DOMAINS}
        for branch in SCIENTIFIC_BRANCHES:
            counts[branch.domain] += 1
        return {
            "namespace": self.NAMESPACE,
            "domains": len(SCIENTIFIC_DOMAINS),
            "domain_branch_counts": counts,
            "branches": len(SCIENTIFIC_BRANCHES),
            "lenses_per_branch": len(SCIENTIFIC_LENSES),
            "canonical_nodes": SCIENTIFIC_CANONICAL_NODES,
            "variants_per_node": SCIENTIFIC_VARIANTS_PER_NODE,
            "addressable_contents": SCIENTIFIC_ADDRESSABLE_CONTENTS,
            "materialization": "on-demand",
            "prepopulated_knowledge_rows": 0,
            "truthfulness_note": (
                "1B são representações científicas combinatórias endereçáveis; "
                "não 1B de fatos científicos independentes pesquisados"
            ),
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        node_index = int(node_index)
        variant_index = int(variant_index)
        if not 0 <= node_index < SCIENTIFIC_CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= variant_index < SCIENTIFIC_VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = node_index * SCIENTIFIC_VARIANTS_PER_NODE + variant_index + 1
        return f"SCI-B05-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"SCI-B05-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= SCIENTIFIC_ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, SCIENTIFIC_VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, len(SCIENTIFIC_LENSES))
        branch = SCIENTIFIC_BRANCHES[branch_index]
        lens_key, lens_label, instruction = SCIENTIFIC_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {
            "id": f"SCI-B05-{absolute:010d}",
            "namespace": self.NAMESPACE,
            "node_index": node_index,
            "variant_index": variant_index,
            "domain": branch.domain,
            "domain_label": DOMAIN_LABELS[branch.domain],
            "branch": branch.key,
            "branch_label": branch.label,
            "subbranches": branch.subbranches,
            "lens": lens_key,
            "lens_label": lens_label,
            **axes,
            "prompt": (
                f"{DOMAIN_LABELS[branch.domain]} / {branch.label} / {lens_label}: {instruction}. "
                f"Profundidade={axes['depth']}; método={axes['method_context']}; "
                f"evidência={axes['evidence_mode']}; representação={axes['representation']}; "
                f"aplicação={axes['application_context']}; verificação={axes['verification']}. "
                "Separar fato, hipótese, modelo, teoria e inferência; declarar unidades, "
                "incerteza, condições de validade, evidências e fontes quando aplicável."
            ),
        }


class ScientificFoundations:
    """Camada científica integrada ao BLOCO 2, BLOCO 3 e Knowledge Graph oficial."""

    NAMESPACE = "B05"
    TAXONOMY_ROOT_ID = "SCI-TAX-ROOT"

    def __init__(self, knowledge: UniversalKnowledgeArchitecture, *, reasoner=None):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.reasoner = reasoner
        self.catalog = ScientificCatalog()
        self._providers: dict[str, Any] = {}
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 5 — FUNDAMENTOS CIENTÍFICOS",
            logical_capacity=SCIENTIFIC_ADDRESSABLE_CONTENTS,
            source="core/scientific_foundations.py",
            metadata={
                "materialization": "on-demand",
                "role": "scientific-foundations",
                "canonical_gate": "BLOCO 2 -> BLOCO 3",
                "knowledge_graph": "shared",
                "local_scientific_providers": "reused-lazily",
            },
        )

    @staticmethod
    def _domain_key(value: str) -> str:
        normalized = _norm(value)
        aliases = {
            "logica": "logic", "logic": "logic",
            "matematica": "mathematics", "mathematics": "mathematics",
            "estatistica": "statistics", "statistics": "statistics",
            "metodo_cientifico": "scientific_method", "scientific_method": "scientific_method", "ciencia": "scientific_method",
            "fisica": "physics", "physics": "physics",
            "quimica": "chemistry", "chemistry": "chemistry",
            "biologia": "biology", "biology": "biology",
            "geologia": "geology", "geology": "geology",
            "astronomia": "astronomy", "astronomy": "astronomy",
            "climatologia": "climatology", "climatology": "climatology", "clima": "climatology",
            "ecologia": "ecology", "ecology": "ecology",
            "fauna": "fauna", "zoologia": "fauna",
            "flora": "flora", "botanica": "flora",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _branch(key: str) -> ScientificBranch:
        for branch in SCIENTIFIC_BRANCHES:
            if branch.key == key:
                return branch
        raise KeyError(key)

    def taxonomy_snapshot(self, domain: str | None = None) -> dict:
        domain_key = self._domain_key(domain) if domain else None
        if domain_key and domain_key not in SCIENTIFIC_DOMAINS:
            raise KeyError(domain)
        branches = [b for b in SCIENTIFIC_BRANCHES if domain_key is None or b.domain == domain_key]
        return {
            "root": "Ciência",
            "domain": domain_key,
            "branches": [
                {
                    "domain": b.domain,
                    "domain_label": DOMAIN_LABELS[b.domain],
                    "branch": b.key,
                    "branch_label": b.label,
                    "subbranches": list(b.subbranches),
                }
                for b in branches
            ],
            "cross_domain_bridges": deepcopy(CROSS_DOMAIN_BRIDGES),
        }

    @staticmethod
    def _domain_node_id(domain: str) -> str:
        return f"SCI-DOM-{domain.upper()}"

    @staticmethod
    def _branch_node_id(branch: str) -> str:
        return f"SCI-BR-{branch.upper()}"

    @staticmethod
    def _subbranch_node_id(branch: str, subbranch: str) -> str:
        slug = _norm(subbranch).upper()[:80]
        return f"SCI-SUB-{branch.upper()}-{slug}"

    def _ensure_taxonomy_path(self, branch: ScientificBranch, *, include_subbranches: bool = True) -> dict:
        root = self.graph.add_entity(
            "science_taxonomy", "Ciência", node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B05", "source_of_truth": "core/scientific_foundations.py"},
        )
        domain_id = self._domain_node_id(branch.domain)
        self.graph.add_entity(
            "science_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id,
            data={"block": "B05", "domain": branch.domain},
        )
        self.graph.relate(root, domain_id, "has_part", metadata={"block": "B05", "taxonomy": True})
        self.graph.relate(domain_id, root, "part_of", metadata={"block": "B05", "taxonomy": True})

        branch_id = self._branch_node_id(branch.key)
        self.graph.add_entity(
            "science_branch", branch.label, node_id=branch_id,
            data={"block": "B05", "domain": branch.domain, "branch": branch.key},
        )
        self.graph.relate(domain_id, branch_id, "has_part", metadata={"block": "B05", "taxonomy": True})
        self.graph.relate(branch_id, domain_id, "part_of", metadata={"block": "B05", "taxonomy": True})

        sub_ids = []
        if include_subbranches:
            for subbranch in branch.subbranches:
                sub_id = self._subbranch_node_id(branch.key, subbranch)
                self.graph.add_entity(
                    "science_subbranch", subbranch, node_id=sub_id,
                    data={"block": "B05", "domain": branch.domain, "branch": branch.key},
                )
                self.graph.relate(branch_id, sub_id, "has_part", metadata={"block": "B05", "taxonomy": True})
                self.graph.relate(sub_id, branch_id, "part_of", metadata={"block": "B05", "taxonomy": True})
                sub_ids.append(sub_id)
        return {"root_id": root, "domain_id": domain_id, "branch_id": branch_id, "subbranch_ids": sub_ids}

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        domain_key = self._domain_key(domain) if domain else None
        if domain_key and domain_key not in SCIENTIFIC_DOMAINS:
            raise KeyError(domain)
        selected = [b for b in SCIENTIFIC_BRANCHES if domain_key is None or b.domain == domain_key]
        paths = [self._ensure_taxonomy_path(branch) for branch in selected]
        return {
            "domain": domain_key,
            "branches_materialized": len(paths),
            "knowledge_graph": "shared",
            "paths": paths,
        }

    def _physics_reference(self, query: str) -> dict | None:
        if "physics" not in self._providers:
            from core.physics_knowledge_150k import PhysicsKnowledgeEngine, SOURCES
            self._providers["physics"] = (PhysicsKnowledgeEngine(), SOURCES)
        engine, sources = self._providers["physics"]
        topic = engine.match(query)
        if topic is None:
            return None
        return {
            "provider": "core.physics_knowledge_150k",
            "domain": "physics",
            "title": topic.title,
            "summary": topic.summary,
            "formula": topic.formula,
            "source": sources[topic.source],
            "topic_id": topic.id,
        }

    def _chemistry_reference(self, query: str) -> dict | None:
        if "chemistry" not in self._providers:
            from core.chemistry_knowledge_500k import ChemistryKnowledgeEngine, SOURCES
            self._providers["chemistry"] = (ChemistryKnowledgeEngine(), SOURCES)
        engine, sources = self._providers["chemistry"]
        topic = engine.match(query)
        if topic is None:
            return None
        return {
            "provider": "core.chemistry_knowledge_500k",
            "domain": "chemistry",
            "title": topic.title,
            "summary": topic.summary,
            "formula": topic.formula,
            "source": sources[topic.source],
            "topic_id": topic.id,
        }

    def _multidisciplinary_reference(self, query: str, domain: str) -> dict | None:
        if "multidisciplinary" not in self._providers:
            from core.multidisciplinary_knowledge import MultidisciplinaryKnowledgeEngine
            self._providers["multidisciplinary"] = MultidisciplinaryKnowledgeEngine()
        engine = self._providers["multidisciplinary"]
        hints = {
            "logic": "lógica", "mathematics": "matemática", "statistics": "estatística",
            "biology": "biologia", "ecology": "biologia ecologia", "fauna": "biologia zoologia",
            "flora": "biologia botânica", "geology": "geografia geologia", "climatology": "geografia climatologia",
        }
        enriched = f"{hints.get(domain, '')} {query}".strip()
        answer = engine.answer(enriched)
        if not answer:
            return None
        return {
            "provider": "core.multidisciplinary_knowledge",
            "domain": domain,
            "answer": answer,
            "source": "provedor multidisciplinar local da STAR",
        }

    def _curriculum_reference(self, query: str, domain: str) -> dict | None:
        if "curriculum" not in self._providers:
            from core.curriculum_knowledge import CurriculumKnowledgeEngine
            self._providers["curriculum"] = CurriculumKnowledgeEngine()
        engine = self._providers["curriculum"]
        answer = engine.answer(query)
        if not answer:
            return None
        return {
            "provider": "core.curriculum_knowledge",
            "domain": domain,
            "answer": answer,
            "source": "catálogo curricular científico local da STAR",
        }

    def reference(self, query: str, *, domain: str | None = None) -> dict | None:
        query = _clean(query)
        if not query:
            return None
        domain_key = self._domain_key(domain) if domain else None
        if domain_key and domain_key not in SCIENTIFIC_DOMAINS:
            raise KeyError(domain)

        explicit = domain_key
        if explicit == "physics":
            result = self._physics_reference(query)
            if result:
                return result
        if explicit == "chemistry":
            result = self._chemistry_reference(query)
            if result:
                return result
        if explicit in {"logic", "mathematics", "statistics", "biology", "geology", "climatology", "ecology", "fauna", "flora"}:
            result = self._multidisciplinary_reference(query, explicit)
            if result:
                return result
        if explicit in {"scientific_method", "astronomy"}:
            result = self._curriculum_reference(query, explicit)
            if result:
                return result

        # Sem domínio explícito: especializados primeiro, depois catálogos amplos.
        for finder in (self._physics_reference, self._chemistry_reference):
            result = finder(query)
            if result:
                return result
        result = self._multidisciplinary_reference(query, explicit or "mathematics")
        if result:
            return result
        return self._curriculum_reference(query, explicit or "scientific_method")

    def evaluate_hypothesis(self, hypothesis: str, *, observations: list[dict] | None = None) -> dict:
        if self.reasoner is None:
            from core.mind import ScientificReasoner
            self.reasoner = ScientificReasoner()
        result = self.reasoner.evaluate(hypothesis, observations=observations)
        result["block"] = "B05"
        result["epistemic_note"] = (
            "avaliação científica é artefato de raciocínio; hipótese não se torna fato ou conhecimento canônico automaticamente"
        )
        return result

    def promote_canonical_scientific(
        self,
        record_id: str,
        canonical_label: str,
        *,
        domain: str,
        branch: str,
        knowledge_type: str = "concept",
        aliases: list[str] | tuple[str, ...] | None = None,
        properties: dict | None = None,
        subtopics: list[str] | tuple[str, ...] | None = None,
        contexts: list[str] | tuple[str, ...] | None = None,
        rules: list | tuple | None = None,
        exceptions: list | tuple | None = None,
        summary: str = "",
    ) -> dict:
        domain_key = self._domain_key(domain)
        if domain_key not in SCIENTIFIC_DOMAINS:
            raise ValueError(f"domínio científico inválido: {domain}")
        branch_obj = self._branch(branch)
        if branch_obj.domain != domain_key:
            raise ValueError(f"ramo {branch} não pertence a {domain_key}")

        result = self.knowledge.promote_canonical(
            record_id,
            canonical_label,
            knowledge_type=knowledge_type,
            namespace=self.NAMESPACE,
            summary=summary,
            aliases=aliases,
            properties=properties,
            categories=["science", domain_key, branch_obj.key],
            subtopics=subtopics,
            contexts=contexts,
            rules=rules,
            exceptions=exceptions,
            provenance={
                "scientific_block": "B05",
                "domain": domain_key,
                "branch": branch_obj.key,
                "source_record_id": record_id,
            },
        )
        taxonomy = self._ensure_taxonomy_path(branch_obj, include_subbranches=False)
        self.graph.relate(
            result["knowledge_id"], taxonomy["branch_id"], "is_a",
            metadata={"block": "B05", "scientific_taxonomy": True},
        )
        self.graph.relate(
            taxonomy["branch_id"], result["knowledge_id"], "has_part",
            metadata={"block": "B05", "scientific_taxonomy": True},
        )
        return result

    def relate_scientific(self, source_id: str, target_id: str, relation: str, *, weight: float = 1.0) -> dict:
        return self.knowledge.relate(
            source_id, target_id, relation, weight=weight,
            metadata={"block": "B05", "scientific_foundations": True},
        )

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "domains": [{"key": key, "label": DOMAIN_LABELS[key]} for key in SCIENTIFIC_DOMAINS],
            "lenses": [{"key": key, "label": label} for key, label, _ in SCIENTIFIC_LENSES],
            "knowledge_graph": "shared knowledge_nodes/knowledge_edges",
            "canonical_knowledge": "BLOCO 2 gate -> BLOCO 3 universal knowledge",
            "providers": {
                "physics": "core.physics_knowledge_150k",
                "chemistry": "core.chemistry_knowledge_500k",
                "logic_math_biology_earth_life": "core.multidisciplinary_knowledge",
                "broad_scientific_fallback": "core.curriculum_knowledge",
            },
            "providers_loaded": sorted(self._providers),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None

        if low in {
            "status bloco 5", "status ciência", "status ciencia",
            "fundamentos científicos", "fundamentos cientificos",
            "status fundamentos científicos", "status fundamentos cientificos",
        }:
            stats = self.stats()
            return (
                "🔬 BLOCO 5 — FUNDAMENTOS CIENTÍFICOS: "
                f"{stats['catalog']['addressable_contents']} conteúdos endereçáveis em B05 | "
                f"{stats['catalog']['domains']} domínios × {stats['catalog']['branches']} ramos × "
                f"{stats['catalog']['lenses_per_branch']} lentes = {stats['catalog']['canonical_nodes']} nós | "
                "Knowledge Graph=COMPARTILHADO | provedores científicos existentes=REUTILIZADOS."
            )

        item = self.catalog.get_variant(raw.upper())
        if item:
            return (
                f"🔬 {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n"
                f"{item['prompt']}"
            )

        taxonomy = re.match(r"^(?:taxonomia cientifica|taxonomia científica)(?:\s+(.+))?$", raw, re.I)
        if taxonomy:
            domain = taxonomy.group(1)
            snapshot = self.taxonomy_snapshot(domain)
            labels = ", ".join(branch["branch_label"] for branch in snapshot["branches"][:12])
            suffix = "…" if len(snapshot["branches"]) > 12 else ""
            return f"🔬 Taxonomia científica: {len(snapshot['branches'])} ramos. {labels}{suffix}"

        reference = re.match(
            r"^(?:referencia cientifica|referência científica)(?:\s+\[([^\]]+)\])?\s+(.+)$",
            raw, re.I,
        )
        if reference:
            domain, query = reference.group(1), reference.group(2)
            result = self.reference(query, domain=domain)
            if not result:
                return "Não encontrei uma referência científica local suficientemente específica para essa consulta."
            if "title" in result:
                formula = f" Relação-base: {result['formula']}." if result.get("formula") else ""
                return f"🔬 {result['title']} — {result['summary']}{formula} Fonte: {result['source']}."
            return f"🔬 {result['answer']}"

        return None
