"""Navegação e contexto espacial da interface STAR WORLD.

Este módulo não conhece Tkinter. Ele mantém apenas o estado de navegação,
permitindo testes rápidos e evitando espalhar regras de "voltar" pela GUI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Route:
    name: str
    label: str
    context: str = ""
    parent: str | None = None


ROUTES: dict[str, Route] = {
    "menu": Route("menu", "Menu", ""),
    "hub": Route("hub", "STAR HUB", "STAR World"),
    "house": Route("house", "Casa", "Casa", "hub"),
    "living_room": Route("living_room", "Sala", "Casa > Sala", "house"),
    "kitchen": Route("kitchen", "Cozinha", "Casa > Cozinha", "house"),
    "bedroom": Route("bedroom", "Quarto", "Casa > Quarto", "house"),
    "closet": Route("closet", "Closet", "Casa > Quarto > Closet", "bedroom"),
    "gallery": Route("gallery", "Álbum", "Casa > Quarto > Closet > Álbum", "closet"),
    "heroes": Route("heroes", "Ilha dos Heróis", "Heróis", "hub"),
    "settings": Route("settings", "Configurações", "Configurações"),
    "chat": Route("chat", "Conversa", "Conversa geral"),
}


@dataclass
class NavigationManager:
    current: str = "menu"
    history: list[str] = field(default_factory=list)
    overlay_returns: list[str] = field(default_factory=list)

    @property
    def return_route(self) -> str | None:
        return self.overlay_returns[-1] if self.overlay_returns else None

    def go(self, route: str, *, remember: bool = True) -> str:
        if route not in ROUTES:
            raise KeyError(f"Rota desconhecida: {route}")
        if remember and self.current != route:
            self.history.append(self.current)
        if route not in {"settings", "chat"}:
            self.overlay_returns.clear()
        self.current = route
        return route

    def open_overlay(self, route: str) -> str:
        if route not in {"settings", "chat"}:
            raise ValueError(f"Rota não é overlay: {route}")
        if self.current != route:
            self.overlay_returns.append(self.current)
        self.current = route
        return route

    def close_overlay(self, fallback: str = "hub") -> str:
        target = self.overlay_returns.pop() if self.overlay_returns else fallback
        self.current = target
        return target

    def back(self) -> str:
        route = ROUTES[self.current]
        if route.parent:
            self.current = route.parent
            return self.current
        if self.history:
            self.current = self.history.pop()
            return self.current
        self.current = "menu"
        return self.current

    @property
    def context(self) -> str:
        return ROUTES[self.current].context

    @property
    def label(self) -> str:
        return ROUTES[self.current].label
