"""BLOCO 16 — interpretação, perspectiva e cognição social.

Especializa capacidades já existentes de B07 (psicologia/cognição social), B09
(sociedade/cultura), B13 (memória social), B14 (atenção) e B15 (SOCIAL/SITUATION
MODEL). Não cria um segundo modelo social, uma máquina de leitura mental nem um
sistema de diagnóstico.

Regra central:
INFERÊNCIA SOCIAL != FATO, INTENÇÃO != CERTEZA, CONFIANÇA != PERMISSÃO.

Escala lógica: 50 ramos x 10 lentes = 500 nós canônicos; 2.000.000 de estados
contextuais por nó = 1.000.000.000 de representações endereçáveis sob demanda.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import prod
import re
import unicodedata
from typing import Any, Iterable

from core.universal_knowledge import UniversalKnowledgeArchitecture


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


@dataclass(frozen=True)
class SocialCognitionBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


SOCIAL_COGNITION_DOMAINS = (
    "mental_states",
    "perspective_expectation",
    "intention_deception",
    "trust_reputation",
    "cooperation_competition",
    "negotiation",
    "persuasion_influence",
    "responsibility",
    "functional_empathy",
    "relationships_context",
)

DOMAIN_LABELS = {
    "mental_states": "Teoria da mente e estados mentais",
    "perspective_expectation": "Perspectiva e expectativa",
    "intention_deception": "Intenção, engano, mentira e segredo",
    "trust_reputation": "Confiança e reputação",
    "cooperation_competition": "Cooperação e competição",
    "negotiation": "Negociação e coordenação",
    "persuasion_influence": "Persuasão, influência e manipulação",
    "responsibility": "Responsabilidade e atribuição social",
    "functional_empathy": "Empatia funcional",
    "relationships_context": "Relações e contexto social",
}

SOCIAL_COGNITION_BRANCHES = (
    SocialCognitionBranch("mental_states", "theory_of_mind", "Teoria da mente", _subs("crenças;desejos;conhecimento;ignorância;falsa crença;incerteza mental")),
    SocialCognitionBranch("mental_states", "belief_tracking", "Rastreamento de crenças", _subs("crença declarada;crença observada;informação disponível;mudança de crença;fonte")),
    SocialCognitionBranch("mental_states", "knowledge_access", "Acesso à informação", _subs("quem viu;quem ouviu;quem sabe;quem não sabe;assimetria de informação")),
    SocialCognitionBranch("mental_states", "mental_state_uncertainty", "Incerteza sobre estados mentais", _subs("hipóteses;ambiguidade;alternativas;informação ausente;limites de inferência")),
    SocialCognitionBranch("mental_states", "social_attribution", "Atribuição social", _subs("causa situacional;causa disposicional;papel;norma;viés de atribuição")),

    SocialCognitionBranch("perspective_expectation", "perspective_taking", "Tomada de perspectiva", _subs("ponto de vista;informação disponível;posição;papel;limites")),
    SocialCognitionBranch("perspective_expectation", "multiple_perspectives", "Múltiplas perspectivas", _subs("perspectivas concorrentes;conflito de interpretação;interesses;contexto")),
    SocialCognitionBranch("perspective_expectation", "expectation_formation", "Formação de expectativas", _subs("expectativa;histórico;norma;promessa;probabilidade;incerteza")),
    SocialCognitionBranch("perspective_expectation", "expectation_violation", "Quebra de expectativa", _subs("surpresa;erro de previsão;mudança;explicações alternativas;revisão")),
    SocialCognitionBranch("perspective_expectation", "role_perspective", "Perspectiva por papel", _subs("papel social;responsabilidade;autoridade;limites;contexto cultural")),

    SocialCognitionBranch("intention_deception", "intention_hypotheses", "Hipóteses de intenção", _subs("objetivo possível;plano possível;declaração;ação;alternativas;incerteza")),
    SocialCognitionBranch("intention_deception", "deception_signals", "Sinais compatíveis com engano", _subs("inconsistência;omissão;contradição;contexto;explicações não enganosas")),
    SocialCognitionBranch("intention_deception", "lie_limits", "Limites para inferir mentira", _subs("mentira exige crença e intenção;erro;memória falha;mal-entendido;incerteza")),
    SocialCognitionBranch("intention_deception", "secrets_privacy", "Segredo, privacidade e informação retida", _subs("segredo;confidencialidade;privacidade;consentimento;necessidade de saber")),
    SocialCognitionBranch("intention_deception", "strategic_information", "Informação estratégica", _subs("revelação parcial;assimetria;timing;negociação;limites éticos")),

    SocialCognitionBranch("trust_reputation", "trust_evidence", "Evidências de confiança", _subs("consistência;cumprimento;competência;honestidade percebida;incerteza")),
    SocialCognitionBranch("trust_reputation", "trust_calibration", "Calibração de confiança", _subs("confiança contextual;risco;verificação;histórico;reversibilidade")),
    SocialCognitionBranch("trust_reputation", "reputation_sources", "Fontes de reputação", _subs("relatos;histórico;fonte;viés;recência;conflito de relatos")),
    SocialCognitionBranch("trust_reputation", "reputation_revision", "Revisão de reputação", _subs("evidência nova;mudança;perdão;recuperação;incerteza")),
    SocialCognitionBranch("trust_reputation", "trust_boundaries", "Limites entre confiança e permissão", _subs("confiança não autoriza;consentimento;escopo;segurança;verificação")),

    SocialCognitionBranch("cooperation_competition", "cooperation_conditions", "Condições de cooperação", _subs("objetivo compartilhado;coordenação;reciprocidade;dependência;confiança")),
    SocialCognitionBranch("cooperation_competition", "competition_conditions", "Condições de competição", _subs("recursos;objetivos incompatíveis;regras;comparação;conflito")),
    SocialCognitionBranch("cooperation_competition", "mixed_motives", "Motivos mistos", _subs("cooperação e competição simultâneas;trade-off;aliança;interesse próprio")),
    SocialCognitionBranch("cooperation_competition", "coordination_failures", "Falhas de coordenação", _subs("mal-entendido;timing;informação incompleta;expectativas;papéis")),
    SocialCognitionBranch("cooperation_competition", "social_dilemmas", "Dilemas sociais", _subs("benefício individual;benefício coletivo;reciprocidade;regras;consequências")),

    SocialCognitionBranch("negotiation", "interests_positions", "Interesses e posições", _subs("posição declarada;interesse subjacente;restrições;prioridades;incerteza")),
    SocialCognitionBranch("negotiation", "alternatives_tradeoffs", "Alternativas e trade-offs", _subs("alternativas;BATNA conceitual;custos;benefícios;concessões;limites")),
    SocialCognitionBranch("negotiation", "offers_counteroffers", "Ofertas e contrapropostas", _subs("oferta;contraproposta;condições;escopo;registro;comparação")),
    SocialCognitionBranch("negotiation", "fairness_reciprocity", "Justiça e reciprocidade", _subs("equidade;reciprocidade;procedimento;percepção;contexto cultural")),
    SocialCognitionBranch("negotiation", "agreement_verification", "Acordo e verificação", _subs("termos;entendimento comum;confirmação;compromisso;revisão")),

    SocialCognitionBranch("persuasion_influence", "persuasion_cues", "Sinais de persuasão", _subs("argumento;credibilidade;emoção;enquadramento;repetição;contexto")),
    SocialCognitionBranch("persuasion_influence", "influence_sources", "Fontes de influência", _subs("autoridade;grupo;norma;reciprocidade;identidade;pressão")),
    SocialCognitionBranch("persuasion_influence", "manipulation_detection", "Detecção de manipulação", _subs("coerção;pressão indevida;engano;exploração de vulnerabilidade;assimetria;proteção")),
    SocialCognitionBranch("persuasion_influence", "autonomy_boundaries", "Autonomia e limites", _subs("consentimento;opção real;recusa;transparência;liberdade de decisão")),
    SocialCognitionBranch("persuasion_influence", "resistance_verification", "Verificação e resistência a influência", _subs("checagem;tempo para decidir;segunda fonte;conflito de interesse;reversibilidade")),

    SocialCognitionBranch("responsibility", "agency", "Agência", _subs("ação;controle;capacidade;conhecimento;alternativas;contexto")),
    SocialCognitionBranch("responsibility", "responsibility_attribution", "Atribuição de responsabilidade", _subs("papel;dever;controle;previsibilidade;contribuição causal;incerteza")),
    SocialCognitionBranch("responsibility", "shared_responsibility", "Responsabilidade compartilhada", _subs("grupo;coordenação;contribuição;dependência;governança")),
    SocialCognitionBranch("responsibility", "accountability", "Prestação de contas", _subs("registro;explicação;critério;consequência;correção")),
    SocialCognitionBranch("responsibility", "responsibility_limits", "Limites de responsabilidade", _subs("coerção;informação limitada;capacidade limitada;acidente;incerteza")),

    SocialCognitionBranch("functional_empathy", "perspective_empathy", "Empatia por perspectiva", _subs("compreender perspectiva;necessidade;contexto;sem presumir sentimento")),
    SocialCognitionBranch("functional_empathy", "emotion_hypotheses", "Hipóteses emocionais", _subs("estado emocional possível;sinais;contexto;alternativas;incerteza")),
    SocialCognitionBranch("functional_empathy", "needs_support", "Necessidades e apoio", _subs("necessidade declarada;apoio;limite;autonomia;adaptação")),
    SocialCognitionBranch("functional_empathy", "empathy_limits", "Limites da empatia", _subs("empatia não é leitura mental;projeção;viés;diferenças individuais")),
    SocialCognitionBranch("functional_empathy", "repair_response", "Resposta e reparação", _subs("escuta;validação;esclarecimento;reparação;feedback")),

    SocialCognitionBranch("relationships_context", "relationship_history", "Histórico de relações", _subs("relações;interações;confiança;conflito;cooperação;mudança;memória social")),
    SocialCognitionBranch("relationships_context", "relationship_roles", "Papéis na relação", _subs("papel;expectativa;limite;responsabilidade;assimetria")),
    SocialCognitionBranch("relationships_context", "relationship_boundaries", "Limites relacionais", _subs("consentimento;privacidade;escopo;distância;revogação")),
    SocialCognitionBranch("relationships_context", "social_context", "Contexto social", _subs("grupo;instituição;cultura;norma;situação;ambiente")),
    SocialCognitionBranch("relationships_context", "relationship_change", "Mudança relacional", _subs("aproximação;distanciamento;ruptura;reparação;renegociação;incerteza")),
)

SOCIAL_COGNITION_LENSES = (
    ("concept", "conceito", "definir o fenômeno sem colapsar hipótese em fato"),
    ("perspective", "perspectiva", "mapear o que cada ator pode perceber, saber ou esperar"),
    ("evidence", "evidência", "separar observações, declarações, memória e inferência"),
    ("intention", "intenção", "manter múltiplas hipóteses de intenção sem leitura mental"),
    ("expectation", "expectativa", "modelar expectativas e violações como previsões revisáveis"),
    ("relation", "relação", "considerar histórico, papéis, confiança e limites"),
    ("context", "contexto", "considerar cultura, situação, normas e assimetrias"),
    ("alternatives", "alternativas", "preservar explicações alternativas e exceções"),
    ("risk", "risco", "avaliar dano, coerção, manipulação e conflito sem autorizar ação"),
    ("limits", "limites", "explicitar incerteza, privacidade, consentimento e limites de inferência"),
)

PERSPECTIVE_AXIS = (
    "self", "other", "observer", "group", "authority", "peer", "dependent", "outsider", "counterparty", "unknown_actor",
)
INTENTION_HYPOTHESIS_AXIS = (
    "cooperate", "compete", "inform", "conceal", "protect", "negotiate", "persuade", "avoid", "repair", "unknown",
)
CONTEXT_AXIS = (
    "conversation", "family", "friendship", "work", "school", "public", "digital", "institutional", "conflict", "cross_cultural",
)
EVIDENCE_AXIS = (
    "direct_observation", "declared_statement", "document", "social_memory", "repeated_pattern", "third_party_report", "behavioral_outcome", "contradiction", "context_only", "insufficient",
)
RELATION_AXIS = (
    "stranger", "acquaintance", "friend", "family", "colleague", "authority", "dependent", "partner", "group_member", "unknown",
)
TEMPORAL_AXIS = (
    "moment", "recent", "session", "day", "week", "month", "longitudinal", "historical", "future_expectation", "unknown",
)
INTERPRETATION_AXIS = ("primary_hypothesis", "alternative_hypothesis")

VARIANT_AXES = (
    ("perspective", PERSPECTIVE_AXIS),
    ("intention_hypothesis", INTENTION_HYPOTHESIS_AXIS),
    ("context", CONTEXT_AXIS),
    ("evidence", EVIDENCE_AXIS),
    ("relationship", RELATION_AXIS),
    ("temporal_scope", TEMPORAL_AXIS),
    ("interpretation_mode", INTERPRETATION_AXIS),
)

CANONICAL_NODES = len(SOCIAL_COGNITION_BRANCHES) * len(SOCIAL_COGNITION_LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in VARIANT_AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE

if len(SOCIAL_COGNITION_DOMAINS) != 10:
    raise RuntimeError("B16 requer 10 domínios")
if len(SOCIAL_COGNITION_BRANCHES) != 50:
    raise RuntimeError(f"B16 requer 50 ramos; encontrados {len(SOCIAL_COGNITION_BRANCHES)}")
if len(SOCIAL_COGNITION_LENSES) != 10:
    raise RuntimeError("B16 requer 10 lentes")
if CANONICAL_NODES != 500 or VARIANTS_PER_NODE != 2_000_000 or ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("escala B16 inválida")

SOCIAL_COGNITION_POLICY = {
    "social_inference_is_fact": False,
    "isolated_signal_proves_intention": False,
    "deception_signal_proves_lie": False,
    "lie_can_be_inferred_without_belief_and_intent_evidence": False,
    "secret_inference_is_certainty": False,
    "reputation_is_fact": False,
    "trust_grants_permission": False,
    "empathy_is_mind_reading": False,
    "manipulation_analysis_provides_exploitation_tactics": False,
    "multiple_hypotheses_required": True,
    "context_and_perspective_required": True,
    "operational_authorization": False,
    "rule": "INFERÊNCIA SOCIAL ≠ FATO; INTENÇÃO ≠ CERTEZA; CONFIANÇA ≠ PERMISSÃO; EMPATIA ≠ LEITURA MENTAL",
}


def _decode_axes(index: int) -> dict[str, str]:
    if not 0 <= int(index) < VARIANTS_PER_NODE:
        raise IndexError(index)
    remainder = int(index)
    decoded: dict[str, str] = {}
    for name, values in reversed(VARIANT_AXES):
        remainder, offset = divmod(remainder, len(values))
        decoded[name] = values[offset]
    return {name: decoded[name] for name, _ in VARIANT_AXES}


class SocialCognitionCatalog:
    NAMESPACE = "B16"
    PREFIX = "SOC-B16"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "domains": len(SOCIAL_COGNITION_DOMAINS),
            "branches": len(SOCIAL_COGNITION_BRANCHES),
            "lenses_per_branch": len(SOCIAL_COGNITION_LENSES),
            "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS,
            "materialization": "on-demand",
            "prepopulated_social_situations": 0,
            "truthfulness_note": "1B are addressable social interpretations/hypotheses, not 1B proven intentions, lies, reputations or personal profiles",
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        if not 0 <= int(node_index) < CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= int(variant_index) < VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = int(node_index) * VARIANTS_PER_NODE + int(variant_index) + 1
        return f"SOC-B16-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"SOC-B16-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, len(SOCIAL_COGNITION_LENSES))
        branch = SOCIAL_COGNITION_BRANCHES[branch_index]
        lens_key, lens_label, instruction = SOCIAL_COGNITION_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {
            "id": f"SOC-B16-{absolute:010d}",
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
                f"Perspectiva={axes['perspective']}; hipótese de intenção={axes['intention_hypothesis']}; "
                f"contexto={axes['context']}; evidência={axes['evidence']}; relação={axes['relationship']}; "
                f"tempo={axes['temporal_scope']}; modo={axes['interpretation_mode']}. "
                "Preservar hipóteses alternativas, incerteza, privacidade e limites de inferência."
            ),
        }


class SocialCognition:
    NAMESPACE = "B16"
    TAXONOMY_ROOT_ID = "SOCIAL-COGNITION-TAX-ROOT"

    def __init__(
        self,
        knowledge: UniversalKnowledgeArchitecture,
        *,
        human_psychology=None,
        society_culture=None,
        internal_models=None,
        memory_continuity=None,
        attention_salience=None,
    ):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.human_psychology = human_psychology
        self.society_culture = society_culture
        self.internal_models = internal_models
        self.memory_continuity = memory_continuity
        self.attention_salience = attention_salience
        self.catalog = SocialCognitionCatalog()
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 16 — INTERPRETAÇÃO, PERSPECTIVA E COGNIÇÃO SOCIAL",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/social_cognition.py",
            metadata={
                "materialization": "on-demand",
                "canonical_gate": "BLOCO 2 -> BLOCO 3",
                "reuses": ["B07", "B09", "B13", "B14", "B15"],
                "shared_knowledge_graph": True,
                "automatic_mind_reading": False,
                "operational_authorization": False,
            },
        )

    @staticmethod
    def _branch(key: str) -> SocialCognitionBranch:
        normalized = _norm(key)
        for branch in SOCIAL_COGNITION_BRANCHES:
            if branch.key == normalized:
                return branch
        raise KeyError(key)

    def perspective_map(
        self,
        actors: Iterable[str],
        *,
        shared_information: Iterable[str] | None = None,
        actor_information: dict[str, Iterable[str]] | None = None,
        declared_goals: dict[str, str] | None = None,
    ) -> dict:
        actors_clean = tuple(dict.fromkeys(_clean(item) for item in actors if _clean(item)))[:32]
        shared = tuple(_clean(item) for item in (shared_information or ()) if _clean(item))[:32]
        actor_information = actor_information or {}
        declared_goals = declared_goals or {}
        perspectives = []
        for actor in actors_clean:
            known = tuple(_clean(item) for item in actor_information.get(actor, ()) if _clean(item))[:32]
            perspectives.append({
                "actor": actor,
                "shared_information": shared,
                "actor_specific_information": known,
                "declared_goal": _clean(declared_goals.get(actor, "")) or None,
                "unknown_information": True,
                "mental_state_is_inferred": False,
            })
        return {
            "perspectives": perspectives,
            "mind_reading": False,
            "certainty_about_private_states": False,
            "operational_authorization": False,
        }

    def interpret_social_situation(
        self,
        observation: str,
        *,
        context: str = "",
        actors: Iterable[str] | None = None,
        declarations: Iterable[str] | None = None,
        evidence: Iterable[str] | None = None,
        relationship: str = "",
        repeated_pattern: bool = False,
    ) -> dict:
        observation = _clean(observation)
        if not observation:
            raise ValueError("observação social vazia")
        actors_clean = tuple(_clean(item) for item in (actors or ()) if _clean(item))[:32]
        declarations_clean = tuple(_clean(item) for item in (declarations or ()) if _clean(item))[:32]
        evidence_clean = tuple(_clean(item) for item in (evidence or ()) if _clean(item))[:32]
        hypotheses = [
            "coordenação ou cooperação compatível com um objetivo compartilhado",
            "competição ou conflito de interesses compatível com o contexto",
            "tentativa de informar ou esclarecer sem intenção estratégica adicional",
            "proteção de privacidade, limite ou informação confidencial",
            "mal-entendido, memória incompleta ou perspectiva diferente",
            "gestão de impressão ou persuasão sem que isso prove manipulação",
            "evitação, autoproteção ou redução de conflito",
            "combinação de fatores ainda não observados",
        ]
        if repeated_pattern:
            hypotheses.append("padrão recorrente que aumenta relevância longitudinal, mas ainda não prova intenção privada")
        return {
            "observation": observation,
            "context": _clean(context),
            "actors": actors_clean,
            "declarations": declarations_clean,
            "evidence": evidence_clean,
            "relationship": _clean(relationship),
            "repeated_pattern": bool(repeated_pattern),
            "epistemic_kind": "inference",
            "certainty": "underdetermined",
            "intention": None,
            "intention_certainty": False,
            "lie_detected": False,
            "deception_certainty": False,
            "secret_certainty": False,
            "possible_hypotheses": hypotheses,
            "alternative_hypotheses_required": True,
            "missing_context": [
                "informação efetivamente disponível a cada ator",
                "declarações diretas de objetivos/intenção",
                "histórico e frequência das interações",
                "normas culturais, institucionais e relacionais",
                "evidência independente para contradições ou alegações de engano",
            ],
            "policy": deepcopy(SOCIAL_COGNITION_POLICY),
        }

    def assess_deception(self, *, signals: Iterable[str] | None = None, evidence: Iterable[str] | None = None) -> dict:
        signal_items = tuple(_clean(item) for item in (signals or ()) if _clean(item))[:32]
        evidence_items = tuple(_clean(item) for item in (evidence or ()) if _clean(item))[:32]
        return {
            "signals": signal_items,
            "evidence": evidence_items,
            "deception_possible": bool(signal_items),
            "lie_proven": False,
            "intent_to_deceive_proven": False,
            "alternative_explanations": (
                "erro factual sem intenção de enganar",
                "memória incompleta ou imprecisa",
                "mal-entendido ou diferença de perspectiva",
                "informação desatualizada",
                "privacidade ou omissão legítima",
            ),
            "requires_belief_and_intent_evidence_for_lie_claim": True,
            "epistemic_kind": "inference",
        }

    def assess_trust(self, entity: str, evidence: Iterable[dict] | None = None) -> dict:
        entity = _clean(entity)
        if not entity:
            raise ValueError("entidade vazia")
        items = []
        weighted = 0.0
        weight_total = 0.0
        for raw in list(evidence or ())[:64]:
            if not isinstance(raw, dict):
                continue
            outcome = _clamp(raw.get("outcome", 0.5))
            reliability = _clamp(raw.get("reliability", 0.5))
            weighted += outcome * reliability
            weight_total += reliability
            items.append({
                "source": _clean(raw.get("source")) or "unknown",
                "outcome": outcome,
                "reliability": reliability,
                "context": _clean(raw.get("context")),
            })
        score = 0.5 if weight_total == 0 else weighted / weight_total
        return {
            "entity": entity,
            "contextual_trust_score": round(score, 6),
            "evidence": items,
            "reputation_is_fact": False,
            "trust_is_contextual_and_revisable": True,
            "grants_permission": False,
            "operational_authorization": False,
        }

    def analyze_influence(self, message: str, *, context: str = "") -> dict:
        message = _clean(message)
        if not message:
            raise ValueError("mensagem vazia")
        low = _norm(message)
        cue_terms = {
            "urgency_pressure": ("agora", "imediatamente", "ultima_chance", "urgente"),
            "authority_pressure": ("autoridade", "ordem", "chefe", "obrigatorio"),
            "scarcity_pressure": ("escasso", "limitado", "ultimo", "somente_hoje"),
            "secrecy_pressure": ("segredo", "nao_conte", "ninguem_pode_saber"),
        }
        detected = [name for name, terms in cue_terms.items() if any(term in low for term in terms)]
        return {
            "message": message,
            "context": _clean(context),
            "influence_cues": detected,
            "manipulation_proven": False,
            "coercion_proven": False,
            "recommended_cognitive_checks": [
                "verificar fatos e fonte independentemente",
                "separar pressão temporal de urgência real",
                "identificar conflitos de interesse",
                "preservar opção de recusa e reversibilidade",
            ],
            "provides_manipulation_tactics": False,
            "operational_authorization": False,
        }

    def remember_social_context(
        self,
        content: str,
        *,
        source: str,
        reference: str,
        entities: Iterable[str] | None = None,
        context: dict | None = None,
        importance: float = 0.5,
    ) -> dict:
        if self.memory_continuity is None:
            raise RuntimeError("B13 MemoryContinuity não anexada")
        return self.memory_continuity.remember(
            "social",
            content,
            source=source,
            reference=reference,
            entities=entities,
            context=context,
            importance=importance,
            meaning="contexto social auditável para continuidade; não prova intenção privada",
            metadata={"block": "B16", "social_cognition": True},
        )

    def select_evidence(self, candidates: Iterable[dict], *, limit: int = 16) -> dict:
        if self.attention_salience is None:
            sampled = list(candidates)[: max(1, min(int(limit), 16))]
            return {"selected": sampled, "bounded": True, "attention_source": None, "operational_authorization": False}
        result = self.attention_salience.select_relevant(candidates, limit=limit)
        return {**result, "bounded": True, "attention_source": "B14"}

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        domain_key = _norm(domain) if domain else None
        if domain_key and domain_key not in SOCIAL_COGNITION_DOMAINS:
            raise KeyError(domain)
        selected = [branch for branch in SOCIAL_COGNITION_BRANCHES if domain_key is None or branch.domain == domain_key]
        root = self.graph.add_entity(
            "social_cognition_taxonomy",
            "INTERPRETAÇÃO, PERSPECTIVA E COGNIÇÃO SOCIAL",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B16", "source": "core/social_cognition.py", "mind_reading": False},
        )
        for source_id, label, block in (
            ("PSY-TAX-ROOT", "B07 Psicologia e Cognição Social", "B07"),
            ("SOC-TAX-ROOT", "B09 Sociedade e Cultura", "B09"),
            ("INTERNAL-MODELS-TAX-ROOT", "B15 Modelos Internos", "B15"),
        ):
            self.graph.add_entity("social_cognition_source", label, node_id=source_id, data={"block": block})
            self.graph.relate(root, source_id, "extends", metadata={"block": "B16"})
        for branch in selected:
            domain_id = f"SC-DOM-{branch.domain.upper()}"
            branch_id = f"SC-BR-{branch.key.upper()}"
            self.graph.add_entity("social_cognition_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id, data={"block": "B16"})
            self.graph.add_entity("social_cognition_branch", branch.label, node_id=branch_id, data={"block": "B16", "domain": branch.domain})
            self.graph.relate(root, domain_id, "has_part", metadata={"block": "B16", "taxonomy": True})
            self.graph.relate(domain_id, branch_id, "has_part", metadata={"block": "B16", "taxonomy": True})
        return {
            "domain": domain_key,
            "branches_materialized": len(selected),
            "knowledge_graph": "shared",
            "parallel_social_model_created": False,
            "mind_reading_engine_created": False,
        }

    def promote_canonical_social_knowledge(
        self,
        record_id: str,
        canonical_label: str,
        *,
        domain: str,
        branch: str,
        knowledge_type: str = "concept",
        aliases=None,
        properties=None,
        summary: str = "",
    ) -> dict:
        domain_key = _norm(domain)
        if domain_key not in SOCIAL_COGNITION_DOMAINS:
            raise ValueError(f"domínio B16 inválido: {domain}")
        branch_obj = self._branch(branch)
        if branch_obj.domain != domain_key:
            raise ValueError(f"ramo {branch} não pertence a {domain_key}")
        props = dict(properties or {})
        props.update({
            "intention_certainty": False,
            "automatic_lie_detection": False,
            "automatic_mind_reading": False,
            "trust_grants_permission": False,
            "knowledge_scope": "social_cognition_and_interpretation",
        })
        result = self.knowledge.promote_canonical(
            record_id,
            canonical_label,
            knowledge_type=knowledge_type,
            namespace=self.NAMESPACE,
            summary=summary,
            aliases=aliases,
            properties=props,
            categories=["social_cognition", domain_key, branch_obj.key],
            provenance={
                "social_cognition_block": "B16",
                "domain": domain_key,
                "branch": branch_obj.key,
                "source_record_id": record_id,
                "automatic_mind_reading": False,
            },
        )
        branch_id = f"SC-BR-{branch_obj.key.upper()}"
        self.materialize_taxonomy(domain_key)
        self.graph.relate(result["knowledge_id"], branch_id, "is_a", metadata={"block": "B16"})
        return result

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "knowledge_graph": "shared knowledge_nodes/knowledge_edges",
            "reuses": ["B07", "B09", "B13", "B14", "B15"],
            "parallel_social_model": False,
            "policy": deepcopy(SOCIAL_COGNITION_POLICY),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {
            "status bloco 16", "status cognicao social", "status cognição social",
            "interpretacao e cognicao social", "interpretação e cognição social",
        }:
            stats = self.stats()
            return (
                f"⭐ BLOCO 16 — COGNIÇÃO SOCIAL: {stats['catalog']['addressable_contents']} representações endereçáveis | "
                f"{stats['catalog']['branches']} ramos × {stats['catalog']['lenses_per_branch']} lentes | "
                "inferência social permanece hipotética, contextual e não autorizadora."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"⭐ {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        if low in {"politica cognicao social", "política cognição social", "limites cognicao social", "limites cognição social"}:
            return "🛡️ B16: inferência social ≠ fato; intenção ≠ certeza; confiança ≠ permissão; empatia ≠ leitura mental; sinais de engano não provam mentira."
        return None
