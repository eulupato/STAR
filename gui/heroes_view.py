"""Interface da Ilha dos Heróis sem lógica de banco."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk

from core.logging_config import get_logger
from gui.components.carousel import CarouselController

log = get_logger("gui.heroes")


class HeroesIslandView(tk.Frame):
    def __init__(self, parent, *, knowledge, palette, on_selected=None):
        super().__init__(parent, bg=palette["bg"])
        self.knowledge = knowledge
        self.palette = palette
        self.on_selected = on_selected
        self.carousel = CarouselController()
        self.photo = None
        self._search_job = None

        self.search_var = tk.StringVar()
        self.universe_var = tk.StringVar(value="Todos")
        self._build()
        self.refresh()

    def _build(self):
        controls = tk.Frame(self, bg=self.palette["bg"])
        controls.pack(fill="x", padx=24, pady=(8, 12))

        self.search = tk.Entry(
            controls,
            textvariable=self.search_var,
            bg="#25364b",
            fg=self.palette["text"],
            insertbackground=self.palette["text"],
            relief=tk.FLAT,
            font=("Segoe UI", 11),
        )
        self.search.pack(side="left", fill="x", expand=True, ipady=8)
        self.search.bind("<KeyRelease>", self._schedule_refresh)

        options = ["Todos", "Marvel", "DC"]
        menu = tk.OptionMenu(
            controls,
            self.universe_var,
            *options,
            command=lambda _value: self.refresh(),
        )
        menu.config(
            bg="#243247",
            fg=self.palette["text"],
            activebackground="#315575",
            activeforeground=self.palette["text"],
            relief=tk.FLAT,
            highlightthickness=0,
        )
        menu["menu"].config(bg="#243247", fg=self.palette["text"])
        menu.pack(side="left", padx=(10, 0))

        content = tk.Frame(self, bg=self.palette["bg"])
        content.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        self.prev_button = tk.Button(
            content,
            text="◀",
            command=lambda: self.move(-1),
            bg="#243247",
            fg=self.palette["text"],
            activebackground="#315575",
            activeforeground=self.palette["text"],
            relief=tk.FLAT,
            font=("Segoe UI", 16, "bold"),
            width=3,
        )
        self.prev_button.pack(side="left", fill="y", padx=(0, 10))

        card = tk.Frame(content, bg=self.palette["panel"], padx=20, pady=18)
        card.pack(side="left", fill="both", expand=True)

        left = tk.Frame(card, bg=self.palette["panel"], width=330)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        self.image_label = tk.Label(
            left,
            bg="#080c12",
            fg=self.palette["muted"],
            text="SEM IMAGEM\nDE REFERÊNCIA",
            font=("Segoe UI", 11, "bold"),
            compound="center",
        )
        self.image_label.pack(fill="both", expand=True, padx=(0, 18))

        right = tk.Frame(card, bg=self.palette["panel"])
        right.pack(side="left", fill="both", expand=True)

        self.name_label = tk.Label(
            right,
            bg=self.palette["panel"],
            fg=self.palette["star"],
            font=("Segoe UI", 23, "bold"),
            anchor="w",
        )
        self.name_label.pack(fill="x")

        self.meta_label = tk.Label(
            right,
            bg=self.palette["panel"],
            fg=self.palette["muted"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.meta_label.pack(fill="x", pady=(3, 12))

        self.details = tk.Text(
            right,
            bg=self.palette["panel"],
            fg=self.palette["text"],
            insertbackground=self.palette["text"],
            relief=tk.FLAT,
            wrap="word",
            font=("Segoe UI", 10),
            state=tk.DISABLED,
        )
        self.details.pack(fill="both", expand=True)

        self.counter_label = tk.Label(
            right,
            bg=self.palette["panel"],
            fg=self.palette["muted"],
            font=("Segoe UI", 9),
        )
        self.counter_label.pack(anchor="e", pady=(8, 0))

        self.next_button = tk.Button(
            content,
            text="▶",
            command=lambda: self.move(1),
            bg="#243247",
            fg=self.palette["text"],
            activebackground="#315575",
            activeforeground=self.palette["text"],
            relief=tk.FLAT,
            font=("Segoe UI", 16, "bold"),
            width=3,
        )
        self.next_button.pack(side="left", fill="y", padx=(10, 0))

    def _schedule_refresh(self, _event=None):
        if self._search_job is not None:
            try:
                self.after_cancel(self._search_job)
            except tk.TclError as exc:
                log.debug("Busca anterior já não estava agendada: %s", exc)
        self._search_job = self.after(140, self.refresh)

    def refresh(self):
        self._search_job = None
        query = self.search_var.get().strip()
        universe = self.universe_var.get()
        filters = {"category": "character"}
        if universe != "Todos":
            filters["universe"] = universe
        previous = self.carousel.current
        previous_id = previous.id if previous else None
        items = self.knowledge.search_entities(query, filters=filters, limit=500)
        self.carousel.set_items(items, keep_id=previous_id)
        self.render()

    def move(self, step):
        self.carousel.move(step)
        self.render()

    def render(self):
        entity = self.carousel.current
        if entity is None:
            self.name_label.config(text="Nenhum personagem encontrado")
            self.meta_label.config(
                text="Importe os PDFs locais ou altere os filtros de busca."
            )
            self._set_details(
                "A Ilha dos Heróis está funcional, mas não há registros que "
                "correspondam à pesquisa atual."
            )
            self.image_label.config(image="", text="SEM IMAGEM\nDE REFERÊNCIA")
            self.counter_label.config(text="0 / 0")
            return

        self.name_label.config(text=entity.name)
        meta = " • ".join(
            item for item in [entity.universe, entity.publisher, entity.species]
            if item
        )
        self.meta_label.config(text=meta or entity.category)

        lines = []
        if entity.original_name and entity.original_name != entity.name:
            lines.append(f"Nome original: {entity.original_name}")
        if entity.aliases:
            lines.append("Aliases: " + ", ".join(entity.aliases))
        if entity.occupation:
            lines.append("Ocupação: " + ", ".join(entity.occupation))
        if entity.team:
            lines.append("Equipe: " + ", ".join(entity.team))
        if entity.affiliations:
            lines.append("Afiliações: " + ", ".join(entity.affiliations))
        if entity.first_appearance:
            lines.append("Primeira aparição: " + entity.first_appearance)
        if entity.description:
            lines.append("\n" + entity.description)
        if entity.powers:
            lines.append("\nPoderes/Habilidades: " + ", ".join(entity.powers))
        if entity.weaknesses:
            lines.append("Fraquezas: " + ", ".join(entity.weaknesses))
        if entity.relationships:
            grouped = {}
            for relation in entity.relationships:
                grouped.setdefault(relation.predicate, []).append(relation.target_name)
            for predicate, names in grouped.items():
                lines.append(f"{predicate.title()}: " + ", ".join(names))
        if entity.sources:
            source = entity.sources[0]
            page = f", pág. {source.page}" if source.page else ""
            lines.append(f"\nFonte: {source.source_ref}{page}")

        self._set_details("\n".join(lines) or "Registro básico; aguardando enriquecimento.")
        self._render_image(entity.image)
        self.counter_label.config(
            text=f"{self.carousel.index + 1} / {len(self.carousel.items)}"
        )
        if self.on_selected:
            self.on_selected(entity)

    def _set_details(self, text):
        self.details.config(state=tk.NORMAL)
        self.details.delete("1.0", tk.END)
        self.details.insert("1.0", str(text))
        self.details.config(state=tk.DISABLED)

    def _render_image(self, path_value):
        self.photo = None
        path = Path(path_value) if path_value else None
        if path and path.exists() and path.is_file():
            try:
                image = Image.open(path).convert("RGB")
                image.thumbnail((310, 430), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(image)
                self.image_label.config(
                    image=self.photo,
                    text="",
                )
                return
            except (OSError, ValueError, tk.TclError) as exc:
                log.debug("Imagem de personagem indisponível (%s): %s", path, exc)
        self.image_label.config(
            image="",
            text="SEM IMAGEM\nDE REFERÊNCIA",
        )
