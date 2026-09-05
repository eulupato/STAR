"""Registro central do STAR WORLD 2D.

Este módulo é a fonte única de verdade da topologia visual da V1.9. Ambientes
internos permanecem aninhados para evitar duplicação: Sala/Cozinha/Quarto/Closet
pertencem à Casa, Central de Criação pertence ao Laboratório e os quatro mundos
do Jardim permanecem dentro do Jardim.

O campo ``status`` descreve a capacidade real atual. ``enterable`` descreve se a
interface 2D já pode ser aberta. Assim a STAR não precisa fingir que um motor
científico ou um subsistema futuro está pronto só porque sua sala já existe.
"""
from __future__ import annotations

from copy import deepcopy

STATUS_LABELS = {
    "available": "DISPONÍVEL",
    "development": "EM DESENVOLVIMENTO",
    "planned": "PLANEJADO",
    "experimental": "EXPERIMENTAL",
    "restricted": "RESTRITO",
    "unavailable": "INDISPONÍVEL",
}

ISLANDS = {
    "casa": {
        "name": "Casa",
        "icon": "🏠",
        "status": "available",
        "enterable": True,
        "type": "home",
        "description": "A casa da STAR: Sala, Cozinha e Quarto. O Closet fica dentro do Quarto.",
        "contents": ["Sala / STAR TV", "Cozinha / receitas", "Quarto", "Closet / skins"],
        "subareas": {
            "sala": {"name": "Sala", "icon": "📺", "status": "available", "enterable": True,
                     "description": "Conversa, descanso e mídia. A TV abre conteúdo do YouTube com validação de URL."},
            "cozinha": {"name": "Cozinha", "icon": "🍳", "status": "available", "enterable": True,
                        "description": "Receitas, ingredientes, preparo guiado e favoritos culinários."},
            "quarto": {"name": "Quarto", "icon": "🛏️", "status": "available", "enterable": True,
                       "description": "Espaço pessoal da STAR e acesso ao Closet."},
            "closet": {"name": "Closet", "icon": "👕", "status": "available", "enterable": True,
                       "description": "Skins e aparência visual da STAR."},
        },
    },
    "laboratorio": {
        "name": "Laboratório",
        "icon": "🧪",
        "status": "experimental",
        "enterable": True,
        "type": "workspace",
        "description": "Investigação, pesquisa, hipóteses, observações e simulações educacionais seguras.",
        "contents": ["Projetos científicos", "Hipóteses", "Observações", "Central de Criação"],
        "subareas": {
            "central_criacao": {"name": "Central de Criação", "icon": "🛠️", "status": "experimental", "enterable": True,
                                "description": "Transforma ideias e projetos em planejamento, versões e protótipos conceituais."},
        },
    },
    "biblioteca": {
        "name": "Biblioteca",
        "icon": "📚",
        "status": "available",
        "enterable": True,
        "type": "knowledge",
        "description": "Conhecimento armazenado: PDFs locais, catálogo, progresso de leitura, notas e Knowledge Packs.",
        "contents": ["PDFs locais", "Leitura", "Progresso", "Knowledge Packs"],
        "concept_note": "Biblioteca = conhecimento armazenado; Pesquisa = aquisição de conhecimento novo.",
    },
    "estudio_musica": {
        "name": "Estúdio de Música",
        "icon": "🎵",
        "status": "experimental",
        "enterable": True,
        "type": "creative",
        "description": "Projetos musicais, letras, BPM, tonalidade, referências de áudio e versões.",
        "contents": ["Projetos", "Letras", "BPM / tonalidade", "Áudios locais"],
    },
    "atelie": {
        "name": "Ateliê",
        "icon": "🎨",
        "status": "experimental",
        "enterable": True,
        "type": "creative",
        "description": "Arte e criação visual, com ideias, paletas e um canvas pixel-art simples.",
        "contents": ["Pixel canvas", "Paletas", "Ideias visuais", "Galeria local"],
    },
    "jardim": {
        "name": "Jardim",
        "icon": "🌱",
        "status": "available",
        "enterable": True,
        "type": "living",
        "description": "Natureza, cultivo, fauna, flora, mar, contemplação e passagem para o Observatório.",
        "contents": ["Jardim / Plantação", "Natureza", "Mar", "Observatório", "OSHA"],
        "subareas": {
            "plantacao": {"name": "Jardim / Plantação", "icon": "🌿", "status": "available", "enterable": True,
                          "description": "Temperos, ervas, chás, frutas, legumes, verduras e cultivo educacional."},
            "natureza": {"name": "Natureza", "icon": "🌳", "status": "available", "enterable": True,
                         "description": "Fauna, flora, ecossistemas e representações educativas de locais reais."},
            "mar": {"name": "Mar", "icon": "🌊", "status": "available", "enterable": True,
                    "description": "Fauna aquática, flora marinha e exploração por zonas de profundidade."},
            "observatorio": {"name": "Observatório", "icon": "🔭", "status": "available", "enterable": True,
                             "description": "Cosmos, estrelas, planetas, galáxias e classificação de realidade.",
                             "reality_classes": ["real", "histórico", "hipotético", "simulado", "fictício", "desconhecido"]},
        },
    },
    "correio": {
        "name": "Correios",
        "icon": "📬",
        "status": "experimental",
        "enterable": True,
        "type": "system",
        "description": "Encomendas, objetos, mensagens de mundo e inventário persistente.",
        "contents": ["Encomendas", "Abrir pacote", "Inventário", "Histórico"],
        "flow": ["encomenda", "objeto", "inventário", "memória"],
    },
    "cura": {
        "name": "Cura",
        "icon": "❤️‍🩹",
        "status": "experimental",
        "enterable": True,
        "type": "system",
        "description": "Diagnóstico honesto da STAR e fluxo controlado de manutenção.",
        "contents": ["Diagnóstico", "Identificação", "Proposta", "Validação", "Teste"],
        "flow": ["diagnóstico", "identificação do problema", "proposta de correção", "validação", "aplicação autorizada", "teste"],
        "safety_note": "Cura não possui liberdade irrestrita para alterar o sistema.",
    },
    "herois": {
        "name": "Heróis",
        "icon": "🦸",
        "status": "development",
        "enterable": True,
        "type": "knowledge",
        "description": "Catálogo especializado de personagens e universos. Usa Knowledge Packs quando disponíveis.",
        "contents": ["Personagens", "Equipes", "Universos", "Knowledge Packs"],
    },
    "idiomas": {
        "name": "Idiomas",
        "icon": "🌐",
        "status": "experimental",
        "enterable": True,
        "type": "knowledge",
        "description": "Vocabulário, gramática, cartões de estudo e progresso local.",
        "contents": ["Idiomas", "Cartões", "Notas", "Progresso"],
    },
}


def get_islands():
    """Retorna uma cópia profunda para impedir mutações acidentais pela GUI."""
    return deepcopy(ISLANDS)


def get_island(key: str):
    item = ISLANDS.get(key)
    return deepcopy(item) if item else None


def get_subarea(island_key: str, subarea_key: str):
    island = ISLANDS.get(island_key, {})
    item = island.get("subareas", {}).get(subarea_key)
    return deepcopy(item) if item else None


def status_label(status: str) -> str:
    return STATUS_LABELS.get(str(status).lower(), "EM DESENVOLVIMENTO")
