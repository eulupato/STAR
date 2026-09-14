"""BLOCO 10 — Contextos Humanos Específicos da STAR.

Camada situacional que cruza pessoa, idade, ambiente, relação, necessidade, risco,
norma, cultura e contexto sobre os BLOCO 2/3/6/7/8/9 e o mesmo Knowledge Graph.
Não recria desenvolvimento humano, psicologia, linguagem ou sociologia.

Princípios permanentes:
- idade != competência/capacidade automática;
- deficiência != incapacidade;
- rótulo != necessidade fixa de suporte;
- toque, distância, privacidade, autonomia e responsabilidade dependem de contexto;
- crise/emergência aumenta saliência de segurança, mas não apaga automaticamente
  autonomia, privacidade, consentimento, jurisdição ou responsabilidade;
- compreensão contextual nunca concede autorização operacional por si só.

Escala lógica:
- 50 ramos × 10 lentes = 500 nós canônicos;
- PESSOA 10 × IDADE 5 × AMBIENTE 5 × RELAÇÃO 5 × NECESSIDADE 4 × RISCO 4 ×
  NORMA 4 × CULTURA 5 × CONTEXTO 5 = 2.000.000 variações por nó;
- 500 × 2.000.000 = 1.000.000.000 representações endereçáveis em B10.

Tudo é materializado sob demanda. 1B não significa 1B de perfis, pessoas, fatos,
diagnósticos, regras universais ou linhas pré-carregadas.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import prod
import re
import unicodedata

from core.universal_knowledge import UniversalKnowledgeArchitecture


@dataclass(frozen=True)
class HumanContextBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in raw.split(";") if x.strip())


def _norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def _clean(text: str) -> str:
    return " ".join(str(text or "").strip().split())


HUMAN_CONTEXT_DOMAINS = (
    "life_stages",
    "disability_capabilities",
    "family_care",
    "school_education",
    "work_organizations",
    "public_private_space",
    "crisis_emergency",
    "human_animal",
    "touch_distance",
    "privacy_boundaries",
    "autonomy_consent",
    "responsibility_safeguards",
    "context_norm_culture",
)

DOMAIN_LABELS = {
    "life_stages": "Fases da vida e contexto",
    "disability_capabilities": "Deficiência, capacidades e acessibilidade",
    "family_care": "Família, cuidado e interdependência",
    "school_education": "Escola e contextos educacionais",
    "work_organizations": "Trabalho e contextos organizacionais",
    "public_private_space": "Espaço público, privado e compartilhado",
    "crisis_emergency": "Crise e emergência",
    "human_animal": "Contextos humano-animal",
    "touch_distance": "Toque, proximidade e distância social",
    "privacy_boundaries": "Privacidade, informação e limites pessoais",
    "autonomy_consent": "Autonomia, consentimento e decisão apoiada",
    "responsibility_safeguards": "Responsabilidade, cuidado e salvaguardas",
    "context_norm_culture": "Normas, cultura e leitura contextual",
}


HUMAN_CONTEXT_BRANCHES = (
    HumanContextBranch("life_stages", "infants", "Bebês", _subs("bebês;dependência;desenvolvimento inicial;comunicação não verbal;rotina;sono;alimentação;segurança;cuidador")),
    HumanContextBranch("life_stages", "children", "Crianças", _subs("crianças;desenvolvimento;aprendizagem;brincadeira;proteção;autonomia progressiva;escola;família;pares")),
    HumanContextBranch("life_stages", "adolescents", "Adolescentes", _subs("adolescentes;puberdade;identidade;pares;escola;autonomia progressiva;privacidade;responsabilidade;risco")),
    HumanContextBranch("life_stages", "adults", "Adultos", _subs("adultos;autonomia;trabalho;família;responsabilidade;cuidado;relações;vida pública;vida privada")),
    HumanContextBranch("life_stages", "older_adults", "Idosos", _subs("idosos;envelhecimento;autonomia;acessibilidade;apoio;participação;privacidade;cuidado;capacidades variáveis")),

    HumanContextBranch("disability_capabilities", "disability_context", "Pessoas com deficiência em contexto", _subs("pessoas com deficiência;modelo social;barreiras;acessibilidade;participação;autonomia;apoio;direitos;adaptação")),
    HumanContextBranch("disability_capabilities", "different_capabilities", "Diferentes capacidades e formas de participação", _subs("diferentes capacidades;capacidades sensoriais;motoras;cognitivas;comunicacionais;temporárias;variabilidade;apoio")),
    HumanContextBranch("disability_capabilities", "accessibility_accommodation", "Acessibilidade e adaptações", _subs("acessibilidade;adaptação;tecnologia assistiva;comunicação acessível;barreiras físicas;barreiras informacionais;participação")),
    HumanContextBranch("disability_capabilities", "support_without_assumption", "Suporte sem presunção de incapacidade", _subs("apoio;preferências;ajuda oferecida;ajuda solicitada;decisão apoiada;independência;interdependência;dignidade")),

    HumanContextBranch("family_care", "family_roles", "Família e papéis familiares", _subs("família;papéis;parentesco;cuidado;autoridade;apoio;conflito;rotinas;responsabilidade")),
    HumanContextBranch("family_care", "caregiving", "Cuidado e cuidadores", _subs("cuidador;cuidado;necessidades;limites;autonomia;fadiga;responsabilidade;apoio;comunicação")),
    HumanContextBranch("family_care", "dependence_interdependence", "Dependência, independência e interdependência", _subs("dependência;independência;interdependência;apoio;capacidade;autonomia;necessidade;reciprocidade")),
    HumanContextBranch("family_care", "home_private_routines", "Casa, rotina e vida privada", _subs("casa;espaço privado;rotina;intimidade;privacidade;segurança;regras domésticas;convivência")),

    HumanContextBranch("school_education", "classroom_context", "Sala de aula e aprendizagem", _subs("escola;sala de aula;aprendizagem;professor;aluno;regras;participação;atenção;acessibilidade")),
    HumanContextBranch("school_education", "learning_support", "Apoios e necessidades educacionais", _subs("apoio educacional;acessibilidade;ritmo;instrução;adaptações;comunicação;necessidades;participação")),
    HumanContextBranch("school_education", "peers_school_social", "Pares e relações na escola", _subs("pares;amizade;cooperação;conflito;bullying;pertencimento;distância social;privacidade")),
    HumanContextBranch("school_education", "school_authority_safeguarding", "Autoridade escolar e salvaguardas", _subs("autoridade;supervisão;responsabilidade;segurança;proteção;privacidade;família;instituição;procedimento")),

    HumanContextBranch("work_organizations", "workplace_roles", "Papéis e relações no trabalho", _subs("trabalho;colegas;gestão;hierarquia;cliente;responsabilidade;comunicação;limites profissionais")),
    HumanContextBranch("work_organizations", "workplace_accessibility", "Acessibilidade e capacidade no trabalho", _subs("acessibilidade;adaptações;capacidade funcional;ferramentas;ambiente;participação;barreiras;apoio")),
    HumanContextBranch("work_organizations", "professional_responsibility", "Responsabilidade profissional", _subs("responsabilidade;dever;competência;procedimento;risco;segurança;prestação de contas;limites")),
    HumanContextBranch("work_organizations", "professional_boundaries", "Limites e privacidade profissionais", _subs("privacidade;confidencialidade;toque;distância;autoridade;consentimento;informação;limites")),

    HumanContextBranch("public_private_space", "public_space", "Espaço público", _subs("espaço público;rua;transporte;praça;serviços;multidão;distância social;privacidade;acessibilidade")),
    HumanContextBranch("public_private_space", "private_space", "Espaço privado", _subs("espaço privado;casa;quarto;intimidade;acesso;consentimento;privacidade;segurança;limites")),
    HumanContextBranch("public_private_space", "shared_space", "Espaços compartilhados", _subs("espaço compartilhado;condomínio;escola;trabalho;hospitalidade;regras;ruído;proximidade;negociação")),
    HumanContextBranch("public_private_space", "space_transition", "Transições entre espaços e expectativas", _subs("entrada;saída;convite;acesso;fronteiras;expectativas;papéis;privacidade;segurança")),

    HumanContextBranch("crisis_emergency", "crisis_context", "Crise e desorganização contextual", _subs("crise;incerteza;estresse;necessidades imediatas;comunicação;apoio;segurança;prioridades")),
    HumanContextBranch("crisis_emergency", "emergency_context", "Emergência e risco imediato", _subs("emergência;risco imediato;segurança;triagem contextual;comunicação;autoridade;consentimento;necessidade")),
    HumanContextBranch("crisis_emergency", "evacuation_shelter", "Evacuação, abrigo e deslocamento", _subs("evacuação;abrigo;deslocamento;multidão;acessibilidade;família;animais;necessidades;informação")),
    HumanContextBranch("crisis_emergency", "acute_uncertainty", "Decisão sob incerteza aguda", _subs("incerteza;tempo limitado;informação incompleta;risco;responsabilidade;escalonamento;reavaliação")),

    HumanContextBranch("human_animal", "companion_animals", "Animais de companhia e convivência", _subs("animais;animais de companhia;guardiões;família;toque;espaço;bem-estar;comportamento;segurança")),
    HumanContextBranch("human_animal", "service_working_animals", "Animais de serviço e trabalho", _subs("animais de serviço;animais de assistência;animais de trabalho;acesso;função;interferência;bem-estar;limites")),
    HumanContextBranch("human_animal", "unfamiliar_animals", "Animais desconhecidos e interação prudente", _subs("animais desconhecidos;comportamento;distância;risco;aproximação;toque;território;guardiões;incerteza")),

    HumanContextBranch("touch_distance", "touch_consent", "Toque, consentimento e necessidade", _subs("toque;consentimento;assentimento;ajuda física;cuidado;necessidade;limites;risco;cultura")),
    HumanContextBranch("touch_distance", "social_distance", "Distância social e espaço interpessoal", _subs("distância social;espaço interpessoal;proximidade;multidão;relação;cultura;segurança;conforto")),
    HumanContextBranch("touch_distance", "proxemics_culture", "Proxêmica e variação cultural", _subs("proxêmica;distância;cultura;contexto;formalidade;relação;ambiente;variação individual")),
    HumanContextBranch("touch_distance", "physical_assistance", "Assistência física e limites", _subs("assistência física;mobilidade;guia;transferência;apoio;preferência;consentimento;segurança;acessibilidade")),

    HumanContextBranch("privacy_boundaries", "privacy", "Privacidade contextual", _subs("privacidade;intimidade;espaço;informação;observação;acesso;expectativa;necessidade;risco")),
    HumanContextBranch("privacy_boundaries", "information_confidentiality", "Informação pessoal e confidencialidade", _subs("informação pessoal;confidencialidade;compartilhamento;necessidade de saber;consentimento;instituição;risco")),
    HumanContextBranch("privacy_boundaries", "personal_boundaries", "Limites pessoais", _subs("limites pessoais;toque;conversa;espaço;tempo;objetos;acesso;recusa;negociação")),

    HumanContextBranch("autonomy_consent", "autonomy", "Autonomia em contexto", _subs("autonomia;preferências;escolha;capacidade;apoio;risco;responsabilidade;idade;contexto")),
    HumanContextBranch("autonomy_consent", "supported_decision", "Decisão apoiada", _subs("decisão apoiada;informação acessível;tempo;alternativas;apoio;preferências;compreensão;autonomia")),
    HumanContextBranch("autonomy_consent", "consent_assent", "Consentimento, assentimento e recusa", _subs("consentimento;assentimento;recusa;compreensão;voluntariedade;autoridade;idade;capacidade;contexto")),

    HumanContextBranch("responsibility_safeguards", "responsibility", "Responsabilidade contextual", _subs("responsabilidade;papel;capacidade;controle;dever;previsibilidade;autoridade;consequências")),
    HumanContextBranch("responsibility_safeguards", "duty_of_care", "Dever de cuidado e proteção", _subs("dever de cuidado;proteção;segurança;dependência;papel profissional;família;instituição;limites")),
    HumanContextBranch("responsibility_safeguards", "supervision_safeguarding", "Supervisão e salvaguardas", _subs("supervisão;salvaguarda;crianças;pessoas vulneráveis;risco;privacidade;autonomia;escalonamento")),
    HumanContextBranch("responsibility_safeguards", "accountability", "Prestação de contas e revisão", _subs("prestação de contas;registro;revisão;justificativa;procedimento;erro;reparação;aprendizado")),

    HumanContextBranch("context_norm_culture", "norms_rules", "Normas formais e informais", _subs("normas;regras;etiqueta;políticas;leis;costumes;expectativas;exceções;conflitos")),
    HumanContextBranch("context_norm_culture", "culture_variation", "Cultura e variação contextual", _subs("cultura;costumes;valores;distância;toque;família;privacidade;autoridade;variação interna")),
    HumanContextBranch("context_norm_culture", "relationship_context", "Relação, poder e contexto", _subs("relação;família;amizade;profissional;autoridade;estranho;dependência;poder;confiança")),
    HumanContextBranch("context_norm_culture", "conflict_negotiation", "Conflito, negociação e ajuste contextual", _subs("conflito;necessidades concorrentes;negociação;limites;mediação;prioridades;reavaliação;contexto")),
)


HUMAN_CONTEXT_LENSES = (
    ("concept", "conceito", "definir o fenômeno e separar descrição, inferência e norma"),
    ("person_capacity", "pessoa e capacidades", "considerar capacidades reais, preferências e apoios sem inferir incapacidade por rótulo"),
    ("development_age", "idade e desenvolvimento", "situar idade e desenvolvimento sem transformar faixa etária em competência automática"),
    ("environment", "ambiente", "avaliar exigências, barreiras, privacidade, recursos e riscos do ambiente"),
    ("relation", "relação", "considerar papel, proximidade, poder, confiança, dependência e limites da relação"),
    ("needs_support", "necessidade e suporte", "identificar necessidades e formas de apoio preservando participação e autonomia quando possível"),
    ("risk_safety", "risco e segurança", "avaliar risco, urgência, incerteza e salvaguardas sem converter contexto em autorização automática"),
    ("norms_rights", "normas, direitos e responsabilidades", "distinguir ética, costumes, políticas e leis dependentes de jurisdição e contexto"),
    ("culture_variation", "cultura e variação", "considerar cultura e normas locais sem essencializar grupos ou ignorar variação individual"),
    ("decision_limits", "decisão e limites", "explicitar incerteza, consentimento, privacidade, alternativas, responsabilidade e limites operacionais"),
)


PERSON_AXIS = (
    "individual_general", "family_member", "caregiver", "student", "worker",
    "person_with_disability", "person_with_temporary_limitation",
    "person_requiring_access_support", "professional_or_responder", "bystander_or_stranger",
)
AGE_AXIS = ("infant", "child", "adolescent", "adult", "older_adult")
ENVIRONMENT_AXIS = ("home_private", "school_education", "workplace", "public_shared", "crisis_emergency")
RELATION_AXIS = ("self", "family_or_caregiver", "peer_or_friend", "professional_or_authority", "stranger_or_public")
NEED_AXIS = ("safety", "care_or_support", "communication_or_information", "participation_or_autonomy")
RISK_AXIS = ("low_or_unspecified", "physical", "psychosocial", "environmental_or_situational")
NORM_AXIS = ("ethical", "social_or_etiquette", "institutional_policy", "legal_or_regulatory")
CULTURE_AXIS = ("individual_or_family", "local_community", "institutional_or_professional", "religious_or_worldview", "cross_cultural")
CONTEXT_AXIS = ("routine", "transition", "conflict", "crisis", "emergency")

VARIANT_AXES = (
    ("person", PERSON_AXIS),
    ("age", AGE_AXIS),
    ("environment", ENVIRONMENT_AXIS),
    ("relation", RELATION_AXIS),
    ("need", NEED_AXIS),
    ("risk", RISK_AXIS),
    ("norm", NORM_AXIS),
    ("culture", CULTURE_AXIS),
    ("context", CONTEXT_AXIS),
)

REQUESTED_TOPICS = (
    "bebês", "crianças", "adolescentes", "adultos", "idosos",
    "pessoas com deficiência", "diferentes capacidades", "família", "escola", "trabalho",
    "espaço público", "espaço privado", "crise", "emergência", "animais", "toque",
    "distância social", "privacidade", "autonomia", "responsabilidade",
)

INTERPRETATION_POLICY = {
    "age_is_automatic_capacity": False,
    "disability_is_inability": False,
    "support_need_is_fixed_from_label": False,
    "public_space_eliminates_privacy": False,
    "private_space_eliminates_safety_rules": False,
    "touch_is_automatically_permitted": False,
    "social_distance_is_universal_constant": False,
    "emergency_cancels_autonomy_or_privacy": False,
    "group_or_role_determines_individual_behavior": False,
    "animal_behavior_is_certain_from_category": False,
    "contextual_inference_is_operational_authorization": False,
    "consent_and_boundary_context_required": True,
    "accessibility_and_supported_autonomy": True,
    "historical_cultural_jurisdictional_context_required": True,
    "alternative_interpretations_required": True,
    "rule": "IDADE, DEFICIÊNCIA, PAPEL OU AMBIENTE NÃO DETERMINAM SOZINHOS CAPACIDADE, NECESSIDADE, CONSENTIMENTO, PRIVACIDADE OU RESPONSABILIDADE",
}

CROSS_BLOCK_REUSE = {
    "B06": "vida, desenvolvimento, corpo e necessidades humanas",
    "B07": "psicologia, relações, comportamento, autonomia e desenvolvimento",
    "B08": "comunicação, gestos, voz, linguagem e interpretação contextual",
    "B09": "família, escola, trabalho, normas, cultura, direito e instituições",
}

CANONICAL_NODES = len(HUMAN_CONTEXT_BRANCHES) * len(HUMAN_CONTEXT_LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in VARIANT_AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE

if len(HUMAN_CONTEXT_DOMAINS) != 13:
    raise ValueError("B10 requer 13 domínios")
if len(HUMAN_CONTEXT_BRANCHES) != 50:
    raise ValueError(f"B10 requer 50 ramos; encontrados {len(HUMAN_CONTEXT_BRANCHES)}")
if len(HUMAN_CONTEXT_LENSES) != 10:
    raise ValueError("B10 requer 10 lentes")
if CANONICAL_NODES != 500:
    raise ValueError(f"B10 requer 500 nós; encontrados {CANONICAL_NODES}")
if VARIANTS_PER_NODE != 2_000_000:
    raise ValueError(f"B10 requer 2M variações/nó; encontradas {VARIANTS_PER_NODE}")
if ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise ValueError(f"B10 requer 1B endereçáveis; encontrados {ADDRESSABLE_CONTENTS}")


def _decode_axes(index: int) -> dict[str, str]:
    if not 0 <= int(index) < VARIANTS_PER_NODE:
        raise IndexError(index)
    remainder = int(index)
    decoded: dict[str, str] = {}
    for name, values in reversed(VARIANT_AXES):
        remainder, offset = divmod(remainder, len(values))
        decoded[name] = values[offset]
    if remainder:
        raise RuntimeError("falha ao decodificar variante B10")
    return {name: decoded[name] for name, _ in VARIANT_AXES}


class HumanContextCatalog:
    NAMESPACE = "B10"
    PREFIX = "CTX-B10"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "domains": len(HUMAN_CONTEXT_DOMAINS),
            "branches": len(HUMAN_CONTEXT_BRANCHES),
            "lenses_per_branch": len(HUMAN_CONTEXT_LENSES),
            "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS,
            "variant_axes": {name: len(values) for name, values in VARIANT_AXES},
            "materialization": "on-demand",
            "prepopulated_knowledge_rows": 0,
            "truthfulness_note": (
                "1B são representações contextuais determinísticas endereçáveis por pessoa, idade, ambiente, relação, necessidade, risco, norma, cultura e contexto; "
                "não 1B de perfis pessoais, diagnósticos, regras universais ou fatos pré-carregados"
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
        return f"CTX-B10-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"CTX-B10-(\d{10})", str(identifier or "").strip().upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, len(HUMAN_CONTEXT_LENSES))
        branch = HUMAN_CONTEXT_BRANCHES[branch_index]
        lens_key, lens_label, instruction = HUMAN_CONTEXT_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {
            "id": f"CTX-B10-{absolute:010d}",
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
                f"Pessoa={axes['person']}; idade={axes['age']}; ambiente={axes['environment']}; relação={axes['relation']}; "
                f"necessidade={axes['need']}; risco={axes['risk']}; norma={axes['norm']}; cultura={axes['culture']}; contexto={axes['context']}. "
                "Preservar capacidades reais, acessibilidade, consentimento, privacidade, autonomia, responsabilidade, variação cultural e incerteza; "
                "contexto não concede autorização operacional."
            ),
        }


class HumanContextFoundations:
    NAMESPACE = "B10"
    TAXONOMY_ROOT_ID = "CTX-TAX-ROOT"

    def __init__(
        self,
        knowledge: UniversalKnowledgeArchitecture,
        *,
        human_life=None,
        human_psychology=None,
        language_communication=None,
        society_culture=None,
    ):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.human_life = human_life
        self.human_psychology = human_psychology
        self.language_communication = language_communication
        self.society_culture = society_culture
        self.catalog = HumanContextCatalog()
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 10 — CONTEXTOS HUMANOS ESPECÍFICOS",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/human_contexts.py",
            metadata={
                "materialization": "on-demand",
                "canonical_gate": "BLOCO 2 -> BLOCO 3",
                "knowledge_graph": "shared",
                "reuses_blocks": list(CROSS_BLOCK_REUSE),
                "parallel_context_database": False,
                "parallel_context_graph": False,
                "automatic_capacity_inference": False,
                "automatic_action_authorization": False,
            },
        )

    @staticmethod
    def _domain_key(value: str) -> str:
        normalized = _norm(value)
        aliases = {
            "bebes": "life_stages", "criancas": "life_stages", "adolescentes": "life_stages", "adultos": "life_stages", "idosos": "life_stages", "idade": "life_stages",
            "deficiencia": "disability_capabilities", "capacidades": "disability_capabilities", "acessibilidade": "disability_capabilities",
            "familia": "family_care", "cuidado": "family_care",
            "escola": "school_education", "educacao": "school_education",
            "trabalho": "work_organizations", "organizacao": "work_organizations",
            "espaco_publico": "public_private_space", "espaco_privado": "public_private_space", "espaco": "public_private_space",
            "crise": "crisis_emergency", "emergencia": "crisis_emergency",
            "animais": "human_animal", "animal": "human_animal",
            "toque": "touch_distance", "distancia_social": "touch_distance", "proximidade": "touch_distance",
            "privacidade": "privacy_boundaries", "limites": "privacy_boundaries",
            "autonomia": "autonomy_consent", "consentimento": "autonomy_consent",
            "responsabilidade": "responsibility_safeguards", "salvaguarda": "responsibility_safeguards",
            "norma": "context_norm_culture", "cultura": "context_norm_culture", "contexto": "context_norm_culture",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _branch(key: str) -> HumanContextBranch:
        for branch in HUMAN_CONTEXT_BRANCHES:
            if branch.key == key:
                return branch
        raise KeyError(key)

    @staticmethod
    def _domain_node_id(domain: str) -> str:
        return f"CTX-DOM-{domain.upper()}"

    @staticmethod
    def _branch_node_id(branch: str) -> str:
        return f"CTX-BR-{branch.upper()}"

    @staticmethod
    def _subtopic_node_id(branch: str, subtopic: str) -> str:
        return f"CTX-SUB-{branch.upper()}-{_norm(subtopic).upper()[:80]}"

    def taxonomy_snapshot(self, domain: str | None = None) -> dict:
        key = self._domain_key(domain) if domain else None
        if key and key not in HUMAN_CONTEXT_DOMAINS:
            raise KeyError(domain)
        selected = [branch for branch in HUMAN_CONTEXT_BRANCHES if key is None or branch.domain == key]
        return {
            "root": "Contextos Humanos Específicos",
            "domain": key,
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
            "reuse": deepcopy(CROSS_BLOCK_REUSE),
            "interpretation_policy": deepcopy(INTERPRETATION_POLICY),
        }

    def _ensure_taxonomy_path(self, branch: HumanContextBranch, *, include_subtopics: bool = True) -> dict:
        root = self.graph.add_entity(
            "human_context_taxonomy",
            "Contextos Humanos Específicos",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B10", "source_of_truth": "core/human_contexts.py"},
        )
        linked_roots = (
            ("LIFE-TAX-ROOT", "human_life_taxonomy", "Vida, Corpo e Necessidades Humanas", "B06"),
            ("PSY-TAX-ROOT", "human_psychology_taxonomy", "Mente Humana e Psicologia", "B07"),
            ("LANG-TAX-ROOT", "language_communication_taxonomy", "Linguagem e Comunicação", "B08"),
            ("SOC-TAX-ROOT", "society_culture_taxonomy", "Sociedade e Cultura", "B09"),
        )
        for node_id, node_type, label, block in linked_roots:
            self.graph.add_entity(node_type, label, node_id=node_id, data={"block": block})
            self.graph.relate(root, node_id, "contextualizes", metadata={"block": "B10", "reuses": block})
            self.graph.relate(node_id, root, "related_to", metadata={"block": "B10", "human_context": True})

        domain_id = self._domain_node_id(branch.domain)
        self.graph.add_entity("human_context_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id, data={"block": "B10", "domain": branch.domain})
        self.graph.relate(root, domain_id, "has_part", metadata={"block": "B10", "taxonomy": True})
        self.graph.relate(domain_id, root, "part_of", metadata={"block": "B10", "taxonomy": True})

        branch_id = self._branch_node_id(branch.key)
        self.graph.add_entity("human_context_branch", branch.label, node_id=branch_id, data={"block": "B10", "domain": branch.domain, "branch": branch.key})
        self.graph.relate(domain_id, branch_id, "has_part", metadata={"block": "B10", "taxonomy": True})
        self.graph.relate(branch_id, domain_id, "part_of", metadata={"block": "B10", "taxonomy": True})

        sub_ids = []
        if include_subtopics:
            for subtopic in branch.subtopics:
                sub_id = self._subtopic_node_id(branch.key, subtopic)
                self.graph.add_entity("human_context_subtopic", subtopic, node_id=sub_id, data={"block": "B10", "domain": branch.domain, "branch": branch.key})
                self.graph.relate(branch_id, sub_id, "has_part", metadata={"block": "B10", "taxonomy": True})
                self.graph.relate(sub_id, branch_id, "part_of", metadata={"block": "B10", "taxonomy": True})
                sub_ids.append(sub_id)
        return {"root_id": root, "domain_id": domain_id, "branch_id": branch_id, "subtopic_ids": sub_ids}

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        key = self._domain_key(domain) if domain else None
        if key and key not in HUMAN_CONTEXT_DOMAINS:
            raise KeyError(domain)
        selected = [branch for branch in HUMAN_CONTEXT_BRANCHES if key is None or branch.domain == key]
        paths = [self._ensure_taxonomy_path(branch) for branch in selected]
        return {
            "domain": key,
            "branches_materialized": len(paths),
            "knowledge_graph": "shared",
            "parallel_context_graph_created": False,
            "paths": paths,
        }

    def contextualize_human_situation(
        self,
        situation: str,
        *,
        person: str = "",
        age: str = "",
        environment: str = "",
        relation: str = "",
        need: str = "",
        risk: str = "",
        norm: str = "",
        culture: str = "",
        context: str = "",
        observations: tuple[str, ...] | list[str] | None = None,
    ) -> dict:
        situation = _clean(situation)
        if not situation:
            raise ValueError("situação humana vazia")
        observed = [_clean(item) for item in (observations or ()) if _clean(item)]
        dimensions = {
            "person": _clean(person), "age": _clean(age), "environment": _clean(environment),
            "relation": _clean(relation), "need": _clean(need), "risk": _clean(risk),
            "norm": _clean(norm), "culture": _clean(culture), "context": _clean(context),
        }
        return {
            "situation": situation,
            **dimensions,
            "observations": observed,
            "epistemic_kind": "inference",
            "certainty": "context_dependent",
            "diagnosis": None,
            "personal_profile_created": False,
            "age_determines_capacity": False,
            "disability_determines_inability": False,
            "role_determines_behavior": False,
            "consent_assumed": False,
            "privacy_voided_by_public_space": False,
            "autonomy_voided_by_emergency": False,
            "operational_authorization": False,
            "context_checks": [
                "identificar a pessoa e suas capacidades reais sem inferir incapacidade por idade, deficiência ou papel",
                "considerar desenvolvimento e idade sem usar faixa etária como competência automática",
                "avaliar barreiras, recursos, acessibilidade, privacidade e risco do ambiente",
                "considerar relação, poder, confiança, dependência e limites interpessoais",
                "distinguir necessidade observada, necessidade declarada e suporte preferido",
                "avaliar risco e urgência sem transformar urgência em permissão irrestrita",
                "distinguir ética, costume, política institucional e lei aplicável",
                "considerar cultura sem tratar grupos como homogêneos",
                "para toque ou assistência física, considerar consentimento/assentimento, necessidade, segurança e limites aplicáveis",
                "em crise/emergência, reavaliar informação incompleta e preservar autonomia/privacidade na medida compatível com segurança e regras aplicáveis",
                "em interação com animais, preservar bem-estar e incerteza comportamental; categoria do animal não garante resposta individual",
                "separar compreensão contextual de autorização operacional ou execução de ação",
            ],
            "missing_dimensions": [key for key, value in dimensions.items() if not value],
            "policy": deepcopy(INTERPRETATION_POLICY),
        }

    def promote_canonical_context_knowledge(
        self,
        record_id: str,
        canonical_label: str,
        *,
        domain: str,
        branch: str,
        knowledge_type: str = "concept",
        aliases=None,
        properties=None,
        subtopics=None,
        contexts=None,
        rules=None,
        exceptions=None,
        summary: str = "",
    ) -> dict:
        domain_key = self._domain_key(domain)
        if domain_key not in HUMAN_CONTEXT_DOMAINS:
            raise ValueError(f"domínio B10 inválido: {domain}")
        branch_obj = self._branch(branch)
        if branch_obj.domain != domain_key:
            raise ValueError(f"ramo {branch} não pertence a {domain_key}")
        props = dict(properties or {})
        props.update({
            "age_is_automatic_capacity": False,
            "disability_is_inability": False,
            "support_need_is_fixed_from_label": False,
            "contextual_inference_is_operational_authorization": False,
            "knowledge_scope": "specific_human_contexts",
        })
        result = self.knowledge.promote_canonical(
            record_id,
            canonical_label,
            knowledge_type=knowledge_type,
            namespace=self.NAMESPACE,
            summary=summary,
            aliases=aliases,
            properties=props,
            categories=["human_context", domain_key, branch_obj.key],
            subtopics=subtopics,
            contexts=contexts,
            rules=rules,
            exceptions=exceptions,
            provenance={
                "human_context_block": "B10",
                "domain": domain_key,
                "branch": branch_obj.key,
                "source_record_id": record_id,
                "automatic_action_authorization": False,
            },
        )
        taxonomy = self._ensure_taxonomy_path(branch_obj, include_subtopics=False)
        self.graph.relate(result["knowledge_id"], taxonomy["branch_id"], "is_a", metadata={"block": "B10", "human_context_taxonomy": True})
        self.graph.relate(taxonomy["branch_id"], result["knowledge_id"], "has_part", metadata={"block": "B10", "human_context_taxonomy": True})
        return result

    def relate(self, source_id: str, target_id: str, relation: str, *, weight: float = 1.0) -> dict:
        return self.knowledge.relate(source_id, target_id, relation, weight=weight, metadata={"block": "B10", "human_context": True})

    def policy(self) -> dict:
        return deepcopy(INTERPRETATION_POLICY)

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "domains": [{"key": key, "label": DOMAIN_LABELS[key]} for key in HUMAN_CONTEXT_DOMAINS],
            "lenses": [{"key": key, "label": label} for key, label, _ in HUMAN_CONTEXT_LENSES],
            "requested_topics": list(REQUESTED_TOPICS),
            "reuse": deepcopy(CROSS_BLOCK_REUSE),
            "knowledge_graph": "shared knowledge_nodes/knowledge_edges",
            "canonical_knowledge": "BLOCO 2 gate -> BLOCO 3 -> B10",
            "parallel_context_database": False,
            "parallel_context_graph": False,
            "interpretation_policy": self.policy(),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {
            "status bloco 10", "status contextos humanos", "contextos humanos especificos", "contextos humanos específicos",
            "bloco 10 contextos humanos", "fundamentos contextuais humanos",
        }:
            stats = self.stats()
            return (
                f"🧭 BLOCO 10 — CONTEXTOS HUMANOS ESPECÍFICOS: {stats['catalog']['addressable_contents']} conteúdos endereçáveis em B10 | "
                f"{stats['catalog']['domains']} domínios × {stats['catalog']['branches']} ramos × {stats['catalog']['lenses_per_branch']} lentes = "
                f"{stats['catalog']['canonical_nodes']} nós | {stats['catalog']['variants_per_node']} variações/nó | Knowledge Graph=COMPARTILHADO."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"🧭 {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        taxonomy = re.match(r"^(?:taxonomia contexto humano|taxonomia contextos humanos)(?:\s+(.+))?$", raw, re.I)
        if taxonomy:
            snapshot = self.taxonomy_snapshot(taxonomy.group(1))
            labels = ", ".join(item["branch_label"] for item in snapshot["branches"][:12])
            return f"🧭 Taxonomia B10: {len(snapshot['branches'])} ramos. {labels}{'…' if len(snapshot['branches']) > 12 else ''}"
        if low in {"limites contexto humano", "limites contextos humanos", "idade define capacidade", "deficiencia define incapacidade", "deficiência define incapacidade"}:
            return "🛡️ BLOCO 10 não trata idade, deficiência, papel social ou ambiente como prova automática de capacidade, incapacidade, necessidade, consentimento, privacidade ou responsabilidade."
        if low in {"toque e consentimento", "toque consentimento", "autonomia em emergencia", "autonomia em emergência"}:
            return "🛡️ Toque, assistência física, privacidade e autonomia dependem de consentimento/assentimento, necessidade, risco, relação, cultura e regras aplicáveis. Crise ou emergência não cria autorização irrestrita por si só."
        return None
