"""Intenções locais da STAR TV.

Este parser apenas descreve a ação desejada. A execução visual pertence à GUI
via Event Bus.
"""
from __future__ import annotations

import re
import unicodedata


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFD", str(text or "").lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())


def parse_media_intent(text: str) -> dict | None:
    value = normalize(text)

    tv_words = ("tv", "televisao", "televisão", "star tv")
    mentions_tv = any(word in value for word in tv_words)

    if "youtube" in value and (
        mentions_tv
        or any(
            phrase in value
            for phrase in (
                "abrir youtube",
                "abre youtube",
                "abra youtube",
                "coloca youtube",
                "coloque youtube",
            )
        )
    ):
        return {"action": "open_youtube", "source": "youtube"}

    if not mentions_tv:
        return None

    if any(term in value for term in ("restaurar", "voltar tamanho", "sair da tela cheia")):
        return {"action": "restore"}

    if any(term in value for term in ("tela cheia", "fullscreen", "ampliar", "maximizar")):
        return {"action": "fullscreen"}

    if any(term in value for term in ("fechar", "desligar", "desliga")):
        return {"action": "close"}

    if any(term in value for term in ("pausar", "pausa", "pause")):
        return {"action": "pause"}

    if any(term in value for term in ("continuar", "reproduzir", "play", "retomar")):
        return {"action": "play"}

    volume = re.search(
        r"volume(?:\s+(?:da|do)?\s*(?:star\s+)?tv)?(?:\s+(?:em|para))?\s+(\d{1,3})",
        value,
    )
    if volume:
        return {
            "action": "volume",
            "value": max(0, min(100, int(volume.group(1)))),
        }

    return None
