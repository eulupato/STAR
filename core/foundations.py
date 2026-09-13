"""BLOCO 1 — fundamentos cognitivos e princípios invioláveis da STAR.

Este módulo é a fonte de verdade operacional do BLOCO 1. Ele não cria uma
segunda identidade, um segundo cérebro ou um sistema de permissões paralelo.
A identidade continua em ``core.star_identity``; este bloco formaliza o ciclo
cognitivo, os cinco modelos de situação, as separações invioláveis e a
fronteira entre cognição e ação.

O catálogo de 1B é virtual/endereço-lógico: 1.000 nós canônicos × 1.000.000 de
combinações determinísticas. As representações são materializadas sob demanda;
não existem um bilhão de fatos, arquivos ou linhas pré-carregadas.
"""
from __future__ import annotations

from copy import deepcopy
import re

from core.cognitive_catalog import CONTEXTS, FAMILIES, LENSES, STYLES


COGNITIVE_CYCLE = (
    {"key": "perceive", "label": "PERCEBER", "purpose": "receber sinais, dados, eventos ou linguagem sem ainda tratá-los como verdade interpretada"},
    {"key": "identify", "label": "IDENTIFICAR", "purpose": "reconhecer entidades, padrões, intenções aparentes e elementos relevantes"},
    {"key": "understand", "label": "COMPREENDER", "purpose": "construir significado operacional para o que foi identificado"},
    {"key": "contextualize", "label": "CONTEXTUALIZAR", "purpose": "situar a informação no tempo, ambiente, tarefa, memória e restrições atuais"},
    {"key": "relate", "label": "RELACIONAR", "purpose": "conectar entidades, fatos, memórias, hipóteses, pessoas, objetivos e causas possíveis"},
    {"key": "predict", "label": "PREVER", "purpose": "estimar consequências e estados futuros sem confundir previsão com fato"},
    {"key": "interpret", "label": "INTERPRETAR", "purpose": "integrar evidências, incerteza, contexto e relações em uma leitura coerente da situação"},
    {"key": "decide", "label": "DECIDIR", "purpose": "selecionar uma resposta, plano ou intenção compatível com objetivos, limites e regras"},
    {"key": "act", "label": "AGIR", "purpose": "executar somente quando capacidade, segurança e autorização operacional permitirem"},
    {"key": "observe", "label": "OBSERVAR", "purpose": "medir o resultado real da resposta ou ação e detectar divergências"},
    {"key": "learn", "label": "APRENDER", "purpose": "atualizar conhecimento, memória ou estratégia sem redefinir silenciosamente a identidade fundamental"},
)


COGNITIVE_MODEL_DEFINITIONS = {
    "world_model": {
        "label": "WORLD MODEL",
        "scope": "mundo externo",
        "purpose": "representar entidades, ambiente, objetos, eventos, relações causais, espaço, tempo e estado observável do mundo",
        "rules": (
            "observação não equivale automaticamente a causa",
            "estado estimado deve preservar incerteza",
            "ficção, hipótese, simulação e realidade devem permanecer distinguíveis",
        ),
    },
    "human_model": {
        "label": "HUMAN MODEL",
        "scope": "pessoas",
        "purpose": "representar informações declaradas ou legitimamente observadas sobre uma pessoa para melhorar contexto e interação",
        "rules": (
            "não inferir automaticamente atributos sensíveis",
            "preferir informação declarada e proveniência auditável",
            "reconhecimento não equivale a autenticação nem autorização",
        ),
    },
    "social_model": {
        "label": "SOCIAL MODEL",
        "scope": "relações e contexto social",
        "purpose": "representar papéis, relações, normas, expectativas, turnos de interação, confiança e permissões sociais conhecidas",
        "rules": (
            "papel social não concede permissão operacional por si só",
            "tratar relações como contexto, não como prova absoluta",
            "preservar mudanças, conflitos e incerteza relacional",
        ),
    },
    "self_model": {
        "label": "SELF MODEL",
        "scope": "a própria STAR",
        "purpose": "representar capacidades, limitações, estado, recursos, identidade, memória disponível e grau de confiança da STAR",
        "rules": (
            "modelo, corpo ou serviço não substituem a identidade da STAR",
            "o SELF MODEL descreve o estado atual; não redefine princípios fundamentais",
            "capacidades indisponíveis devem permanecer explicitamente indisponíveis",
        ),
    },
    "situation_model": {
        "label": "SITUATION MODEL",
        "scope": "situação atual integrada",
        "purpose": "combinar WORLD, HUMAN, SOCIAL e SELF com objetivo, tarefa, tempo, evidência, risco e permissões para representar o agora",
        "rules": (
            "é temporário e revisável",
            "deve separar fatos, observações, inferências, hipóteses e desconhecidos",
            "uma decisão operacional deve consultar limites e autorização além do modelo da situação",
        ),
    },
}


INVIOLABLE_DISTINCTIONS = {
    "model_not_star": {
        "statement": "MODELO ≠ STAR",
        "meaning": "um modelo de IA é um recurso cognitivo substituível; a STAR é a arquitetura completa e sua identidade persistente",
    },
    "body_not_star": {
        "statement": "CORPO ≠ STAR",
        "meaning": "PC, celular, Watch, robô, avatar ou futuro corpo são interfaces/encarnações; a identidade da STAR não fica presa a um corpo",
    },
    "ai_not_star": {
        "statement": "IA ≠ STAR",
        "meaning": "um motor, serviço ou agente de IA isolado não é a STAR; pode ser utilizado por ela sem assumir sua identidade",
    },
    "thinking_not_action": {
        "statement": "PENSAR ≠ AGIR",
        "meaning": "raciocinar, planejar, imaginar ou recomendar não autoriza nem executa automaticamente uma ação externa",
    },
    "curiosity_not_authorization": {
        "statement": "CURIOSIDADE ≠ AUTORIZAÇÃO",
        "meaning": "curiosidade pode motivar investigação cognitiva, mas nunca concede por si só permissão para operar sistemas, dados ou dispositivos",
    },
    "inference_not_fact": {
        "statement": "INFERÊNCIA ≠ FATO",
        "meaning": "deduções, previsões e hipóteses permanecem marcadas como inferências até que evidência suficiente permita outra classificação",
    },
    "cognitive_not_operational_autonomy": {
        "statement": "AUTONOMIA COGNITIVA ≠ AUTONOMIA OPERACIONAL",
        "meaning": "a STAR pode analisar, aprender, comparar e formar hipóteses sem receber automaticamente autoridade para executar ações no mundo",
    },
}


FOUNDATION_AREAS = (
    ("identity", "identidade e continuidade"),
    ("model_role", "papel de modelos e motores de IA"),
    ("body_role", "corpo, interfaces e endpoints"),
    ("perception", "percepção e entrada"),
    ("identification", "identificação e classificação"),
    ("understanding", "compreensão"),
    ("context", "contextualização"),
    ("relations", "relações e causalidade"),
    ("prediction", "previsão e antecipação"),
    ("interpretation", "interpretação"),
    ("decision", "decisão"),
    ("action", "ação e execução"),
    ("observation", "observação de resultados"),
    ("learning", "aprendizado e atualização"),
    ("world_model", "WORLD MODEL"),
    ("human_model", "HUMAN MODEL"),
    ("social_model", "SOCIAL MODEL"),
    ("self_model", "SELF MODEL"),
    ("situation_model", "SITUATION MODEL"),
    ("limits", "limites, permissões e autonomia"),
)

EPISTEMIC_STATES = (
    "fato_validado",
    "observacao",
    "informacao_declarada",
    "memoria",
    "inferencia",
    "hipotese",
    "previsao",
    "opiniao_funcional",
    "desconhecido",
    "conflito",
)

AUTHORITY_STATES = (
    "sem_autorizacao",
    "identidade_fundamental",
    "instrucao_do_criador",
    "usuario_autorizado",
    "permissao_do_sistema",
    "permissao_de_ferramenta",
    "permissao_de_dispositivo",
    "fonte_externa",
    "saida_de_modelo",
    "informacao_nao_verificada",
)

OPERATION_STATES = (
    "pensar",
    "analisar",
    "perguntar",
    "aguardar",
    "simular",
    "recomendar",
    "solicitar_autorizacao",
    "acao_somente_leitura",
    "acao_reversivel",
    "acao_irreversivel",
)

FOUNDATION_CANONICAL_NODES = len(FOUNDATION_AREAS) * len(LENSES)
FOUNDATION_VARIANTS_PER_NODE = (
    len(FAMILIES)
    * len(STYLES)
    * len(CONTEXTS)
    * len(EPISTEMIC_STATES)
    * len(AUTHORITY_STATES)
    * len(OPERATION_STATES)
)
FOUNDATION_ADDRESSABLE_CONTENTS = FOUNDATION_CANONICAL_NODES * FOUNDATION_VARIANTS_PER_NODE

if FOUNDATION_CANONICAL_NODES != 1_000:
    raise RuntimeError("BLOCO 1 deve manter exatamente 1.000 nós canônicos")
if FOUNDATION_VARIANTS_PER_NODE != 1_000_000:
    raise RuntimeError("BLOCO 1 deve manter exatamente 1.000.000 combinações por nó")
if FOUNDATION_ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("BLOCO 1 deve manter exatamente 1B de representações endereçáveis")


class CognitiveCycle:
    """Contrato ordenado do ciclo cognitivo, sem executar ações por conta própria."""

    def stages(self) -> list[dict]:
        return deepcopy(list(COGNITIVE_CYCLE))

    def labels(self) -> tuple[str, ...]:
        return tuple(stage["label"] for stage in COGNITIVE_CYCLE)

    def next_stage(self, label_or_key: str) -> dict | None:
        value = str(label_or_key or "").strip().lower()
        for index, stage in enumerate(COGNITIVE_CYCLE):
            if value in {stage["key"].lower(), stage["label"].lower()}:
                return deepcopy(COGNITIVE_CYCLE[index + 1]) if index + 1 < len(COGNITIVE_CYCLE) else None
        raise KeyError(label_or_key)


class CognitiveModels:
    """Cinco modelos explícitos com separação entre evidência e inferência."""

    KINDS = ("facts", "observations", "declared", "memories", "inferences", "hypotheses", "predictions", "unknowns")

    def __init__(self):
        self._frames = {
            key: {"definition": deepcopy(spec), **{kind: [] for kind in self.KINDS}, "context": {}}
            for key, spec in COGNITIVE_MODEL_DEFINITIONS.items()
        }

    def names(self) -> tuple[str, ...]:
        return tuple(self._frames)

    def definition(self, name: str) -> dict:
        if name not in self._frames:
            raise KeyError(name)
        return deepcopy(self._frames[name]["definition"])

    def record(
        self,
        name: str,
        kind: str,
        value,
        *,
        source: str | None = None,
        confidence: float | None = None,
    ) -> dict:
        if name not in self._frames:
            raise KeyError(name)
        if kind not in self.KINDS:
            raise ValueError(f"classe epistêmica inválida: {kind}")
        if kind == "facts" and not str(source or "").strip():
            raise ValueError("fatos exigem fonte/proveniência; inferência não pode ser promovida silenciosamente a fato")
        item = {
            "value": deepcopy(value),
            "source": source,
            "confidence": None if confidence is None else max(0.0, min(float(confidence), 1.0)),
            "epistemic_class": kind,
        }
        self._frames[name][kind].append(item)
        return deepcopy(item)

    def set_context(self, name: str, **context) -> dict:
        if name not in self._frames:
            raise KeyError(name)
        self._frames[name]["context"].update(deepcopy(context))
        return deepcopy(self._frames[name]["context"])

    def snapshot(self, name: str) -> dict:
        if name not in self._frames:
            raise KeyError(name)
        return deepcopy(self._frames[name])

    def situation(self) -> dict:
        return {
            "model": "SITUATION MODEL",
            "world": self.snapshot("world_model"),
            "human": self.snapshot("human_model"),
            "social": self.snapshot("social_model"),
            "self": self.snapshot("self_model"),
            "situation": self.snapshot("situation_model"),
            "note": "síntese auditável; inferências permanecem separadas de fatos",
        }


class OperationalBoundary:
    """Gate determinístico entre cognição e execução operacional."""

    def evaluate(
        self,
        intent: str,
        *,
        permission: bool = False,
        capability: bool = False,
        safety_ok: bool = False,
        curiosity: bool = False,
        inference_available: bool = False,
        cognitive_autonomy: bool = True,
        authorization_source: str | None = None,
    ) -> dict:
        # Curiosidade, inferência e autonomia cognitiva são contexto; nunca grants.
        requirements = {
            "permission": bool(permission),
            "capability": bool(capability),
            "safety_ok": bool(safety_ok),
        }
        can_act = all(requirements.values())
        missing = [name for name, ok in requirements.items() if not ok]
        return {
            "intent": str(intent or "").strip(),
            "can_act": can_act,
            "missing": missing,
            "authorization_source": authorization_source if permission else None,
            "cognitive_context": {
                "curiosity": bool(curiosity),
                "inference_available": bool(inference_available),
                "cognitive_autonomy": bool(cognitive_autonomy),
            },
            "rule": "PENSAR ≠ AGIR; CURIOSIDADE ≠ AUTORIZAÇÃO; AUTONOMIA COGNITIVA ≠ AUTONOMIA OPERACIONAL",
        }


class FoundationalContentCatalog:
    """Catálogo virtual de 1B de representações operacionais do BLOCO 1."""

    PREFIX = "FOUND"

    def stats(self) -> dict:
        return {
            "areas": len(FOUNDATION_AREAS),
            "lenses_per_area": len(LENSES),
            "canonical_nodes": FOUNDATION_CANONICAL_NODES,
            "variants_per_node": FOUNDATION_VARIANTS_PER_NODE,
            "addressable_contents": FOUNDATION_ADDRESSABLE_CONTENTS,
            "materialization": "on-demand",
            "prepopulated_fact_rows": 0,
            "truthfulness_note": "1B são combinações operacionais endereçáveis; não 1B de fatos independentes pesquisados",
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        if not 0 <= int(node_index) < FOUNDATION_CANONICAL_NODES:
            raise IndexError("nó fundamental inválido")
        if not 0 <= int(variant_index) < FOUNDATION_VARIANTS_PER_NODE:
            raise IndexError("variante fundamental inválida")
        number = int(node_index) * FOUNDATION_VARIANTS_PER_NODE + int(variant_index) + 1
        return f"FOUND-{number:010d}"

    @staticmethod
    def _indices(variant_index: int) -> tuple[int, int, int, int, int, int]:
        value = int(variant_index)
        factors = []
        for _ in range(6):
            value, remainder = divmod(value, 10)
            factors.append(remainder)
        return tuple(reversed(factors))

    def get_variant(self, content_id: str) -> dict | None:
        match = re.fullmatch(r"FOUND-(\d{10})", str(content_id or "").upper())
        if not match:
            return None
        number = int(match.group(1))
        if not 1 <= number <= FOUNDATION_ADDRESSABLE_CONTENTS:
            return None
        zero = number - 1
        node_index, variant_index = divmod(zero, FOUNDATION_VARIANTS_PER_NODE)
        area_index, lens_index = divmod(node_index, len(LENSES))
        area_key, area_label = FOUNDATION_AREAS[area_index]
        lens_key, lens_label = LENSES[lens_index]
        family_i, style_i, context_i, epistemic_i, authority_i, operation_i = self._indices(variant_index)
        result = {
            "id": self.content_id(node_index, variant_index),
            "node_index": node_index,
            "variant_index": variant_index,
            "area": area_key,
            "area_label": area_label,
            "lens": lens_key,
            "lens_label": lens_label,
            "family": FAMILIES[family_i],
            "style": STYLES[style_i],
            "context": CONTEXTS[context_i],
            "epistemic_state": EPISTEMIC_STATES[epistemic_i],
            "authority_state": AUTHORITY_STATES[authority_i],
            "operation_state": OPERATION_STATES[operation_i],
        }
        result["prompt"] = (
            f"Aplicar {result['family']} em {area_label}, pela lente '{lens_label}', "
            f"no contexto {result['context']}; preservar estado epistêmico "
            f"{result['epistemic_state']}, autoridade {result['authority_state']} e operação "
            f"{result['operation_state']}. Nunca converter inferência em fato nem cognição em autorização."
        )
        return result


class FoundationSuite:
    """Interface central e reutilizável do BLOCO 1."""

    def __init__(self, identity=None):
        self.identity = identity
        self.cycle = CognitiveCycle()
        self.models = CognitiveModels()
        self.boundary = OperationalBoundary()
        self.catalog = FoundationalContentCatalog()

    def principles(self) -> list[str]:
        base = []
        if self.identity is not None:
            try:
                base = list(self.identity.get_principles())
            except AttributeError:
                base = []
        inviolable = [item["statement"] for item in INVIOLABLE_DISTINCTIONS.values()]
        return list(dict.fromkeys([*base, *inviolable]))

    def definitions(self) -> dict:
        return {
            "cycle": self.cycle.stages(),
            "models": deepcopy(COGNITIVE_MODEL_DEFINITIONS),
            "distinctions": deepcopy(INVIOLABLE_DISTINCTIONS),
        }

    def stats(self) -> dict:
        catalog = self.catalog.stats()
        return {
            "status": "experimental-v2-foundation",
            "cycle_stages": len(COGNITIVE_CYCLE),
            "cognitive_models": len(COGNITIVE_MODEL_DEFINITIONS),
            "inviolable_distinctions": len(INVIOLABLE_DISTINCTIONS),
            "addressable_contents": catalog["addressable_contents"],
            "materialization": catalog["materialization"],
            "prepopulated_fact_rows": catalog["prepopulated_fact_rows"],
            "operational_autonomy_from_cognition": False,
        }

    def handle(self, text: str) -> str | None:
        raw = " ".join(str(text or "").strip().split())
        low = raw.lower()
        if low in {"status fundamentos", "status bloco 1", "status princípios", "status principios"}:
            stats = self.stats()
            return (
                "⭐ BLOCO 1: "
                f"{stats['cycle_stages']} etapas cognitivas | "
                f"{stats['cognitive_models']} modelos | "
                f"{stats['inviolable_distinctions']} distinções invioláveis | "
                f"{stats['addressable_contents']} representações endereçáveis sob demanda."
            )
        if low in {"princípios invioláveis", "principios inviolaveis", "regras invioláveis", "regras inviolaveis"}:
            return "⭐ Princípios invioláveis:\n" + "\n".join(
                f"- {item['statement']}: {item['meaning']}" for item in INVIOLABLE_DISTINCTIONS.values()
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"⭐ {item['id']} — {item['area_label']} / {item['lens_label']}\n{item['prompt']}"
        return None
