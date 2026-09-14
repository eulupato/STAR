"""BLOCO 6 — Vida, Corpo e Necessidades Humanas da STAR.

Esta camada organiza conhecimento sobre vida, biologia humana, anatomia,
fisiologia e necessidades humanas sem criar um sistema clínico paralelo.
A ciência de base permanece no BLOCO 5; conhecimento persistente continua
obedecendo ao gate epistêmico do BLOCO 2, à organização universal do BLOCO 3 e
ao Knowledge Graph oficial.

Regra de segurança permanente:
CONHECIMENTO BIOLÓGICO ≠ DIAGNÓSTICO AUTOMÁTICO.
Sinais corporais, dor, fadiga, fome, sede, sono ou observações pessoais são
contexto e nunca são convertidos automaticamente em doença, condição médica ou
tratamento.

Escala lógica:
- 50 ramos × 20 lentes = 1.000 nós canônicos;
- 10 profundidades × 10 escalas biológicas × 10 contextos fisiológicos ×
  10 fases da vida × 10 modos de evidência × 10 representações =
  1.000.000 variações por nó;
- 1.000 × 1.000.000 = 1.000.000.000 representações endereçáveis em B06.

As representações são materializadas sob demanda. 1B não significa um bilhão de
fatos independentes pesquisados nem um bilhão de linhas pré-carregadas.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
import unicodedata
from typing import Any

from core.universal_knowledge import UniversalKnowledgeArchitecture


@dataclass(frozen=True)
class HumanLifeBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


HUMAN_LIFE_DOMAINS = (
    "life_foundations",
    "cells_tissues",
    "metabolism_homeostasis",
    "evolution_adaptation",
    "anatomy",
    "cardiorespiratory",
    "digestive_nutrition",
    "musculoskeletal_skin",
    "nervous_sensory",
    "immune_endocrine",
    "reproduction_development_aging",
    "needs_sleep_fatigue",
    "hygiene_prevention",
)

DOMAIN_LABELS = {
    "life_foundations": "Fundamentos da vida e organismos",
    "cells_tissues": "Células, tecidos, órgãos e sistemas",
    "metabolism_homeostasis": "Metabolismo e homeostase",
    "evolution_adaptation": "Evolução e adaptação",
    "anatomy": "Anatomia humana",
    "cardiorespiratory": "Sistema cardiovascular e respiratório",
    "digestive_nutrition": "Digestão e nutrição",
    "musculoskeletal_skin": "Músculos, ossos, movimento e pele",
    "nervous_sensory": "Sistema nervoso, cérebro e sentidos",
    "immune_endocrine": "Imunidade e sistema endócrino",
    "reproduction_development_aging": "Reprodução, desenvolvimento e envelhecimento",
    "needs_sleep_fatigue": "Necessidades humanas, sono e fadiga",
    "hygiene_prevention": "Higiene, prevenção e autocuidado básico",
}


HUMAN_LIFE_BRANCHES = (
    # Fundamentos da vida — 3
    HumanLifeBranch("life_foundations", "life_organization", "Organização da vida e integração do organismo", _subs(
        "vida;organismos;níveis de organização biológica;células;tecidos;órgãos;sistemas;organismo integrado;"
        "sistemas corporais;comunicação entre sistemas;homeostase;respostas integradas;ambiente interno"
    )),
    HumanLifeBranch("life_foundations", "biomolecules_cellular_basis", "Base molecular e celular da vida", _subs(
        "água;íons;carboidratos;lipídios;proteínas;ácidos nucleicos;ATP;membranas;organelas"
    )),
    HumanLifeBranch("life_foundations", "genes_information", "Informação biológica e expressão gênica", _subs(
        "DNA;RNA;genes;cromossomos;replicação;transcrição;tradução;regulação gênica"
    )),

    # Células, tecidos, órgãos e sistemas — 4
    HumanLifeBranch("cells_tissues", "cell_structure_function", "Estrutura e função celular", _subs(
        "membrana plasmática;citoplasma;núcleo;mitocôndrias;ribossomos;retículo endoplasmático;Golgi;lisossomos;citoesqueleto"
    )),
    HumanLifeBranch("cells_tissues", "cell_transport_cycle", "Transporte, sinalização e ciclo celular", _subs(
        "difusão;osmose;transporte ativo;endocitose;exocitose;receptores;sinalização celular;ciclo celular;mitose;apoptose"
    )),
    HumanLifeBranch("cells_tissues", "tissue_biology", "Biologia dos tecidos", _subs(
        "tecido epitelial;tecido conjuntivo;tecido muscular;tecido nervoso;matriz extracelular;regeneração;reparo"
    )),
    HumanLifeBranch("cells_tissues", "organs_systems", "Órgãos e sistemas corporais", _subs(
        "órgãos;unidades funcionais;vascularização;inervação;integração anatômica;integração fisiológica"
    )),

    # Metabolismo e homeostase — 4
    HumanLifeBranch("metabolism_homeostasis", "energy_metabolism", "Metabolismo energético", _subs(
        "metabolismo;catabolismo;anabolismo;enzimas;ATP;glicólise;ciclo do ácido cítrico;fosforilação oxidativa;metabolismo de lipídios;metabolismo de aminoácidos"
    )),
    HumanLifeBranch("metabolism_homeostasis", "fluids_electrolytes_acid_base", "Fluidos, eletrólitos e equilíbrio ácido-base", _subs(
        "água corporal;compartimentos líquidos;sódio;potássio;cálcio;osmolaridade;pH;sistemas tampão;equilíbrio ácido-base"
    )),
    HumanLifeBranch("metabolism_homeostasis", "thermoregulation_energy_balance", "Termorregulação e balanço energético", _subs(
        "temperatura corporal;produção de calor;perda de calor;metabolismo basal;balanço energético;termogênese"
    )),
    HumanLifeBranch("metabolism_homeostasis", "feedback_homeostasis", "Fisiologia, homeostase e feedback", _subs(
        "fisiologia;homeostase;feedback negativo;feedback positivo;set points;controle fisiológico;compensação;integração neuroendócrina"
    )),

    # Evolução e adaptação — 3
    HumanLifeBranch("evolution_adaptation", "human_evolution", "Evolução humana e ancestralidade", _subs(
        "evolução;seleção natural;deriva genética;ancestralidade humana;hominínios;genética de populações;filogenia"
    )),
    HumanLifeBranch("evolution_adaptation", "adaptation_plasticity", "Adaptação e plasticidade", _subs(
        "adaptação;aclimatação;plasticidade fenotípica;adaptação fisiológica;adaptação ambiental;resposta ao treinamento"
    )),
    HumanLifeBranch("evolution_adaptation", "variation_life_history", "Variação humana e história de vida", _subs(
        "variação biológica;diversidade genética;crescimento;maturação;reprodução;senescência;trade-offs de história de vida"
    )),

    # Anatomia — 3
    HumanLifeBranch("anatomy", "anatomical_language", "Organização, linguagem e visualização anatômica", _subs(
        "posição anatômica;planos anatômicos;eixos;regiões corporais;cavidades;termos direcionais;superfície corporal;"
        "histologia;microscopia;anatomia seccional;imagem anatômica;relações espaciais;variação anatômica normal"
    )),
    HumanLifeBranch("anatomy", "axial_anatomy", "Anatomia axial", _subs(
        "cabeça;pescoço;tórax;abdome;pelve;coluna;órgãos torácicos;órgãos abdominais"
    )),
    HumanLifeBranch("anatomy", "appendicular_anatomy", "Anatomia dos membros", _subs(
        "cintura escapular;membro superior;mão;cintura pélvica;membro inferior;pé;relações neurovasculares"
    )),

    # Cardiovascular e respiratório — 4
    HumanLifeBranch("cardiorespiratory", "cardiovascular_system", "Sistema cardiovascular", _subs(
        "coração;vasos sanguíneos;artérias;veias;capilares;sangue;circulação pulmonar;circulação sistêmica"
    )),
    HumanLifeBranch("cardiorespiratory", "heart_function", "Coração e função cardíaca", _subs(
        "câmaras cardíacas;válvulas;ciclo cardíaco;débito cardíaco;sistema de condução;frequência cardíaca;pressão arterial"
    )),
    HumanLifeBranch("cardiorespiratory", "respiratory_system", "Sistema respiratório e pulmões", _subs(
        "pulmões;vias aéreas;traqueia;brônquios;bronquíolos;alvéolos;pleura;ventilação;mecânica respiratória"
    )),
    HumanLifeBranch("cardiorespiratory", "gas_exchange_transport", "Trocas gasosas e transporte", _subs(
        "oxigênio;dióxido de carbono;difusão alveolar;hemoglobina;transporte de gases;controle respiratório;relação ventilação-perfusão"
    )),

    # Digestão e nutrição — 4
    HumanLifeBranch("digestive_nutrition", "digestive_system", "Sistema digestório", _subs(
        "boca;saliva;esôfago;estômago;intestino delgado;intestino grosso;fígado;vesícula biliar;pâncreas;digestão"
    )),
    HumanLifeBranch("digestive_nutrition", "digestion_absorption_microbiome", "Digestão, absorção e microbioma", _subs(
        "digestão mecânica;digestão química;enzimas digestivas;absorção;motilidade;barreira intestinal;microbioma intestinal"
    )),
    HumanLifeBranch("digestive_nutrition", "nutrition_macronutrients", "Nutrição e macronutrientes", _subs(
        "nutrição;carboidratos;proteínas;gorduras;fibras;energia alimentar;digestibilidade;balanço energético"
    )),
    HumanLifeBranch("digestive_nutrition", "micronutrients_hydration", "Micronutrientes e hidratação", _subs(
        "vitaminas;minerais;eletrólitos;água;hidratação;necessidades nutricionais;biodisponibilidade"
    )),

    # Musculoesquelético e pele — 4
    HumanLifeBranch("musculoskeletal_skin", "muscle_system", "Músculos e contração", _subs(
        "músculos;músculo esquelético;músculo liso;músculo cardíaco;sarcômero;contração;força muscular;fadiga muscular"
    )),
    HumanLifeBranch("musculoskeletal_skin", "skeletal_system", "Ossos e articulações", _subs(
        "ossos;tecido ósseo;remodelação óssea;cartilagem;articulações;ligamentos;esqueleto axial;esqueleto apendicular"
    )),
    HumanLifeBranch("musculoskeletal_skin", "movement_posture", "Movimento, postura e biomecânica humana", _subs(
        "movimento;postura;alavancas;coordenação;equilíbrio;marcha;propriocepção;biomecânica"
    )),
    HumanLifeBranch("musculoskeletal_skin", "skin_integument", "Pele e sistema tegumentar", _subs(
        "pele;epiderme;derme;tecido subcutâneo;pelos;unhas;glândulas sudoríparas;barreira cutânea;termorregulação;sensibilidade"
    )),

    # Sistema nervoso e sentidos — 6
    HumanLifeBranch("nervous_sensory", "nervous_system", "Sistema nervoso", _subs(
        "sistema nervoso central;sistema nervoso periférico;neurônios;glia;sinapses;potencial de ação;neurotransmissores"
    )),
    HumanLifeBranch("nervous_sensory", "brain", "Cérebro", _subs(
        "cérebro;córtex cerebral;tálamo;hipotálamo;gânglios da base;sistema límbico;cerebelo;tronco encefálico;plasticidade neural"
    )),
    HumanLifeBranch("nervous_sensory", "spinal_peripheral_autonomic", "Medula, nervos e sistema autônomo", _subs(
        "medula espinal;nervos cranianos;nervos periféricos;sistema simpático;sistema parassimpático;reflexos;controle autonômico"
    )),
    HumanLifeBranch("nervous_sensory", "vision", "Visão", _subs(
        "olhos;córnea;cristalino;retina;fotorreceptores;nervo óptico;vias visuais;percepção visual;adaptação luminosa"
    )),
    HumanLifeBranch("nervous_sensory", "hearing_balance", "Audição e equilíbrio", _subs(
        "audição;ouvido externo;ouvido médio;ouvido interno;cóclea;células ciliadas;vias auditivas;sistema vestibular;equilíbrio"
    )),
    HumanLifeBranch("nervous_sensory", "somatosensation_pain", "Somatossensação e dor", _subs(
        "tato;pressão;temperatura;propriocepção;nocicepção;dor;modulação da dor;vias somatossensoriais"
    )),

    # Imunidade e endocrinologia — 4
    HumanLifeBranch("immune_endocrine", "immune_system", "Sistema imunológico", _subs(
        "sistema imunológico;imunidade inata;imunidade adaptativa;linfócitos;anticorpos;antígenos;memória imunológica"
    )),
    HumanLifeBranch("immune_endocrine", "inflammation_lymphatic_repair", "Inflamação, sistema linfático e reparo", _subs(
        "inflamação;sistema linfático;linfa;linfonodos;reparo tecidual;cicatrização;barreiras;resposta local"
    )),
    HumanLifeBranch("immune_endocrine", "endocrine_system", "Sistema endócrino e hormônios", _subs(
        "hormônios;hipófise;hipotálamo;tireoide;paratireoides;adrenais;pâncreas endócrino;gônadas;receptores hormonais"
    )),
    HumanLifeBranch("immune_endocrine", "endocrine_regulation", "Regulação hormonal e ritmos", _subs(
        "eixos hormonais;feedback endócrino;ritmos circadianos;cortisol;insulina;glucagon;hormônios tireoidianos;hormônios sexuais"
    )),

    # Reprodução, desenvolvimento e envelhecimento — 4
    HumanLifeBranch("reproduction_development_aging", "reproduction", "Reprodução humana", _subs(
        "reprodução;gametogênese;ovulação;ciclo reprodutivo;espermatogênese;fertilização;função reprodutiva"
    )),
    HumanLifeBranch("reproduction_development_aging", "embryology_pregnancy", "Embriologia e gestação", _subs(
        "fecundação;implantação;embrião;feto;placenta;desenvolvimento pré-natal;gestação;parto"
    )),
    HumanLifeBranch("reproduction_development_aging", "growth_development", "Crescimento, desenvolvimento e maturação", _subs(
        "desenvolvimento;infância;crescimento físico;desenvolvimento neural;desenvolvimento motor;maturação;puberdade;"
        "maturação sexual;mudanças hormonais;crescimento puberal;características sexuais;desenvolvimento corporal"
    )),
    HumanLifeBranch("reproduction_development_aging", "aging", "Envelhecimento e senescência", _subs(
        "envelhecimento;senescência;mudanças celulares;mudanças fisiológicas;reserva funcional;plasticidade ao longo da vida;longevidade"
    )),

    # Necessidades humanas, sono e fadiga — 4
    HumanLifeBranch("needs_sleep_fatigue", "sleep_circadian", "Sono e ritmos circadianos", _subs(
        "sono;vigília;ritmo circadiano;arquitetura do sono;sono REM;sono não REM;pressão homeostática do sono;recuperação"
    )),
    HumanLifeBranch("needs_sleep_fatigue", "hunger_thirst", "Fome, sede e regulação do consumo", _subs(
        "fome;saciedade;apetite;sede;hidratação;osmorregulação;sinais metabólicos;hipotálamo;balanço energético"
    )),
    HumanLifeBranch("needs_sleep_fatigue", "fatigue_recovery", "Fadiga, esforço e recuperação", _subs(
        "fadiga;fadiga muscular;fadiga central;esforço;recuperação;sono;energia;adaptação ao exercício"
    )),
    HumanLifeBranch("needs_sleep_fatigue", "human_needs", "Necessidades humanas fundamentais", _subs(
        "necessidades humanas;respiração;água;alimentação;sono;termorregulação;eliminação;movimento;repouso;segurança;conforto;interação social"
    )),

    # Higiene e prevenção básica — 3
    HumanLifeBranch("hygiene_prevention", "personal_hygiene", "Higiene pessoal", _subs(
        "higiene;mãos;pele;banho;higiene oral;dentes;cabelos;unhas;roupas;rotinas de limpeza"
    )),
    HumanLifeBranch("hygiene_prevention", "food_environment_hygiene", "Higiene alimentar, ambiental e prevenção de transmissão", _subs(
        "higiene dos alimentos;água segura;armazenamento de alimentos;limpeza de superfícies;saneamento;ventilação;ambiente;"
        "lavagem de mãos;etiqueta respiratória;barreiras;limpeza;desinfecção;vacinação como conceito imunológico;cadeia de transmissão"
    )),
    HumanLifeBranch("hygiene_prevention", "body_awareness_non_diagnostic", "Consciência corporal não diagnóstica", _subs(
        "sinais corporais;dor;fadiga;fome;sede;sono;mudanças percebidas;limites do autoconhecimento;quando buscar avaliação profissional"
    )),
)


HUMAN_LIFE_LENSES = (
    ("concept", "conceito", "definir o fenômeno, a terminologia e o nível biológico relevante"),
    ("structure", "estrutura", "descrever componentes, organização espacial e relações anatômicas"),
    ("function", "função", "explicar a função fisiológica sem inferir doença individual"),
    ("mechanism", "mecanismo", "descrever processos causais e etapas conhecidas"),
    ("metabolism", "metabolismo", "conectar energia, substratos, enzimas e fluxo metabólico quando aplicável"),
    ("regulation", "regulação", "explicar homeostase, feedback e controle neuroendócrino"),
    ("signaling", "sinalização", "descrever comunicação celular, neural, hormonal ou imune"),
    ("measurement", "medição", "indicar grandezas, métodos, unidades e variabilidade sem transformar medidas em diagnóstico"),
    ("normal_variation", "variação biológica", "registrar diversidade e faixas fisiológicas sem reduzir pessoas a um padrão único"),
    ("development", "desenvolvimento", "situar mudanças ao longo da vida e maturação"),
    ("evolution_adaptation", "evolução e adaptação", "relacionar história evolutiva, plasticidade e adaptação"),
    ("input_output", "entradas e saídas", "mapear nutrientes, gases, água, sinais, resíduos e respostas do sistema"),
    ("interaction", "interação entre sistemas", "conectar órgãos, tecidos e sistemas sem duplicar o conhecimento-base"),
    ("evidence", "evidências", "separar observação, experimento, consenso, incerteza e fonte"),
    ("limits", "limites e exceções", "registrar condições de validade, exceções e limites de generalização"),
    ("needs", "necessidades humanas", "relacionar sinais e necessidades fisiológicas sem converter necessidade em doença"),
    ("nutrition", "nutrição e hidratação", "conectar necessidades de energia, nutrientes e água de forma geral"),
    ("maintenance_hygiene", "manutenção e higiene", "descrever proteção, higiene e autocuidado básico sem prescrever tratamento"),
    ("relations", "relações e Knowledge Graph", "mapear dependências, parte-de, regula, sinaliza, protege e interage-com"),
    ("frontier", "fronteira científica", "separar consenso, hipótese ativa, resultado preliminar e lacunas de conhecimento"),
)

DEPTHS = (
    "fundamental", "basic", "intermediate", "advanced", "undergraduate",
    "graduate", "professional", "research", "specialist", "review",
)
BIOLOGICAL_SCALES = (
    "molecular", "organelle", "cell", "tissue", "organ",
    "system", "organism", "lifespan", "population", "integrated",
)
PHYSIOLOGICAL_CONTEXTS = (
    "baseline", "feeding", "fasting", "exercise", "sleep",
    "wakefulness", "stress", "recovery", "environment", "adaptation",
)
LIFE_STAGES = (
    "prenatal", "infancy", "childhood", "adolescence", "young_adult",
    "adult", "middle_age", "older_adult", "aging", "lifespan_general",
)
EVIDENCE_MODES = (
    "cellular_measurement", "physiological_measurement", "controlled_experiment", "observational_study",
    "longitudinal_study", "replication", "systematic_review", "reference_text",
    "population_evidence", "uncertain_or_frontier",
)
REPRESENTATIONS = (
    "explanation", "anatomical_schema", "process_flow", "feedback_loop", "table",
    "comparison", "worked_example", "developmental_timeline", "taxonomy", "graph_relation",
)

CANONICAL_NODES = len(HUMAN_LIFE_BRANCHES) * len(HUMAN_LIFE_LENSES)
VARIANTS_PER_NODE = (
    len(DEPTHS) * len(BIOLOGICAL_SCALES) * len(PHYSIOLOGICAL_CONTEXTS) *
    len(LIFE_STAGES) * len(EVIDENCE_MODES) * len(REPRESENTATIONS)
)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE

assert len(HUMAN_LIFE_DOMAINS) == 13
assert len(HUMAN_LIFE_BRANCHES) == 50
assert len(HUMAN_LIFE_LENSES) == 20
assert CANONICAL_NODES == 1_000
assert VARIANTS_PER_NODE == 1_000_000
assert ADDRESSABLE_CONTENTS == 1_000_000_000
assert {branch.domain for branch in HUMAN_LIFE_BRANCHES} == set(HUMAN_LIFE_DOMAINS)


REQUESTED_TOPICS = (
    "células", "tecidos", "órgãos", "organismos", "metabolismo", "reprodução", "envelhecimento",
    "evolução", "adaptação", "anatomia", "fisiologia", "cérebro", "coração", "pulmões", "digestão",
    "músculos", "ossos", "pele", "visão", "audição", "sistema nervoso", "sistema imunológico",
    "hormônios", "sono", "fome", "sede", "dor", "fadiga", "necessidades humanas", "desenvolvimento",
    "nutrição", "higiene",
)

CROSS_DOMAIN_RELATIONS = {
    "life_foundations": ("cells_tissues", "metabolism_homeostasis", "evolution_adaptation"),
    "cells_tissues": ("metabolism_homeostasis", "anatomy", "immune_endocrine"),
    "metabolism_homeostasis": ("cardiorespiratory", "digestive_nutrition", "immune_endocrine", "needs_sleep_fatigue"),
    "evolution_adaptation": ("life_foundations", "reproduction_development_aging", "needs_sleep_fatigue"),
    "anatomy": ("cardiorespiratory", "digestive_nutrition", "musculoskeletal_skin", "nervous_sensory"),
    "cardiorespiratory": ("metabolism_homeostasis", "nervous_sensory", "needs_sleep_fatigue"),
    "digestive_nutrition": ("metabolism_homeostasis", "needs_sleep_fatigue", "immune_endocrine"),
    "musculoskeletal_skin": ("nervous_sensory", "metabolism_homeostasis", "hygiene_prevention"),
    "nervous_sensory": ("immune_endocrine", "needs_sleep_fatigue", "cardiorespiratory"),
    "immune_endocrine": ("metabolism_homeostasis", "reproduction_development_aging", "nervous_sensory"),
    "reproduction_development_aging": ("immune_endocrine", "metabolism_homeostasis", "evolution_adaptation"),
    "needs_sleep_fatigue": ("nervous_sensory", "metabolism_homeostasis", "digestive_nutrition"),
    "hygiene_prevention": ("musculoskeletal_skin", "immune_endocrine", "digestive_nutrition"),
}

NEED_GUIDANCE = {
    "sleep": ("sono", "repouso e sincronização fisiológica; varia ao longo da vida e do contexto"),
    "hunger": ("fome", "sinal regulatório relacionado a disponibilidade energética, ingestão e controle neuroendócrino"),
    "thirst": ("sede", "sinal regulatório relacionado a água corporal, osmolaridade e balanço de fluidos"),
    "pain": ("dor", "experiência sensorial e afetiva protetora; intensidade e causa não podem ser diagnosticadas por este bloco"),
    "fatigue": ("fadiga", "redução percebida ou funcional de capacidade; pode depender de múltiplos sistemas e contexto"),
    "nutrition": ("nutrição", "necessidade de energia, macronutrientes, micronutrientes e água, dependente de contexto e fase da vida"),
    "hygiene": ("higiene", "práticas de limpeza e proteção que reduzem exposição e preservam barreiras corporais"),
    "breathing": ("respiração", "necessidade de ventilação e troca gasosa para sustentar metabolismo aeróbio"),
    "temperature": ("termorregulação", "manutenção de condições térmicas compatíveis com função fisiológica"),
    "recovery": ("recuperação", "restauração de reservas e adaptação após esforço, vigília ou estresse fisiológico"),
}

DIAGNOSTIC_POLICY = {
    "automatic_diagnosis": False,
    "symptom_to_disease_inference": False,
    "automatic_treatment_selection": False,
    "personal_health_profile_created": False,
    "knowledge_is_general_reference": True,
    "rule": "CONHECIMENTO BIOLÓGICO ≠ DIAGNÓSTICO AUTOMÁTICO",
}

REFERENCE_FAMILIES = (
    "BLOCO 5 / Biologia",
    "OpenStax Biology",
    "OpenStax Anatomy & Physiology",
    "NCBI Bookshelf",
    "NIH foundational physiology/neuroscience/immunology",
    "WHO/CDC public-health and hygiene foundations",
)


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return "_".join(re.findall(r"[a-z0-9]+", text))


def _decode_axes(variant_index: int) -> dict[str, str]:
    axes = (
        ("depth", DEPTHS),
        ("biological_scale", BIOLOGICAL_SCALES),
        ("physiological_context", PHYSIOLOGICAL_CONTEXTS),
        ("life_stage", LIFE_STAGES),
        ("evidence_mode", EVIDENCE_MODES),
        ("representation", REPRESENTATIONS),
    )
    remainder = int(variant_index)
    decoded: dict[str, str] = {}
    for name, values in reversed(axes):
        remainder, index = divmod(remainder, len(values))
        decoded[name] = values[index]
    if remainder:
        raise IndexError(variant_index)
    return decoded


class HumanLifeCatalog:
    """Catálogo B06 de 1B representações sobre vida/corpo, geradas sob demanda."""

    NAMESPACE = "B06"

    def stats(self) -> dict:
        counts = {domain: 0 for domain in HUMAN_LIFE_DOMAINS}
        for branch in HUMAN_LIFE_BRANCHES:
            counts[branch.domain] += 1
        return {
            "namespace": self.NAMESPACE,
            "domains": len(HUMAN_LIFE_DOMAINS),
            "domain_branch_counts": counts,
            "branches": len(HUMAN_LIFE_BRANCHES),
            "lenses_per_branch": len(HUMAN_LIFE_LENSES),
            "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS,
            "materialization": "on-demand",
            "prepopulated_knowledge_rows": 0,
            "truthfulness_note": (
                "1B são representações combinatórias de conhecimento biológico/humano; "
                "não 1B de fatos médicos independentes nem perfis de saúde pessoais"
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
        return f"LIFE-B06-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"LIFE-B06-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, len(HUMAN_LIFE_LENSES))
        branch = HUMAN_LIFE_BRANCHES[branch_index]
        lens_key, lens_label, instruction = HUMAN_LIFE_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {
            "id": f"LIFE-B06-{absolute:010d}",
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
                f"Profundidade={axes['depth']}; escala={axes['biological_scale']}; "
                f"contexto fisiológico={axes['physiological_context']}; fase da vida={axes['life_stage']}; "
                f"evidência={axes['evidence_mode']}; representação={axes['representation']}. "
                "Separar conhecimento geral de informação pessoal e nunca converter sinais em diagnóstico automático."
            ),
        }


class HumanLifeFoundations:
    """Camada B06 integrada a ciência, conhecimento universal e grafo compartilhado."""

    NAMESPACE = "B06"
    TAXONOMY_ROOT_ID = "LIFE-TAX-ROOT"

    def __init__(self, knowledge: UniversalKnowledgeArchitecture, *, scientific_foundations=None):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.scientific_foundations = scientific_foundations
        self.catalog = HumanLifeCatalog()
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 6 — VIDA, CORPO E NECESSIDADES HUMANAS",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/human_life.py",
            metadata={
                "materialization": "on-demand",
                "role": "human-life-body-foundations",
                "canonical_gate": "BLOCO 2 -> BLOCO 3",
                "scientific_foundation": "BLOCO 5",
                "knowledge_graph": "shared",
                "automatic_diagnosis": False,
                "personal_health_profile_created": False,
            },
        )

    @staticmethod
    def _domain_key(value: str) -> str:
        normalized = _norm(value)
        aliases = {
            "vida": "life_foundations", "life": "life_foundations", "organismos": "life_foundations",
            "celulas": "cells_tissues", "tecidos": "cells_tissues", "orgaos": "cells_tissues",
            "metabolismo": "metabolism_homeostasis", "homeostase": "metabolism_homeostasis", "fisiologia": "metabolism_homeostasis",
            "evolucao": "evolution_adaptation", "adaptacao": "evolution_adaptation",
            "anatomia": "anatomy",
            "coracao": "cardiorespiratory", "pulmoes": "cardiorespiratory", "respiracao": "cardiorespiratory",
            "digestao": "digestive_nutrition", "nutricao": "digestive_nutrition",
            "musculos": "musculoskeletal_skin", "ossos": "musculoskeletal_skin", "pele": "musculoskeletal_skin",
            "cerebro": "nervous_sensory", "sistema_nervoso": "nervous_sensory", "visao": "nervous_sensory", "audicao": "nervous_sensory", "dor": "nervous_sensory",
            "imunidade": "immune_endocrine", "sistema_imunologico": "immune_endocrine", "hormonios": "immune_endocrine",
            "reproducao": "reproduction_development_aging", "desenvolvimento": "reproduction_development_aging", "envelhecimento": "reproduction_development_aging",
            "sono": "needs_sleep_fatigue", "fome": "needs_sleep_fatigue", "sede": "needs_sleep_fatigue", "fadiga": "needs_sleep_fatigue", "necessidades_humanas": "needs_sleep_fatigue",
            "higiene": "hygiene_prevention",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _branch(key: str) -> HumanLifeBranch:
        for branch in HUMAN_LIFE_BRANCHES:
            if branch.key == key:
                return branch
        raise KeyError(key)

    @staticmethod
    def _domain_node_id(domain: str) -> str:
        return f"LIFE-DOM-{domain.upper()}"

    @staticmethod
    def _branch_node_id(branch: str) -> str:
        return f"LIFE-BR-{branch.upper()}"

    @staticmethod
    def _subtopic_node_id(branch: str, subtopic: str) -> str:
        return f"LIFE-SUB-{branch.upper()}-{_norm(subtopic).upper()[:80]}"

    def taxonomy_snapshot(self, domain: str | None = None) -> dict:
        domain_key = self._domain_key(domain) if domain else None
        if domain_key and domain_key not in HUMAN_LIFE_DOMAINS:
            raise KeyError(domain)
        selected = [b for b in HUMAN_LIFE_BRANCHES if domain_key is None or b.domain == domain_key]
        return {
            "root": "Vida, Corpo e Necessidades Humanas",
            "domain": domain_key,
            "branches": [
                {
                    "domain": branch.domain,
                    "domain_label": DOMAIN_LABELS[branch.domain],
                    "branch": branch.key,
                    "branch_label": branch.label,
                    "subtopics": list(branch.subtopics),
                }
                for branch in selected
            ],
            "cross_domain_relations": deepcopy(CROSS_DOMAIN_RELATIONS),
            "diagnostic_policy": deepcopy(DIAGNOSTIC_POLICY),
        }

    def _ensure_taxonomy_path(self, branch: HumanLifeBranch, *, include_subtopics: bool = True) -> dict:
        root = self.graph.add_entity(
            "human_life_taxonomy", "Vida, Corpo e Necessidades Humanas", node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B06", "diagnostic": False, "source_of_truth": "core/human_life.py"},
        )
        science_biology = "SCI-DOM-BIOLOGY"
        self.graph.add_entity(
            "science_domain", "Biologia", node_id=science_biology,
            data={"block": "B05", "domain": "biology"},
        )
        self.graph.relate(root, science_biology, "refines", metadata={"block": "B06", "source_block": "B05"})
        self.graph.relate(science_biology, root, "related_to", metadata={"block": "B06", "specialization": True})

        domain_id = self._domain_node_id(branch.domain)
        self.graph.add_entity(
            "human_life_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id,
            data={"block": "B06", "domain": branch.domain, "diagnostic": False},
        )
        self.graph.relate(root, domain_id, "has_part", metadata={"block": "B06", "taxonomy": True})
        self.graph.relate(domain_id, root, "part_of", metadata={"block": "B06", "taxonomy": True})

        branch_id = self._branch_node_id(branch.key)
        self.graph.add_entity(
            "human_life_branch", branch.label, node_id=branch_id,
            data={"block": "B06", "domain": branch.domain, "branch": branch.key, "diagnostic": False},
        )
        self.graph.relate(domain_id, branch_id, "has_part", metadata={"block": "B06", "taxonomy": True})
        self.graph.relate(branch_id, domain_id, "part_of", metadata={"block": "B06", "taxonomy": True})

        sub_ids = []
        if include_subtopics:
            for subtopic in branch.subtopics:
                sub_id = self._subtopic_node_id(branch.key, subtopic)
                self.graph.add_entity(
                    "human_life_subtopic", subtopic, node_id=sub_id,
                    data={"block": "B06", "domain": branch.domain, "branch": branch.key},
                )
                self.graph.relate(branch_id, sub_id, "has_part", metadata={"block": "B06", "taxonomy": True})
                self.graph.relate(sub_id, branch_id, "part_of", metadata={"block": "B06", "taxonomy": True})
                sub_ids.append(sub_id)
        return {"root_id": root, "domain_id": domain_id, "branch_id": branch_id, "subtopic_ids": sub_ids}

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        domain_key = self._domain_key(domain) if domain else None
        if domain_key and domain_key not in HUMAN_LIFE_DOMAINS:
            raise KeyError(domain)
        selected = [b for b in HUMAN_LIFE_BRANCHES if domain_key is None or b.domain == domain_key]
        paths = [self._ensure_taxonomy_path(branch) for branch in selected]
        return {
            "domain": domain_key,
            "branches_materialized": len(paths),
            "knowledge_graph": "shared",
            "diagnostic_engine_created": False,
            "paths": paths,
        }

    def reference(self, query: str) -> dict | None:
        """Reusa a ciência existente; não canoniza nem diagnostica a partir da resposta."""
        query = _clean(query)
        if not query:
            return None
        if self.scientific_foundations is None:
            return None
        result = self.scientific_foundations.reference(query, domain="biology")
        if not result:
            return None
        return {
            **result,
            "block": "B06",
            "diagnostic": False,
            "canonicalized": False,
            "note": "referência científica geral reutilizada do BLOCO 5; não é diagnóstico individual",
        }

    def contextualize_need(self, need: str, *, context: str = "") -> dict:
        """Explica uma necessidade/sinal sem produzir hipótese diagnóstica."""
        key = _norm(need)
        aliases = {
            "sono": "sleep", "sleep": "sleep",
            "fome": "hunger", "hunger": "hunger",
            "sede": "thirst", "thirst": "thirst",
            "dor": "pain", "pain": "pain",
            "fadiga": "fatigue", "fatigue": "fatigue",
            "nutricao": "nutrition", "nutrition": "nutrition",
            "higiene": "hygiene", "hygiene": "hygiene",
            "respiracao": "breathing", "breathing": "breathing",
            "temperatura": "temperature", "termorregulacao": "temperature",
            "recuperacao": "recovery", "recovery": "recovery",
        }
        canonical = aliases.get(key)
        if canonical not in NEED_GUIDANCE:
            raise KeyError(need)
        label, role = NEED_GUIDANCE[canonical]
        return {
            "need": canonical,
            "label": label,
            "physiological_role": role,
            "context": _clean(context),
            "diagnosis": None,
            "disease_candidates": [],
            "disease_inference_performed": False,
            "treatment_selected": False,
            "policy": deepcopy(DIAGNOSTIC_POLICY),
            "note": "contexto fisiológico geral; sinais persistentes, intensos ou preocupantes exigem avaliação apropriada fora deste bloco",
        }

    def promote_canonical_human_knowledge(
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
        """Materializa apenas conhecimento geral já CANONICAL; nunca perfis pessoais."""
        domain_key = self._domain_key(domain)
        if domain_key not in HUMAN_LIFE_DOMAINS:
            raise ValueError(f"domínio B06 inválido: {domain}")
        branch_obj = self._branch(branch)
        if branch_obj.domain != domain_key:
            raise ValueError(f"ramo {branch} não pertence a {domain_key}")
        props = dict(properties or {})
        props.update({
            "diagnostic_use": False,
            "personal_health_profile": False,
            "knowledge_scope": "general_human_biology",
        })
        result = self.knowledge.promote_canonical(
            record_id,
            canonical_label,
            knowledge_type=knowledge_type,
            namespace=self.NAMESPACE,
            summary=summary,
            aliases=aliases,
            properties=props,
            categories=["life", "human_body", domain_key, branch_obj.key],
            subtopics=subtopics,
            contexts=contexts,
            rules=rules,
            exceptions=exceptions,
            provenance={
                "human_life_block": "B06",
                "scientific_foundation": "B05",
                "domain": domain_key,
                "branch": branch_obj.key,
                "source_record_id": record_id,
                "diagnostic": False,
            },
        )
        taxonomy = self._ensure_taxonomy_path(branch_obj, include_subtopics=False)
        self.graph.relate(
            result["knowledge_id"], taxonomy["branch_id"], "is_a",
            metadata={"block": "B06", "human_life_taxonomy": True, "diagnostic": False},
        )
        self.graph.relate(
            taxonomy["branch_id"], result["knowledge_id"], "has_part",
            metadata={"block": "B06", "human_life_taxonomy": True, "diagnostic": False},
        )
        return result

    def relate(self, source_id: str, target_id: str, relation: str, *, weight: float = 1.0) -> dict:
        return self.knowledge.relate(
            source_id, target_id, relation, weight=weight,
            metadata={"block": "B06", "human_life": True, "diagnostic": False},
        )

    def policy(self) -> dict:
        return deepcopy(DIAGNOSTIC_POLICY)

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "domains": [{"key": key, "label": DOMAIN_LABELS[key]} for key in HUMAN_LIFE_DOMAINS],
            "lenses": [{"key": key, "label": label} for key, label, _ in HUMAN_LIFE_LENSES],
            "knowledge_graph": "shared knowledge_nodes/knowledge_edges",
            "canonical_knowledge": "BLOCO 2 gate -> BLOCO 3 -> B06",
            "scientific_foundation": "BLOCO 5 reused",
            "reference_families": list(REFERENCE_FAMILIES),
            "diagnostic_policy": self.policy(),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None

        if low in {
            "status bloco 6", "status vida e corpo", "status corpo humano",
            "vida corpo e necessidades humanas", "fundamentos da vida humana",
        }:
            stats = self.stats()
            return (
                "🧬 BLOCO 6 — VIDA, CORPO E NECESSIDADES HUMANAS: "
                f"{stats['catalog']['addressable_contents']} conteúdos endereçáveis em B06 | "
                f"{stats['catalog']['domains']} domínios × {stats['catalog']['branches']} ramos × "
                f"{stats['catalog']['lenses_per_branch']} lentes = {stats['catalog']['canonical_nodes']} nós | "
                "Knowledge Graph=COMPARTILHADO | diagnóstico automático=DESATIVADO."
            )

        item = self.catalog.get_variant(raw.upper())
        if item:
            return (
                f"🧬 {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n"
                f"{item['prompt']}"
            )

        taxonomy = re.match(r"^(?:taxonomia vida|taxonomia corpo humano)(?:\s+(.+))?$", raw, re.I)
        if taxonomy:
            snapshot = self.taxonomy_snapshot(taxonomy.group(1))
            labels = ", ".join(branch["branch_label"] for branch in snapshot["branches"][:12])
            suffix = "…" if len(snapshot["branches"]) > 12 else ""
            return f"🧬 Taxonomia B06: {len(snapshot['branches'])} ramos. {labels}{suffix}"

        need = re.match(r"^(?:necessidade humana|contextualizar necessidade)\s+(.+)$", raw, re.I)
        if need:
            result = self.contextualize_need(need.group(1).strip())
            return (
                f"🧬 {result['label'].title()}: {result['physiological_role']}. "
                "Isto é contexto fisiológico geral e não diagnóstico."
            )

        if re.match(r"^(?:diagnostico automatico|diagnóstico automático)(?:\s+bloco 6)?$", raw, re.I):
            return (
                "🛡️ BLOCO 6 não possui diagnóstico automático. Conhecimento biológico, sinais corporais e necessidades "
                "não são convertidos automaticamente em doenças ou tratamentos."
            )

        return None
