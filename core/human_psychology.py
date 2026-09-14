"""BLOCO 7 — Mente Humana e Psicologia da STAR.

Organiza conhecimento psicológico e comportamental geral sobre o mesmo BLOCO 2,
BLOCO 3 e Knowledge Graph. Reutiliza BLOCO 6 e a base multidisciplinar existente.

Regra permanente:
COMPORTAMENTO ISOLADO != DIAGNOSTICO, TRACO ESTAVEL, INTENCAO OU CERTEZA.

Escala: 50 ramos x 20 lentes = 1.000 nos; 1.000.000 variacoes/no = 1B
enderecaveis em B07, sempre materializados sob demanda.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
import unicodedata
from typing import Any

from core.universal_knowledge import UniversalKnowledgeArchitecture


@dataclass(frozen=True)
class PsychologyBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in raw.split(";") if x.strip())


PSYCHOLOGY_DOMAINS = (
    "perception_attention", "memory_learning", "motivation_habits", "emotion_regulation",
    "personality_identity_self", "cognition_decision_bias", "stress_trauma_grief",
    "behavior_expression_intention", "theory_of_mind_social_cognition", "relationships_attachment",
    "development_context", "research_measurement_interpretation", "psychological_needs_adaptation",
)

DOMAIN_LABELS = {
    "perception_attention": "Percepção e atenção",
    "memory_learning": "Memória humana e aprendizagem",
    "motivation_habits": "Motivação e hábitos",
    "emotion_regulation": "Emoções e regulação",
    "personality_identity_self": "Personalidade, identidade e self",
    "cognition_decision_bias": "Cognição, decisões e vieses",
    "stress_trauma_grief": "Estresse, trauma e luto",
    "behavior_expression_intention": "Comportamento, expressões e intenção",
    "theory_of_mind_social_cognition": "Teoria da mente e cognição social",
    "relationships_attachment": "Relações psicológicas e apego",
    "development_context": "Desenvolvimento e contexto",
    "research_measurement_interpretation": "Pesquisa, medição e interpretação psicológica",
    "psychological_needs_adaptation": "Necessidades psicológicas, adaptação e bem-estar",
}

PSYCHOLOGY_BRANCHES = (
    PsychologyBranch("perception_attention", "sensory_perception", "Percepção sensorial", _subs("percepção;processamento sensorial;detecção;discriminação;limiares;integração multissensorial;constâncias perceptivas")),
    PsychologyBranch("perception_attention", "perceptual_organization", "Organização e interpretação perceptiva", _subs("organização perceptiva;figura-fundo;Gestalt;profundidade;movimento;expectativas;contexto perceptivo;ilusões")),
    PsychologyBranch("perception_attention", "attention_systems", "Atenção e seleção", _subs("atenção;atenção seletiva;atenção sustentada;atenção dividida;orientação;vigilância;controle atencional")),
    PsychologyBranch("perception_attention", "attention_limits", "Limites, distração e carga atencional", _subs("carga cognitiva;distração;interferência;piscar atencional;cegueira por desatenção;fadiga atencional;multitarefa")),

    PsychologyBranch("memory_learning", "memory_systems", "Sistemas de memória humana", _subs("memória humana;memória de trabalho;memória episódica;memória semântica;memória procedural;memória prospectiva")),
    PsychologyBranch("memory_learning", "encoding_retrieval", "Codificação, consolidação e recuperação", _subs("codificação;consolidação;recuperação;pistas;reconhecimento;recordação;esquecimento;interferência")),
    PsychologyBranch("memory_learning", "learning_mechanisms", "Mecanismos de aprendizagem", _subs("aprendizagem;condicionamento clássico;condicionamento operante;aprendizagem observacional;reforço;extinção;generalização")),
    PsychologyBranch("memory_learning", "skill_knowledge_learning", "Aquisição de habilidades e conhecimento", _subs("prática;feedback;automatização;transferência;aprendizagem espaçada;recuperação ativa;metacognição;erro e correção")),

    PsychologyBranch("motivation_habits", "motivation", "Motivação e direção do comportamento", _subs("motivação;metas;incentivos;valor esperado;persistência;esforço;motivação intrínseca;motivação extrínseca")),
    PsychologyBranch("motivation_habits", "needs_drives", "Necessidades, impulsos e autorregulação", _subs("necessidades psicológicas;autonomia;competência;pertencimento;impulsos;autorregulação;adiamento de gratificação")),
    PsychologyBranch("motivation_habits", "habit_formation", "Formação e manutenção de hábitos", _subs("hábitos;gatilho;rotina;recompensa;automaticidade;repetição;contexto;substituição de hábito")),
    PsychologyBranch("motivation_habits", "goal_pursuit", "Metas, intenção de ação e persistência", _subs("formação de metas;planejamento;implementação de intenção;monitoramento;progresso;fracasso;reengajamento")),

    PsychologyBranch("emotion_regulation", "emotion_processes", "Processos emocionais", _subs("emoções;afeto;valência;ativação;avaliação;resposta corporal;experiência subjetiva;expressão emocional")),
    PsychologyBranch("emotion_regulation", "emotion_theories", "Teorias e interpretações da emoção", _subs("teorias da emoção;avaliação cognitiva;construção psicológica;emoções básicas;contexto cultural;interpretações concorrentes")),
    PsychologyBranch("emotion_regulation", "emotion_regulation", "Regulação emocional", _subs("regulação emocional;reavaliação;supressão;aceitação;distração;ruminação;coping;flexibilidade regulatória")),
    PsychologyBranch("emotion_regulation", "emotional_expression", "Expressões e comunicação emocional", _subs("expressões;expressão facial;prosódia;postura;gestos;congruência;mascaramento;regras culturais de exibição")),

    PsychologyBranch("personality_identity_self", "personality", "Personalidade e diferenças individuais", _subs("personalidade;traços;Big Five;temperamento;estabilidade;mudança;diferenças individuais;contexto")),
    PsychologyBranch("personality_identity_self", "self_concept", "Autoconceito e identidade", _subs("identidade;autoconceito;papéis;identidade social;continuidade pessoal;narrativas de si;contexto cultural")),
    PsychologyBranch("personality_identity_self", "self_esteem", "Autoestima e autoavaliação", _subs("autoestima;autoeficácia;autocompaixão;autovalor;comparação social;feedback;variabilidade situacional")),
    PsychologyBranch("personality_identity_self", "identity_development", "Desenvolvimento e mudança da identidade", _subs("exploração;compromisso;transições;pertencimento;mudança de papéis;identidade ao longo da vida")),

    PsychologyBranch("cognition_decision_bias", "cognition", "Cognição e processamento de informação", _subs("cognição;representações mentais;conceitos;categorização;raciocínio;resolução de problemas;metacognição")),
    PsychologyBranch("cognition_decision_bias", "judgment_decision", "Julgamento e tomada de decisão", _subs("decisões;julgamento;escolha;preferências;risco;incerteza;valor;trade-offs;decisão sob pressão")),
    PsychologyBranch("cognition_decision_bias", "heuristics_biases", "Heurísticas e vieses cognitivos", _subs("vieses;heurísticas;ancoragem;disponibilidade;representatividade;confirmação;aversão à perda;excesso de confiança")),
    PsychologyBranch("cognition_decision_bias", "reasoning_errors", "Erros de raciocínio e interpretação", _subs("falácias informais;correlação e causalidade;taxa-base;conjunção;retrospectiva;atribuição;generalização")),
    PsychologyBranch("cognition_decision_bias", "decision_context", "Contexto, enquadramento e arquitetura de escolha", _subs("framing;efeito padrão;ordem;contexto social;pressão temporal;informação incompleta;fadiga decisória")),

    PsychologyBranch("stress_trauma_grief", "stress", "Estresse e resposta adaptativa", _subs("estresse;estressores;avaliação de ameaça;coping;resposta aguda;estresse crônico;recuperação;resiliência")),
    PsychologyBranch("stress_trauma_grief", "trauma", "Trauma como fenômeno psicológico geral", _subs("trauma;experiência potencialmente traumática;respostas pós-evento;memória;evitação;hipervigilância;variação individual;recuperação")),
    PsychologyBranch("stress_trauma_grief", "grief", "Luto, perda e adaptação", _subs("luto;perda;vínculo;saudade;adaptação;continuidade de vínculo;rituais;diferenças culturais;trajetórias diversas")),
    PsychologyBranch("stress_trauma_grief", "resilience_coping", "Resiliência, coping e recuperação", _subs("resiliência;coping focado no problema;coping focado na emoção;apoio social;flexibilidade;recursos;significado")),

    PsychologyBranch("behavior_expression_intention", "behavior_analysis", "Comportamento observável e contexto", _subs("comportamento;antecedentes;consequências;contexto;situação;frequência;variabilidade;aprendizagem;função possível")),
    PsychologyBranch("behavior_expression_intention", "nonverbal_expression", "Expressões não verbais", _subs("expressões;rosto;olhar;gestos;postura;distância interpessoal;prosódia;sincronia;contexto cultural")),
    PsychologyBranch("behavior_expression_intention", "intention_inference", "Intenção e limites de inferência", _subs("intenção;objetivos;planos;declarações;ações;ambiguidade;atribuição de intenção;alternativas plausíveis")),
    PsychologyBranch("behavior_expression_intention", "behavior_context", "Comportamento situacional e padrões", _subs("padrões comportamentais;situação;papéis;normas;hábitos;estado emocional;pressões sociais;mudança ao longo do tempo")),

    PsychologyBranch("theory_of_mind_social_cognition", "theory_of_mind", "Teoria da mente", _subs("teoria da mente;crenças;desejos;perspectivas;falsa crença;estados mentais;inferência social;incerteza")),
    PsychologyBranch("theory_of_mind_social_cognition", "social_perception", "Percepção social", _subs("percepção social;impressões;categorias sociais;atribuição;primeiras impressões;estereótipos;contexto")),
    PsychologyBranch("theory_of_mind_social_cognition", "empathy_perspective", "Empatia e tomada de perspectiva", _subs("empatia;tomada de perspectiva;compaixão;contágio emocional;limites da empatia;diferenças individuais")),
    PsychologyBranch("theory_of_mind_social_cognition", "attribution", "Atribuição e explicação de comportamento", _subs("atribuição;causas situacionais;causas disposicionais;erro fundamental de atribuição;viés ator-observador")),

    PsychologyBranch("relationships_attachment", "attachment", "Apego e vínculos", _subs("apego;vínculo;segurança;proximidade;separação;modelos internos;desenvolvimento;variação relacional")),
    PsychologyBranch("relationships_attachment", "interpersonal_relations", "Relações interpessoais", _subs("relações psicológicas;reciprocidade;confiança;intimidade;limites;conflito;cooperação;reparação")),
    PsychologyBranch("relationships_attachment", "communication", "Comunicação e interpretação interpessoal", _subs("comunicação;escuta;mensagem;feedback;mal-entendidos;metacomunicação;contexto;diferenças culturais")),
    PsychologyBranch("relationships_attachment", "groups_belonging", "Grupos, pertencimento e influência social", _subs("pertencimento;normas;conformidade;influência social;identidade de grupo;cooperação;polarização;status")),

    PsychologyBranch("development_context", "lifespan_development", "Desenvolvimento psicológico ao longo da vida", _subs("desenvolvimento;infância;adolescência;adulto;envelhecimento;mudança cognitiva;mudança emocional;transições")),
    PsychologyBranch("development_context", "socialization_family", "Socialização, família e ambientes próximos", _subs("socialização;família;cuidadores;pares;escola;modelagem;normas;apoio;conflito")),
    PsychologyBranch("development_context", "culture_context", "Cultura e contexto psicológico", _subs("cultura;normas;valores;individualismo;coletivismo;linguagem;significados;contexto histórico;diversidade")),
    PsychologyBranch("development_context", "environment_behavior", "Ambiente, situação e comportamento", _subs("ambiente;espaço;ruído;densidade;rotina;tecnologia;contexto social;estressores ambientais;design comportamental")),

    PsychologyBranch("research_measurement_interpretation", "research_methods", "Métodos de pesquisa em psicologia", _subs("experimentos;estudos observacionais;longitudinais;transversais;amostragem;randomização;replicação;pré-registro")),
    PsychologyBranch("research_measurement_interpretation", "psychometrics", "Psicometria e medição", _subs("psicometria;confiabilidade;validade;escalas;questionários;testes;viés de medida;invariância;normas")),
    PsychologyBranch("research_measurement_interpretation", "interpretation_limits", "Interpretação, causalidade e limites", _subs("interpretação;contextos;possibilidades;exceções;interpretações alternativas;incerteza;causalidade;generalização;replicabilidade")),

    PsychologyBranch("psychological_needs_adaptation", "psychological_needs", "Necessidades psicológicas e bem-estar", _subs("necessidades psicológicas;pertencimento;autonomia;competência;segurança psicológica;sentido;conexão;descanso")),
    PsychologyBranch("psychological_needs_adaptation", "adaptation_wellbeing", "Adaptação, flexibilidade e bem-estar", _subs("adaptação;flexibilidade psicológica;recuperação;apoio social;rotinas;propósito;bem-estar;qualidade de vida")),
)

PSYCHOLOGY_LENSES = (
    ("concept", "conceito", "definir o fenômeno e distinguir termos próximos"),
    ("components", "componentes", "descrever componentes, processos e relações internas"),
    ("mechanism", "mecanismo", "explicar mecanismos propostos sem convertê-los em certeza individual"),
    ("development", "desenvolvimento", "situar mudanças ao longo da vida e experiência"),
    ("context", "contexto", "mostrar como situação, ambiente e história alteram interpretação"),
    ("culture", "cultura", "considerar normas culturais e evitar universalização indevida"),
    ("individual_differences", "diferenças individuais", "preservar variabilidade entre pessoas"),
    ("evidence", "evidências", "separar observação, correlação, experimento, síntese e incerteza"),
    ("measurement", "medição", "explicar medidas, validade, confiabilidade e limitações"),
    ("possibilities", "possibilidades", "listar hipóteses plausíveis sem escolher uma como certeza"),
    ("alternative_interpretations", "interpretações alternativas", "apresentar leituras concorrentes compatíveis com a evidência"),
    ("exceptions", "exceções", "mostrar casos-limite, heterogeneidade e quando generalizações falham"),
    ("biases", "vieses", "avaliar vieses cognitivos, do observador, amostra e medição"),
    ("behavior", "comportamento", "descrever padrões observáveis sem diagnosticar ou rotular"),
    ("expression", "expressões", "interpretar sinais expressivos como ambíguos e dependentes de contexto"),
    ("intention", "intenção", "distinguir ação observável de intenção não observada"),
    ("relationships", "relações", "mapear interações, reciprocidade, papéis e influência social"),
    ("applications", "aplicações", "conectar conhecimento a educação, comunicação e autorregulação não clínica"),
    ("limits", "limites", "declarar o que os dados permitem e o que não permitem concluir"),
    ("frontier", "fronteira e debate", "separar consenso, teorias concorrentes, debate ativo e lacunas"),
)

CONTEXTS = ("individual", "interpersonal", "family", "school", "work", "digital", "cultural", "group", "high_stress", "everyday")
PERSPECTIVES = ("cognitive", "behavioral", "social", "developmental", "biological", "learning", "personality", "cultural", "systems", "integrative")
EVIDENCE_MODES = ("direct_observation", "self_report", "behavioral_task", "experiment", "longitudinal", "correlational", "psychometric", "meta_analysis", "qualitative", "uncertain")
TIMESCALES = ("moment", "minutes_hours", "day", "days_weeks", "months", "years", "developmental_stage", "life_transition", "repeated_pattern", "lifespan")
CONFIDENCE_BANDS = ("very_low", "low", "limited", "tentative", "moderate", "moderate_high", "high_for_general_pattern", "context_dependent", "conflicting", "unknown")
REPRESENTATIONS = ("explanation", "comparison", "case_variants", "evidence_table", "process_flow", "context_matrix", "alternative_hypotheses", "exception_map", "timeline", "graph_relation")

CANONICAL_NODES = len(PSYCHOLOGY_BRANCHES) * len(PSYCHOLOGY_LENSES)
VARIANTS_PER_NODE = len(CONTEXTS) * len(PERSPECTIVES) * len(EVIDENCE_MODES) * len(TIMESCALES) * len(CONFIDENCE_BANDS) * len(REPRESENTATIONS)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE

assert len(PSYCHOLOGY_DOMAINS) == 13
assert len(PSYCHOLOGY_BRANCHES) == 50
assert len(PSYCHOLOGY_LENSES) == 20
assert CANONICAL_NODES == 1_000
assert VARIANTS_PER_NODE == 1_000_000
assert ADDRESSABLE_CONTENTS == 1_000_000_000
assert {x.domain for x in PSYCHOLOGY_BRANCHES} == set(PSYCHOLOGY_DOMAINS)

REQUESTED_TOPICS = (
    "percepção", "atenção", "memória humana", "aprendizagem", "motivação", "emoções", "personalidade",
    "cognição", "hábitos", "decisões", "vieses", "trauma", "estresse", "luto", "identidade", "autoestima",
    "comportamento", "expressões", "intenção", "teoria da mente", "relações psicológicas",
)

INTERPRETATION_POLICY = {
    "isolated_behavior_is_diagnosis": False,
    "isolated_behavior_is_stable_trait": False,
    "expression_is_intention": False,
    "inferred_intention_is_certainty": False,
    "automatic_mental_disorder_inference": False,
    "automatic_personality_label": False,
    "personal_psychological_profile_created": False,
    "single_observation_is_pattern": False,
    "rule": "COMPORTAMENTO ISOLADO != DIAGNOSTICO, TRACO ESTAVEL, INTENCAO OU CERTEZA",
}

CROSS_DOMAIN_RELATIONS = {
    "perception_attention": ("memory_learning", "cognition_decision_bias", "behavior_expression_intention"),
    "memory_learning": ("perception_attention", "motivation_habits", "stress_trauma_grief"),
    "motivation_habits": ("emotion_regulation", "cognition_decision_bias", "psychological_needs_adaptation"),
    "emotion_regulation": ("stress_trauma_grief", "relationships_attachment", "behavior_expression_intention"),
    "personality_identity_self": ("development_context", "relationships_attachment", "cognition_decision_bias"),
    "cognition_decision_bias": ("perception_attention", "theory_of_mind_social_cognition", "research_measurement_interpretation"),
    "stress_trauma_grief": ("emotion_regulation", "memory_learning", "psychological_needs_adaptation"),
    "behavior_expression_intention": ("theory_of_mind_social_cognition", "relationships_attachment", "cognition_decision_bias"),
    "theory_of_mind_social_cognition": ("relationships_attachment", "behavior_expression_intention", "development_context"),
    "relationships_attachment": ("emotion_regulation", "personality_identity_self", "development_context"),
    "development_context": ("personality_identity_self", "memory_learning", "relationships_attachment"),
    "research_measurement_interpretation": ("cognition_decision_bias", "development_context", "theory_of_mind_social_cognition"),
    "psychological_needs_adaptation": ("motivation_habits", "emotion_regulation", "stress_trauma_grief"),
}

REFERENCE_FAMILIES = (
    "BLOCO 6 / cérebro, sistema nervoso e necessidades humanas",
    "Psicologia e Sociologia / core.multidisciplinary_knowledge",
    "OpenStax Psychology 2e", "APA educational/research foundations", "WHO mental-health literacy references",
)


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return "_".join(re.findall(r"[a-z0-9]+", text))


def _decode_axes(variant_index: int) -> dict[str, str]:
    axes = (("context", CONTEXTS), ("perspective", PERSPECTIVES), ("evidence_mode", EVIDENCE_MODES), ("timescale", TIMESCALES), ("confidence_band", CONFIDENCE_BANDS), ("representation", REPRESENTATIONS))
    remainder = int(variant_index)
    decoded: dict[str, str] = {}
    for name, values in reversed(axes):
        remainder, index = divmod(remainder, len(values))
        decoded[name] = values[index]
    if remainder:
        raise IndexError(variant_index)
    return decoded


class PsychologyCatalog:
    NAMESPACE = "B07"

    def stats(self) -> dict:
        counts = {domain: 0 for domain in PSYCHOLOGY_DOMAINS}
        for branch in PSYCHOLOGY_BRANCHES:
            counts[branch.domain] += 1
        return {"namespace": self.NAMESPACE, "domains": len(PSYCHOLOGY_DOMAINS), "domain_branch_counts": counts, "branches": len(PSYCHOLOGY_BRANCHES), "lenses_per_branch": len(PSYCHOLOGY_LENSES), "canonical_nodes": CANONICAL_NODES, "variants_per_node": VARIANTS_PER_NODE, "addressable_contents": ADDRESSABLE_CONTENTS, "materialization": "on-demand", "prepopulated_knowledge_rows": 0, "truthfulness_note": "1B são representações combinatórias de psicologia/comportamento geral, não diagnósticos, perfis pessoais, intenções certas ou fatos independentes"}

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        if not 0 <= int(node_index) < CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= int(variant_index) < VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = int(node_index) * VARIANTS_PER_NODE + int(variant_index) + 1
        return f"PSY-B07-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"PSY-B07-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, len(PSYCHOLOGY_LENSES))
        branch = PSYCHOLOGY_BRANCHES[branch_index]
        lens_key, lens_label, instruction = PSYCHOLOGY_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {"id": f"PSY-B07-{absolute:010d}", "namespace": self.NAMESPACE, "domain": branch.domain, "domain_label": DOMAIN_LABELS[branch.domain], "branch": branch.key, "branch_label": branch.label, "subtopics": branch.subtopics, "lens": lens_key, "lens_label": lens_label, **axes, "prompt": f"{DOMAIN_LABELS[branch.domain]} / {branch.label} / {lens_label}: {instruction}. Contexto={axes['context']}; perspectiva={axes['perspective']}; evidência={axes['evidence_mode']}; escala temporal={axes['timescale']}; confiança={axes['confidence_band']}; representação={axes['representation']}. Preservar contexto, possibilidades, exceções e interpretações alternativas. Nunca converter comportamento isolado em diagnóstico, traço estável, intenção ou certeza."}


class HumanPsychologyFoundations:
    NAMESPACE = "B07"
    TAXONOMY_ROOT_ID = "PSY-TAX-ROOT"

    def __init__(self, knowledge: UniversalKnowledgeArchitecture, *, human_life=None, multidisciplinary=None):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.human_life = human_life
        self.multidisciplinary = multidisciplinary
        self.catalog = PsychologyCatalog()
        self._providers: dict[str, Any] = {}
        self.knowledge.register_namespace(self.NAMESPACE, "BLOCO 7 — MENTE HUMANA E PSICOLOGIA", logical_capacity=ADDRESSABLE_CONTENTS, source="core/human_psychology.py", metadata={"materialization": "on-demand", "canonical_gate": "BLOCO 2 -> BLOCO 3", "biological_foundation": "BLOCO 6", "knowledge_graph": "shared", "automatic_diagnosis": False, "automatic_personality_label": False, "intention_certainty": False, "personal_psychological_profile_created": False})

    @staticmethod
    def _domain_key(value: str) -> str:
        n = _norm(value)
        aliases = {"percepcao": "perception_attention", "atencao": "perception_attention", "memoria": "memory_learning", "memoria_humana": "memory_learning", "aprendizagem": "memory_learning", "motivacao": "motivation_habits", "habitos": "motivation_habits", "emocoes": "emotion_regulation", "emocao": "emotion_regulation", "personalidade": "personality_identity_self", "identidade": "personality_identity_self", "autoestima": "personality_identity_self", "cognicao": "cognition_decision_bias", "decisoes": "cognition_decision_bias", "vieses": "cognition_decision_bias", "trauma": "stress_trauma_grief", "estresse": "stress_trauma_grief", "luto": "stress_trauma_grief", "comportamento": "behavior_expression_intention", "expressoes": "behavior_expression_intention", "intencao": "behavior_expression_intention", "teoria_da_mente": "theory_of_mind_social_cognition", "relacoes_psicologicas": "relationships_attachment", "relacoes": "relationships_attachment", "desenvolvimento": "development_context", "cultura": "development_context", "psicometria": "research_measurement_interpretation", "interpretacao": "research_measurement_interpretation", "necessidades_psicologicas": "psychological_needs_adaptation", "bem_estar": "psychological_needs_adaptation"}
        return aliases.get(n, n)

    @staticmethod
    def _branch(key: str) -> PsychologyBranch:
        for branch in PSYCHOLOGY_BRANCHES:
            if branch.key == key:
                return branch
        raise KeyError(key)

    @staticmethod
    def _domain_node_id(domain: str) -> str:
        return f"PSY-DOM-{domain.upper()}"

    @staticmethod
    def _branch_node_id(branch: str) -> str:
        return f"PSY-BR-{branch.upper()}"

    @staticmethod
    def _subtopic_node_id(branch: str, subtopic: str) -> str:
        return f"PSY-SUB-{branch.upper()}-{_norm(subtopic).upper()[:80]}"

    def taxonomy_snapshot(self, domain: str | None = None) -> dict:
        key = self._domain_key(domain) if domain else None
        if key and key not in PSYCHOLOGY_DOMAINS:
            raise KeyError(domain)
        selected = [b for b in PSYCHOLOGY_BRANCHES if key is None or b.domain == key]
        return {"root": "Mente Humana e Psicologia", "domain": key, "branches": [{"domain": b.domain, "domain_label": DOMAIN_LABELS[b.domain], "branch": b.key, "branch_label": b.label, "subtopics": list(b.subtopics)} for b in selected], "cross_domain_relations": deepcopy(CROSS_DOMAIN_RELATIONS), "interpretation_policy": deepcopy(INTERPRETATION_POLICY)}

    def _ensure_taxonomy_path(self, branch: PsychologyBranch, *, include_subtopics: bool = True) -> dict:
        root = self.graph.add_entity("human_psychology_taxonomy", "Mente Humana e Psicologia", node_id=self.TAXONOMY_ROOT_ID, data={"block": "B07", "diagnostic": False, "source_of_truth": "core/human_psychology.py"})
        life_root = "LIFE-TAX-ROOT"
        self.graph.add_entity("human_life_taxonomy", "Vida, Corpo e Necessidades Humanas", node_id=life_root, data={"block": "B06"})
        self.graph.relate(root, life_root, "related_to", metadata={"block": "B07", "biological_context": True})
        self.graph.relate(life_root, root, "related_to", metadata={"block": "B07", "psychological_context": True})
        domain_id = self._domain_node_id(branch.domain)
        self.graph.add_entity("psychology_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id, data={"block": "B07", "domain": branch.domain, "diagnostic": False})
        self.graph.relate(root, domain_id, "has_part", metadata={"block": "B07", "taxonomy": True})
        self.graph.relate(domain_id, root, "part_of", metadata={"block": "B07", "taxonomy": True})
        branch_id = self._branch_node_id(branch.key)
        self.graph.add_entity("psychology_branch", branch.label, node_id=branch_id, data={"block": "B07", "domain": branch.domain, "branch": branch.key, "diagnostic": False})
        self.graph.relate(domain_id, branch_id, "has_part", metadata={"block": "B07", "taxonomy": True})
        self.graph.relate(branch_id, domain_id, "part_of", metadata={"block": "B07", "taxonomy": True})
        sub_ids = []
        if include_subtopics:
            for subtopic in branch.subtopics:
                sub_id = self._subtopic_node_id(branch.key, subtopic)
                self.graph.add_entity("psychology_subtopic", subtopic, node_id=sub_id, data={"block": "B07", "domain": branch.domain, "branch": branch.key})
                self.graph.relate(branch_id, sub_id, "has_part", metadata={"block": "B07", "taxonomy": True})
                self.graph.relate(sub_id, branch_id, "part_of", metadata={"block": "B07", "taxonomy": True})
                sub_ids.append(sub_id)
        return {"root_id": root, "domain_id": domain_id, "branch_id": branch_id, "subtopic_ids": sub_ids}

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        key = self._domain_key(domain) if domain else None
        if key and key not in PSYCHOLOGY_DOMAINS:
            raise KeyError(domain)
        selected = [b for b in PSYCHOLOGY_BRANCHES if key is None or b.domain == key]
        paths = [self._ensure_taxonomy_path(b) for b in selected]
        return {"domain": key, "branches_materialized": len(paths), "knowledge_graph": "shared", "diagnostic_engine_created": False, "paths": paths}

    def reference(self, query: str) -> dict | None:
        query = _clean(query)
        if not query:
            return None
        if self.multidisciplinary is None:
            if "multidisciplinary" not in self._providers:
                from core.multidisciplinary_knowledge import MultidisciplinaryKnowledgeEngine
                self._providers["multidisciplinary"] = MultidisciplinaryKnowledgeEngine()
            engine = self._providers["multidisciplinary"]
        else:
            engine = self.multidisciplinary
        answer = engine.answer(f"psicologia {query}")
        if not answer:
            return None
        return {"provider": "core.multidisciplinary_knowledge", "subject": "psychology_sociology", "answer": answer, "block": "B07", "diagnostic": False, "canonicalized": False, "note": "referência educacional geral; não diagnostica, não define personalidade e não prova intenção"}

    def interpret_behavior(self, observation: str, *, context: str = "", repeated_pattern: bool = False, corroborating_evidence: tuple[str, ...] | list[str] | None = None) -> dict:
        observation = _clean(observation)
        if not observation:
            raise ValueError("observação comportamental vazia")
        evidence = [_clean(x) for x in (corroborating_evidence or ()) if _clean(x)]
        possibilities = ["resposta situacional ao contexto imediato", "hábito ou rotina aprendida", "estado emocional transitório", "estratégia de comunicação ou autoproteção", "preferência individual sem significado clínico", "efeito de normas sociais/culturais", "combinação de múltiplos fatores não observados"]
        if repeated_pattern:
            possibilities.append("padrão repetido que requer contexto longitudinal e ainda não equivale a diagnóstico")
        return {"observation": observation, "context": _clean(context), "repeated_pattern": bool(repeated_pattern), "corroborating_evidence": evidence, "epistemic_kind": "inference", "certainty": "underdetermined", "possible_interpretations": possibilities, "alternative_interpretations_required": True, "exceptions_required": True, "diagnosis": None, "mental_disorder_candidates": [], "stable_personality_label": None, "intention": None, "intention_certainty": False, "single_observation_is_pattern": False, "policy": deepcopy(INTERPRETATION_POLICY), "missing_context": ["história e frequência do comportamento", "situação e objetivo declarado pela própria pessoa", "normas culturais e relacionais", "estado físico/emocional e eventos recentes", "observações independentes ao longo do tempo"]}

    def promote_canonical_psychology_knowledge(self, record_id: str, canonical_label: str, *, domain: str, branch: str, knowledge_type: str = "concept", aliases=None, properties=None, subtopics=None, contexts=None, rules=None, exceptions=None, summary: str = "") -> dict:
        domain_key = self._domain_key(domain)
        if domain_key not in PSYCHOLOGY_DOMAINS:
            raise ValueError(f"domínio B07 inválido: {domain}")
        branch_obj = self._branch(branch)
        if branch_obj.domain != domain_key:
            raise ValueError(f"ramo {branch} não pertence a {domain_key}")
        props = dict(properties or {})
        props.update({"diagnostic_use": False, "automatic_personality_label": False, "intention_certainty": False, "personal_psychological_profile": False, "knowledge_scope": "general_psychology_and_behavior"})
        result = self.knowledge.promote_canonical(record_id, canonical_label, knowledge_type=knowledge_type, namespace=self.NAMESPACE, summary=summary, aliases=aliases, properties=props, categories=["psychology", "human_mind", domain_key, branch_obj.key], subtopics=subtopics, contexts=contexts, rules=rules, exceptions=exceptions, provenance={"psychology_block": "B07", "human_life_foundation": "B06", "domain": domain_key, "branch": branch_obj.key, "source_record_id": record_id, "diagnostic": False})
        taxonomy = self._ensure_taxonomy_path(branch_obj, include_subtopics=False)
        self.graph.relate(result["knowledge_id"], taxonomy["branch_id"], "is_a", metadata={"block": "B07", "psychology_taxonomy": True, "diagnostic": False})
        self.graph.relate(taxonomy["branch_id"], result["knowledge_id"], "has_part", metadata={"block": "B07", "psychology_taxonomy": True, "diagnostic": False})
        return result

    def relate(self, source_id: str, target_id: str, relation: str, *, weight: float = 1.0) -> dict:
        return self.knowledge.relate(source_id, target_id, relation, weight=weight, metadata={"block": "B07", "psychology": True, "diagnostic": False})

    def policy(self) -> dict:
        return deepcopy(INTERPRETATION_POLICY)

    def stats(self) -> dict:
        return {"status": "experimental-integrated", "namespace": self.knowledge.store.get_namespace(self.NAMESPACE), "catalog": self.catalog.stats(), "domains": [{"key": k, "label": DOMAIN_LABELS[k]} for k in PSYCHOLOGY_DOMAINS], "lenses": [{"key": k, "label": l} for k, l, _ in PSYCHOLOGY_LENSES], "knowledge_graph": "shared knowledge_nodes/knowledge_edges", "canonical_knowledge": "BLOCO 2 gate -> BLOCO 3 -> B07", "biological_foundation": "BLOCO 6 linked, not reductive", "reference_families": list(REFERENCE_FAMILIES), "interpretation_policy": self.policy()}

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {"status bloco 7", "status psicologia", "status mente humana", "mente humana e psicologia", "fundamentos psicologicos", "fundamentos psicológicos"}:
            s = self.stats()
            return f"🧠 BLOCO 7 — MENTE HUMANA E PSICOLOGIA: {s['catalog']['addressable_contents']} conteúdos endereçáveis em B07 | {s['catalog']['domains']} domínios × {s['catalog']['branches']} ramos × {s['catalog']['lenses_per_branch']} lentes = {s['catalog']['canonical_nodes']} nós | Knowledge Graph=COMPARTILHADO | diagnóstico/leitura mental automática=DESATIVADOS."
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"🧠 {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        taxonomy = re.match(r"^(?:taxonomia psicologia|taxonomia mente humana)(?:\s+(.+))?$", raw, re.I)
        if taxonomy:
            snapshot = self.taxonomy_snapshot(taxonomy.group(1))
            labels = ", ".join(x["branch_label"] for x in snapshot["branches"][:12])
            return f"🧠 Taxonomia B07: {len(snapshot['branches'])} ramos. {labels}{'…' if len(snapshot['branches']) > 12 else ''}"
        if re.match(r"^(?:diagnostico psicologico automatico|diagnóstico psicológico automático|leitura mental automatica|leitura mental automática)$", raw, re.I):
            return "🛡️ BLOCO 7 não transforma comportamento isolado em diagnóstico, personalidade, intenção ou certeza. Interpretações permanecem contextuais, alternativas e explicitamente incertas."
        return None
