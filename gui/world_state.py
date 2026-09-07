"""Persistência local leve dos ambientes 2D do STAR WORLD.

O arquivo fica em ``runtime/star_world_state.json`` (runtime já é ignorado pelo
Git). O objetivo é persistir somente estado da experiência 2D sem duplicar a
memória cognitiva oficial da STAR.
"""
from __future__ import annotations

import json
import threading
from copy import deepcopy
from pathlib import Path

DEFAULT_STATE = {
    "tv_favorites": [],
    "recipes": [
        {"id": "omelete", "name": "Omelete de ervas", "category": "Café da manhã", "time": "15 min", "difficulty": "Fácil",
         "ingredients": ["2 ovos", "ervas frescas", "sal", "1 fio de azeite"],
         "steps": ["Separe os ingredientes.", "Bata os ovos.", "Misture as ervas.", "Aqueça a frigideira.", "Cozinhe até firmar e sirva."]},
        {"id": "macarrao", "name": "Macarrão ao molho de tomate", "category": "Almoço / jantar", "time": "30 min", "difficulty": "Fácil",
         "ingredients": ["massa", "tomate ou molho de tomate", "alho", "azeite", "sal", "ervas"],
         "steps": ["Ferva água suficiente para a massa.", "Prepare o molho em outra panela.", "Cozinhe a massa conforme a embalagem.", "Escorra e misture ao molho.", "Finalize com ervas e sirva."]},
        {"id": "salada", "name": "Salada crocante", "category": "Saladas", "time": "12 min", "difficulty": "Fácil",
         "ingredients": ["folhas", "tomate", "cenoura", "pepino", "azeite", "limão"],
         "steps": ["Higienize os vegetais.", "Corte os ingredientes.", "Misture em uma tigela.", "Tempere apenas na hora de servir."]},
        {"id": "chocolate", "name": "Chocolate quente simples", "category": "Bebidas", "time": "10 min", "difficulty": "Fácil",
         "ingredients": ["leite", "cacau em pó", "açúcar a gosto"],
         "steps": ["Misture o cacau com parte do leite ainda frio.", "Junte o restante do leite.", "Aqueça mexendo até ficar uniforme.", "Adoce a gosto e sirva."]},
    ],
    "recipe_favorites": [],
    "cultivation": {},
    "plants": [
        {"id": "manjericao", "name": "Manjericão", "scientific": "Ocimum basilicum", "category": "Tempero / erva", "sun": "Sol a meia-sombra", "water": "Regular", "soil": "Fértil e drenado", "harvest": "Folhas conforme crescimento", "uses": "Molhos, massas, saladas e chás aromáticos."},
        {"id": "hortela", "name": "Hortelã", "scientific": "Mentha spp.", "category": "Erva / chá", "sun": "Meia-sombra a sol suave", "water": "Solo levemente úmido", "soil": "Rico e drenado", "harvest": "Folhas", "uses": "Chás, bebidas, molhos e sobremesas."},
        {"id": "tomate", "name": "Tomate", "scientific": "Solanum lycopersicum", "category": "Fruto hortícola", "sun": "Sol pleno", "water": "Regular, sem encharcar", "soil": "Fértil", "harvest": "Frutos maduros", "uses": "Molhos, saladas e preparos diversos."},
        {"id": "alface", "name": "Alface", "scientific": "Lactuca sativa", "category": "Folhosa", "sun": "Sol suave / meia-sombra", "water": "Frequente", "soil": "Leve e fértil", "harvest": "Folhas ou planta inteira", "uses": "Saladas e sanduíches."},
        {"id": "morango", "name": "Morango", "scientific": "Fragaria × ananassa", "category": "Fruta", "sun": "Sol pleno", "water": "Regular", "soil": "Rico e drenado", "harvest": "Frutos vermelhos", "uses": "In natura, doces e bebidas."},
        {"id": "camomila", "name": "Camomila", "scientific": "Matricaria chamomilla", "category": "Flor / chá", "sun": "Sol", "water": "Moderada", "soil": "Bem drenado", "harvest": "Flores", "uses": "Infusões aromáticas."},
    ],
    "nature_species": [
        {"name": "Ipê-amarelo", "kind": "Flora", "scientific": "Handroanthus spp.", "habitat": "Diversos ambientes brasileiros", "role": "Árvore nativa, recurso para fauna e paisagismo."},
        {"name": "Capivara", "kind": "Fauna", "scientific": "Hydrochoerus hydrochaeris", "habitat": "Áreas próximas à água na América do Sul", "role": "Herbívoro de ecossistemas aquáticos e terrestres."},
        {"name": "Onça-pintada", "kind": "Fauna", "scientific": "Panthera onca", "habitat": "Florestas e áreas úmidas das Américas", "role": "Predador de topo em vários ecossistemas."},
        {"name": "Vitória-régia", "kind": "Flora", "scientific": "Victoria amazonica", "habitat": "Águas calmas da Amazônia", "role": "Planta aquática de grande porte."},
    ],
    "world_places": [
        {"name": "Paris — Torre Eiffel", "type": "LOCAL REAL · REPRESENTAÇÃO", "note": "Representação educativa; não é transmissão ao vivo."},
        {"name": "Marrocos", "type": "LOCAL REAL · REPRESENTAÇÃO", "note": "Exploração cultural e geográfica representada visualmente."},
        {"name": "Havaí", "type": "LOCAL REAL · REPRESENTAÇÃO", "note": "Ilhas vulcânicas, praias e ecossistemas do Pacífico."},
        {"name": "Floresta Amazônica", "type": "LOCAL REAL · REPRESENTAÇÃO", "note": "Bioma tropical de enorme biodiversidade."},
    ],
    "marine_species": [
        {"name": "Tartaruga-verde", "zone": "Costa / oceano", "kind": "Réptil marinho", "note": "Ocorre em mares tropicais e subtropicais."},
        {"name": "Baleia-jubarte", "zone": "Oceano aberto", "kind": "Mamífero", "note": "Realiza grandes migrações sazonais."},
        {"name": "Peixe-palhaço", "zone": "Recifes", "kind": "Peixe", "note": "Associado a anêmonas em recifes tropicais."},
        {"name": "Peixe-lanterna", "zone": "Zona crepuscular", "kind": "Peixe", "note": "Muitos possuem órgãos bioluminescentes."},
        {"name": "Lula-gigante", "zone": "Mar profundo", "kind": "Cefalópode", "note": "Habita águas profundas e é raramente observada viva."},
    ],
    "astronomy": [
        {"name": "Sol", "class": "REAL", "category": "Estrela", "note": "Estrela central do Sistema Solar."},
        {"name": "Saturno", "class": "REAL", "category": "Planeta", "note": "Gigante gasoso conhecido por seu sistema de anéis."},
        {"name": "Nebulosa de Órion", "class": "REAL", "category": "Nebulosa", "note": "Região de formação estelar na constelação de Órion."},
        {"name": "Via Láctea", "class": "REAL", "category": "Galáxia", "note": "Galáxia que contém o Sistema Solar."},
        {"name": "Krypton", "class": "FICTÍCIO", "category": "Planeta fictício", "note": "Objeto de ficção; não é apresentado como descoberta astronômica."},
        {"name": "Modelo de planeta hipotético", "class": "HIPOTÉTICO", "category": "Modelo", "note": "Exemplo educacional explicitamente marcado como hipótese."},
    ],
    "shared_projects": [],
    "library": [],
    "music_projects": [],
    "art_projects": [],
    "pixel_art": {"size": 16, "points": {}},
    "mail": [
        {"id": "welcome", "title": "Bem-vindo ao STAR WORLD", "status": "unread", "item": "Cartão de boas-vindas", "description": "Uma pequena lembrança da abertura do STAR WORLD."},
        {"id": "shell", "title": "Encomenda com símbolo de concha", "status": "unread", "item": "Pista da OSHA", "description": "A caixa parece leve demais. Talvez a encomenda já tenha escapado para o Jardim."},
    ],
    "inventory": [],
    "languages": [
        {"name": "Inglês", "status": "EXPERIMENTAL", "cards": [["hello", "olá"], ["book", "livro"], ["garden", "jardim"], ["star", "estrela"]]},
        {"name": "Espanhol", "status": "EXPERIMENTAL", "cards": [["hola", "olá"], ["libro", "livro"], ["jardín", "jardim"], ["estrella", "estrela"]]},
        {"name": "Francês", "status": "EXPERIMENTAL", "cards": [["bonjour", "olá"], ["livre", "livro"], ["jardin", "jardim"], ["étoile", "estrela"]]},
        {"name": "Latim", "status": "PLANEJADO", "cards": [["stella", "estrela"], ["liber", "livro"]]},
    ],
}


def _merge_defaults(current, defaults):
    if isinstance(defaults, dict):
        target = current if isinstance(current, dict) else {}
        for key, value in defaults.items():
            target[key] = _merge_defaults(target.get(key), value)
        return target
    if current is None:
        return deepcopy(defaults)
    return current


class WorldState:
    """Estado persistente da camada visual/funcional do STAR WORLD."""

    def __init__(self, project_root: Path):
        self.path = Path(project_root) / "runtime" / "star_world_state.json"
        self._lock = threading.RLock()
        self.data = self._load()

    def _load(self):
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            raw = {}
        return _merge_defaults(raw, deepcopy(DEFAULT_STATE))

    def save(self):
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.path)

    def get(self, key, default=None):
        with self._lock:
            return deepcopy(self.data.get(key, default))

    def set(self, key, value):
        with self._lock:
            self.data[key] = deepcopy(value)
            self.save()

    def append(self, key, value):
        with self._lock:
            self.data.setdefault(key, []).append(deepcopy(value))
            self.save()

    def replace_list_item(self, key, index, value):
        with self._lock:
            self.data.setdefault(key, [])[index] = deepcopy(value)
            self.save()

    def toggle_in_list(self, key, value):
        with self._lock:
            values = self.data.setdefault(key, [])
            if value in values:
                values.remove(value)
                active = False
            else:
                values.append(value)
                active = True
            self.save()
            return active

    def upsert_by_id(self, key, item):
        with self._lock:
            items = self.data.setdefault(key, [])
            identifier = item.get("id")
            for i, existing in enumerate(items):
                if existing.get("id") == identifier:
                    items[i] = deepcopy(item)
                    self.save()
                    return
            items.append(deepcopy(item))
            self.save()
