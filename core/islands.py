"""Catálogo modular do STAR WORLD.

As ilhas representam ambientes/capacidades da STAR. Uma ilha pode existir
visualmente no HUB mesmo quando o respectivo pacote de conhecimento ainda
não foi instalado. O campo ``status`` indica o estado do pacote.
"""

ISLANDS = {
    "herois": {
        "name": "Heróis",
        "icon": "🦸",
        "status": "planned",
        "type": "knowledge",
        "description": "Catálogo aprofundado de heróis e personagens, com biografias e referências organizadas.",
        "contents": [
            "biografia, origem e história",
            "evolução do personagem e principais arcos",
            "HQs, edições e cronologias",
            "filmes, séries e outras aparições",
            "família, parentes e relações",
            "poderes, habilidades e equipamentos",
            "versões, universos e identidades",
            "curiosidades e referências",
        ],
    },
    "idiomas": {
        "name": "Idiomas",
        "icon": "🌐",
        "status": "planned",
        "type": "knowledge",
        "description": "Aprendizado de línguas modernas, antigas e históricas, da escrita ao uso prático.",
        "contents": [
            "inglês, espanhol, francês e outras línguas modernas",
            "latim e grego antigo",
            "egípcio antigo e línguas históricas",
            "línguas mesoamericanas e ameríndias",
            "famílias linguísticas e evolução",
            "gramática e vocabulário",
            "pronúncia, escrita e leitura",
            "história, contexto e cultura linguística",
        ],
    },
    "laboratorio": {
        "name": "Laboratório",
        "icon": "🧪",
        "status": "planned",
        "type": "workspace",
        "description": "Ambiente de investigação, ciência, experimentação e análise.",
        "contents": [
            "química e biologia",
            "materiais e propriedades",
            "cálculos e análise científica",
            "hipóteses e testes",
            "experimentos e protocolos",
            "simulações e modelagem",
            "análise de resultados",
        ],
    },
    "central_criacao": {
        "name": "Central de Criação",
        "icon": "🛠️",
        "status": "planned",
        "type": "workspace",
        "description": "Ambiente para construir, desenvolver e testar projetos físicos e tecnológicos.",
        "contents": [
            "máquinas e equipamentos",
            "protótipos e mecanismos",
            "engenharia e mecânica",
            "montagem e fabricação",
            "desenvolvimento físico",
            "testes de protótipos",
        ],
    },
    "biblioteca": {
        "name": "Biblioteca",
        "icon": "📚",
        "status": "planned",
        "type": "knowledge",
        "description": "Grande arquivo de conhecimento armazenado, organizado em livros, documentos e coleções.",
        "contents": [
            "livros e documentos",
            "referências e fontes",
            "coleções de conhecimento",
            "materiais adquiridos",
            "histórico e versões",
            "organização por assunto",
        ],
    },
    "estudio_musica": {
        "name": "Estúdio de Música",
        "icon": "🎵",
        "status": "planned",
        "type": "creative",
        "description": "Espaço dedicado à composição, produção, experimentação e criação musical.",
        "contents": [
            "composição",
            "letras e ideias musicais",
            "beats e produção",
            "experimentação sonora",
            "testes e arranjos",
            "projetos musicais",
        ],
    },
    "observatorio": {
        "name": "Observatório",
        "icon": "🔭",
        "status": "planned",
        "type": "knowledge",
        "description": "Ambiente de astronomia, observação do céu e exploração de corpos celestes.",
        "contents": [
            "estrelas e planetas",
            "corpos celestes",
            "astronomia e astrofísica",
            "exploração astronômica",
            "passagem do tempo e céu noturno",
            "objetos fictícios claramente identificados como ficção",
        ],
    },
    "jardim": {
        "name": "Jardim",
        "icon": "🌱",
        "status": "planned",
        "type": "living",
        "description": "Ambiente vivo para natureza, fauna, flora, água, cultivo, contemplação e descanso.",
        "contents": [
            "plantas, árvores e flores",
            "fauna e animais",
            "água e ecossistemas",
            "cultivo e botânica",
            "natureza e observação",
            "lazer, contemplação e descanso",
            "espaço associado à OSHA, o pet da STAR",
        ],
    },
    "casa": {
        "name": "Casa",
        "icon": "🏠",
        "status": "planned",
        "type": "home",
        "description": "A casa da STAR dentro do STAR WORLD, com ambientes pessoais e de rotina.",
        "contents": [
            "🍳 Cozinha — receitas, pratos e preparo culinário",
            "🛏️ Quarto — espaço pessoal da STAR",
            "👕 Closet — roupas, skins, acessórios e aparência",
        ],
        "subareas": {
            "cozinha": {
                "name": "Cozinha",
                "icon": "🍳",
                "description": "Culinária e gastronomia, com a STAR realmente preparando receitas.",
                "contents": ["receitas", "preparo", "aprendizado culinário", "experimentação gastronômica"],
            },
            "quarto": {
                "name": "Quarto",
                "icon": "🛏️",
                "description": "Espaço pessoal da STAR dentro da Casa.",
                "contents": ["rotina", "descanso", "organização pessoal", "acesso ao Closet"],
            },
            "closet": {
                "name": "Closet",
                "icon": "👕",
                "description": "Espaço de personalização visual da STAR.",
                "contents": ["roupas", "skins", "acessórios", "aparências", "itens especiais"],
            },
        },
    },
    "correio": {
        "name": "Correio",
        "icon": "📬",
        "status": "planned",
        "type": "system",
        "description": "Entrada de encomendas, objetos e acontecimentos narrativos no STAR WORLD.",
        "contents": [
            "recebimento de encomendas",
            "objetos e itens",
            "inventário",
            "registro em memória",
            "eventos e histórias",
            "integração futura com narrativas como a origem da OSHA",
        ],
    },
    "cura": {
        "name": "Cura",
        "icon": "❤️‍🩹",
        "status": "planned",
        "type": "system",
        "description": "Sistema controlado de diagnóstico, manutenção e autocorreção da própria STAR.",
        "contents": [
            "diagnóstico",
            "identificação do problema",
            "proposta de correção",
            "validação",
            "aplicação controlada",
            "teste após correção",
        ],
        "safety_note": "Não concede liberdade irrestrita para alterar o próprio código; toda alteração deve passar por validação e controle.",
    },
}


def get_islands():
    """Retorna uma cópia segura do catálogo para a interface."""
    return {key: dict(value) for key, value in ISLANDS.items()}
