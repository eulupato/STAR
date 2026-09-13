"""Catálogo temático de voz da STAR: exatamente 1.000.000 de variações.

Seis dimensões de dez opções (10^6). O catálogo é endereçável e gerado sob
demanda; não materializa um milhão de strings na memória.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from core.commands import strip_wake_word
from core.multidisciplinary_taxonomy import SUBJECT_ORDER, SUBJECTS

ACTIONS = (
    "explique", "me ensine", "resuma", "compare", "revise comigo",
    "me faça perguntas sobre", "aprofunde", "conecte", "exemplifique", "verifique meu entendimento de",
)
TONES = (
    "de forma direta", "de forma intuitiva", "didaticamente", "tecnicamente", "com calma",
    "com linguagem simples", "com rigor", "como tutor", "como revisão", "como pesquisador",
)
DEPTHS = (
    "do zero", "no nível básico", "no nível intermediário", "no nível avançado", "no nível de graduação",
    "no nível profissional", "no nível de pesquisa", "do básico ao avançado", "com foco conceitual", "com foco quantitativo",
)
FORMATS = (
    "usando definição e exemplo", "com perguntas e respostas", "com um problema guiado", "com comparação",
    "com erros comuns", "com fontes e evidências", "com conexões interdisciplinares", "com uma síntese",
    "com um desafio final", "com checagem passo a passo",
)
CONTEXTS = (
    "para estudo", "para revisão", "para prova", "para projeto", "para pesquisa",
    "para aplicação prática", "para conversa", "para aula", "para exercício", "para aprofundamento",
)
CLOSERS = (
    "e termine com uma pergunta", "e termine com um resumo", "e destaque os limites", "e mostre uma curiosidade",
    "e diga o que costuma confundir", "e conecte a outra área", "e confira se entendi", "e proponha um exemplo",
    "e mostre a evidência", "e indique o próximo passo de estudo",
)

THEMATIC_VOICE_VARIATIONS = 1_000_000

_STUDY_PREFIXES = (
    "explique ", "me explique ", "explica ", "me ensine ", "ensine ", "resuma ", "resumir ",
    "compare ", "revise comigo ", "revise ", "revisar ", "me faca perguntas sobre ", "me faça perguntas sobre ",
    "aprofunde ", "conecte ", "exemplifique ", "verifique meu entendimento de ", "fale sobre ",
    "quero aprender ", "quero estudar ", "estude comigo ", "estudar ", "me conte sobre ",
)

@dataclass(frozen=True)
class ThematicVoiceMatch:
    query: str
    action: str
    original: str


def thematic_voice_id(index: int) -> str:
    if not 0 <= index < THEMATIC_VOICE_VARIATIONS:
        raise IndexError("índice fora de VOICE-STUDY-000001..VOICE-STUDY-1000000")
    return f"VOICE-STUDY-{index + 1:07d}"


def thematic_voice_variant(index: int) -> dict:
    if not 0 <= index < THEMATIC_VOICE_VARIATIONS:
        raise IndexError("índice fora do catálogo temático")
    n = index
    closer_i = n % 10; n //= 10
    context_i = n % 10; n //= 10
    format_i = n % 10; n //= 10
    depth_i = n % 10; n //= 10
    tone_i = n % 10; n //= 10
    action_i = n % 10

    anchors = []
    for subject in SUBJECT_ORDER:
        for area in SUBJECTS[subject]["areas"]:
            anchors.append((subject, area))
    subject, area = anchors[index % len(anchors)]
    phrase = (
        f"STAR, {ACTIONS[action_i]} {area} {TONES[tone_i]} {DEPTHS[depth_i]} "
        f"{FORMATS[format_i]} {CONTEXTS[context_i]} {CLOSERS[closer_i]}"
    )
    return {
        "id": thematic_voice_id(index),
        "phrase": phrase,
        "subject": subject,
        "subject_label": SUBJECTS[subject]["label"],
        "topic": area,
        "action": ACTIONS[action_i],
        "tone": TONES[tone_i],
        "depth": DEPTHS[depth_i],
        "format": FORMATS[format_i],
        "context": CONTEXTS[context_i],
        "closer": CLOSERS[closer_i],
    }


def thematic_voice_stats() -> dict:
    return {
        "variations": THEMATIC_VOICE_VARIATIONS,
        "model": "10 actions x 10 tones x 10 depths x 10 formats x 10 contexts x 10 closers",
        "subjects": len(SUBJECT_ORDER),
        "topic_anchors": sum(len(SUBJECTS[s]["areas"]) for s in SUBJECT_ORDER),
        "materialization": "on-demand",
    }


def parse_thematic_voice(text: str) -> ThematicVoiceMatch | None:
    original = str(text or "")
    value = strip_wake_word(original)
    normalized = value.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    for prefix in sorted(_STUDY_PREFIXES, key=len, reverse=True):
        if normalized.startswith(prefix):
            query = value[len(prefix):].strip(" .,:;?!")
            if query:
                return ThematicVoiceMatch(query=query, action=prefix.strip(), original=original)
    return None
