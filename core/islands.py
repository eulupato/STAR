"""Catálogo oficial do STAR WORLD para a interface 2D.

As ilhas são pontos de entrada de capacidades. Ambientes internos permanecem
aninhados para evitar duplicação visual e arquitetural: Cozinha/Quarto/Closet
pertencem à Casa, Central de Criação pertence ao Laboratório e Observatório é
alcançado pelo Jardim.
"""
from __future__ import annotations

from copy import deepcopy


ISLANDS = {
    "casa": {
        "name": "Casa",
        "icon": "🏠",
        "status": "available",
        "type": "home",
        "description": "A casa da STAR dentro do STAR WORLD, com seus ambientes pessoais e de rotina.",
        "contents": [
            "Cozinha — receitas, pratos e preparo culinário",
            "Quarto — espaço pessoal da STAR",
            "Closet — roupas, skins, acessórios e aparência",
        ],
        "subareas": {
            "cozinha": {
                "name": "Cozinha",
                "icon": "🍳",
                "status": "available",
                "description": "Culinária e gastronomia, com a STAR realmente preparando receitas.",
                "contents": ["receitas", "preparo", "aprendizado culinário", "experimentação gastronômica"],
            },
            "quarto": {
                "name": "Quarto",
                "icon": "🛏️",
                "status": "available",
                "description": "Espaço pessoal da STAR dentro da Casa.",
                "contents": ["rotina", "descanso", "organização pessoal", "acesso ao Closet"],
            },
            "closet": {
                "name": "Closet",
                "icon": "👕",
                "status": "available",
                "description": "Espaço de personalização visual da STAR.",
                "contents": ["roupas", "skins", "acessórios", "aparências", "itens especiais"],
            },
        },
    },
    "laboratorio": {
        "name": "Laboratório",
        "icon": "🧪",
        "status": "development",
        "type": "workspace",
        "description": "A ilha da investigação: química, biologia, materiais, hipóteses, experimentos, testes, simulações e análise científica.",
        "contents": [
            "Laboratório principal",
            "Central de Criação (anexa)",
            "Microscópios",
            "Simulações",
        ],
        "subareas": {
            "central_criacao": {
                "name": "Central de Criação",
                "icon": "🛠️",
                "status": "development",
                "description": "Ambiente anexo para construir, desenvolver e testar projetos físicos e tecnológicos.",
                "contents": [
                    "máquinas e equipamentos", "protótipos e mecanismos", "engenharia e mecânica",
                    "montagem e fabricação", "desenvolvimento físico", "testes de protótipos",
                ],
            },
        },
    },
    "biblioteca": {
        "name": "Biblioteca",
        "icon": "📚",
        "status": "development",
        "type": "knowledge",
        "description": "Armazenamento e organização do conhecimento já adquirido: livros, documentos, referências, arquivos, coleções e histórico.",
        "contents": ["livros e documentos", "referências e fontes", "coleções", "conhecimento armazenado"],
        "concept_note": "Biblioteca = conhecimento armazenado; Pesquisa = aquisição de conhecimento novo.",
    },
    "estudio_musica": {
        "name": "Estúdio de Música",
        "icon": "🎵",
        "status": "development",
        "type": "creative",
        "description": "Espaço dedicado à composição, letras, beats, produção, experimentação, testes e criação musical.",
        "contents": ["composição", "letras", "beats", "produção"],
    },
    "jardim": {
        "name": "Jardim",
        "icon": "🌱",
        "status": "available",
        "type": "living",
        "description": "Ambiente vivo para natureza, fauna, flora, água, cultivo, contemplação e descanso. É o principal espaço da OSHA.",
        "contents": ["plantas e flores", "fauna", "água e cultivo", "OSHA"],
        "subareas": {
            "observatorio": {
                "name": "Observatório",
                "icon": "🔭",
                "status": "available",
                "description": "Astronomia, observação, contemplação e exploração de corpos celestes.",
                "contents": ["estrelas", "planetas", "corpos celestes", "classificação de realidade"],
                "reality_classes": ["real", "histórico", "hipotético", "simulado", "fictício", "desconhecido"],
            }
        },
    },
    "correio": {
        "name": "Correio",
        "icon": "📬",
        "status": "development",
        "type": "system",
        "description": "Entrada de encomendas, objetos e acontecimentos narrativos no STAR WORLD.",
        "contents": ["encomendas", "objetos", "inventário", "memória"],
        "flow": ["encomenda", "objeto", "inventário", "memória"],
    },
    "cura": {
        "name": "Cura",
        "icon": "❤️‍🩹",
        "status": "development",
        "type": "system",
        "description": "Sistema controlado de diagnóstico, manutenção e autocorreção da própria STAR.",
        "contents": ["diagnóstico", "identificação", "proposta", "validação"],
        "flow": ["diagnóstico", "identificação do problema", "proposta de correção", "validação", "aplicação", "teste"],
        "safety_note": "Não concede liberdade irrestrita para alterar o próprio código; toda alteração deve passar por validação e controle.",
    },
    "herois": {
        "name": "Heróis",
        "icon": "🦸",
        "status": "development",
        "type": "knowledge",
        "description": "Arquivo de heróis, equipes, universos, biografias, habilidades, relações e referências.",
        "contents": ["personagens", "equipes", "universos", "biografias"],
    },
    "atelie": {
        "name": "Ateliê",
        "icon": "🎨",
        "status": "development",
        "type": "creative",
        "description": "Arte e criação visual: desenho, pintura, design, conceitos, personagens e cenários.",
        "contents": ["desenho", "pixel art", "design", "criação visual"],
    },
    "idiomas": {
        "name": "Idiomas",
        "icon": "🌐",
        "status": "development",
        "type": "knowledge",
        "description": "Aprendizado de línguas, gramática, vocabulário, pronúncia, escrita e contexto cultural.",
        "contents": ["línguas modernas", "línguas históricas", "gramática", "pronúncia"],
    },
}


def get_islands():
    """Retorna cópia profunda para impedir mutações acidentais pela GUI."""
    return deepcopy(ISLANDS)


def get_subarea(island_key: str, subarea_key: str):
    """Busca um ambiente interno sem promovê-lo a ilha independente."""
    island = ISLANDS.get(island_key, {})
    subarea = island.get("subareas", {}).get(subarea_key)
    return deepcopy(subarea) if subarea else None
