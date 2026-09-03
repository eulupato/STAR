"""Controlador genérico de seleção anterior/próximo."""
from __future__ import annotations


class CarouselController:
    def __init__(self, items=None):
        self.items = list(items or [])
        self.index = 0

    def set_items(self, items, *, keep_id=None):
        items = list(items or [])
        self.items = items
        self.index = 0
        if keep_id is not None:
            for index, item in enumerate(items):
                if getattr(item, "id", None) == keep_id:
                    self.index = index
                    break
        return self.current

    @property
    def current(self):
        if not self.items:
            return None
        self.index %= len(self.items)
        return self.items[self.index]

    def move(self, step: int):
        if not self.items:
            return None
        self.index = (self.index + int(step)) % len(self.items)
        return self.current

    def select(self, index: int):
        if not self.items:
            return None
        self.index = max(0, min(int(index), len(self.items) - 1))
        return self.current
