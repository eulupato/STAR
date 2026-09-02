"""Interface da Ilha dos Heróis sem lógica de banco."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk

from core.logging_config import get_logger
from gui.components.carousel import CarouselController
from knowledge.hero_visuals import theme_for_entity, visual_references

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
        self._image_index = 0
        self._image_refs: list[str] = []
        self._rendered_entity_id = None

        self.search_var = tk.StringVar()
        self.universe_var = tk.StringVar(value="Todos")
        self.filter_vars = {
            "team": tk.StringVar(),
            "power": tk.StringVar(),
            "ability": tk.StringVar(),
            "tag": tk.StringVar(),
            "species": tk.StringVar(),
            "relationship": tk.StringVar(),
        }
        self._build()
        self.refresh()

    def _build(self):
        controls = tk.Frame(self, bg=self.palette["bg"])
        controls.pack(fill="x", padx=24, pady=(8, 12))

        tk.Label(
            controls,
            text="Nome / alias / busca",
            bg=self.palette["bg"],
            fg=self.palette["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(0, 8))

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

        advanced = tk.Frame(self, bg=self.palette["bg"])
        advanced.pack(fill="x", padx=24, pady=(0, 10))
        fields = (
            ("Equipe", "team"),
            ("Poder", "power"),
            ("Habilidade", "ability"),
            ("Tag", "tag"),
            ("Tipo / espécie", "species"),
            ("Relação com", "relationship"),
        )
        for index, (label, key) in enumerate(fields):
            holder = tk.Frame(advanced, bg=self.palette["bg"])
            holder.grid(
                row=index // 3,
                column=index % 3,
                sticky="ew",
                padx=(0 if index % 3 == 0 else 8, 0),
                pady=(0, 7),
            )
            tk.Label(
                holder,
                text=label,
                bg=self.palette["bg"],
                fg=self.palette["muted"],
                font=("Segoe UI", 8, "bold"),
            ).pack(anchor="w")
            entry = tk.Entry(
                holder,
                textvariable=self.filter_vars[key],
                bg="#25364b",
                fg=self.palette["text"],
                insertbackground=self.palette["text"],
                relief=tk.FLAT,
                font=("Segoe UI", 9),
            )
            entry.pack(fill="x", ipady=5)
            entry.bind("<KeyRelease>", self._schedule_refresh)

        for column in range(3):
            advanced.grid_columnconfigure(column, weight=1)

        tk.Button(
            advanced,
            text="LIMPAR FILTROS",
            command=self._clear_filters,
            bg="#243247",
            fg=self.palette["text"],
            activebackground="#315575",
            activeforeground=self.palette["text"],
            relief=tk.FLAT,
            font=("Segoe UI", 8, "bold"),
            padx=12,
            pady=5,
        ).grid(row=2, column=2, sticky="e", pady=(2, 0))

        self.content = tk.Frame(self, bg=self.palette["bg"])
        self.content.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        self.prev_button = tk.Button(
            self.content,
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

        self.card = tk.Frame(
            self.content,
            bg=self.palette["panel"],
            padx=20,
            pady=18,
        )
        self.card.pack(side="left", fill="both", expand=True)

        self.left = tk.Frame(self.card, bg=self.palette["panel"], width=330)
        self.left.pack(side="left", fill="y")
        self.left.pack_propagate(False)

        self.image_label = tk.Label(
            self.left,
            bg="#080c12",
            fg=self.palette["muted"],
            text="SEM IMAGEM\nDE REFERÊNCIA",
            font=("Segoe UI", 11, "bold"),
            compound="center",
        )
        self.image_label.pack(fill="both", expand=True, padx=(0, 18))

        self.image_controls = tk.Frame(self.left, bg=self.palette["panel"])
        self.image_controls.pack(fill="x", padx=(0, 18), pady=(8, 0))
        self.image_prev = tk.Button(
            self.image_controls,
            text="◀ imagem",
            command=lambda: self.move_image(-1),
            relief=tk.FLAT,
            font=("Segoe UI", 8, "bold"),
        )
        self.image_prev.pack(side="left")
        self.image_counter = tk.Label(
            self.image_controls,
            text="0 / 0",
            font=("Segoe UI", 8, "bold"),
        )
        self.image_counter.pack(side="left", expand=True)
        self.image_next = tk.Button(
            self.image_controls,
            text="imagem ▶",
            command=lambda: self.move_image(1),
            relief=tk.FLAT,
            font=("Segoe UI", 8, "bold"),
        )
        self.image_next.pack(side="right")

        self.right = tk.Frame(self.card, bg=self.palette["panel"])
        self.right.pack(side="left", fill="both", expand=True)

        self.name_label = tk.Label(
            self.right,
            bg=self.palette["panel"],
            fg=self.palette["star"],
            font=("Segoe UI", 23, "bold"),
            anchor="w",
        )
        self.name_label.pack(fill="x")

        self.meta_label = tk.Label(
            self.right,
            bg=self.palette["panel"],
            fg=self.palette["muted"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.meta_label.pack(fill="x", pady=(3, 12))

        self.details = tk.Text(
            self.right,
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
            self.right,
            bg=self.palette["panel"],
            fg=self.palette["muted"],
            font=("Segoe UI", 9),
        )
        self.counter_label.pack(anchor="e", pady=(8, 0))

        self.next_button = tk.Button(
            self.content,
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

    def _clear_filters(self):
        self.search_var.set("")
        self.universe_var.set("Todos")
        for variable in self.filter_vars.values():
            variable.set("")
        self.refresh()

    def refresh(self):
        self._search_job = None
        query = self.search_var.get().strip()
        universe = self.universe_var.get()
        filters = {"category": "character"}
        if universe != "Todos":
            filters["universe"] = universe
        for key, variable in self.filter_vars.items():
            value = variable.get().strip()
            if value:
                filters[key] = value

        previous = self.carousel.current
        previous_id = previous.id if previous else None
        items = self.knowledge.search_entities(query, filters=filters, limit=5000)
        self.carousel.set_items(items, keep_id=previous_id)
        self.render()

    def move(self, step):
        self.carousel.move(step)
        self.render()

    def move_image(self, step):
        if not self._image_refs:
            return
        self._image_index = (self._image_index + step) % len(self._image_refs)
        self._render_image_reference()

    def _apply_theme(self, entity):
        theme = theme_for_entity(entity)
        self.card.config(bg=theme.panel)
        self.left.config(bg=theme.panel)
        self.right.config(bg=theme.panel)
        self.image_controls.config(bg=theme.panel)

        self.name_label.config(bg=theme.panel, fg=theme.accent)
        self.meta_label.config(bg=theme.panel, fg=theme.muted)
        self.details.config(
            bg=theme.panel,
            fg=theme.text,
            insertbackground=theme.text,
        )
        self.counter_label.config(bg=theme.panel, fg=theme.muted)
        self.image_label.config(
            bg=theme.background,
            fg=theme.muted,
            highlightbackground=theme.accent,
            highlightcolor=theme.accent,
            highlightthickness=1,
        )
        for button in (
            self.prev_button,
            self.next_button,
            self.image_prev,
            self.image_next,
        ):
            button.config(
                bg=theme.background,
                fg=theme.accent_secondary,
                activebackground=theme.accent,
                activeforeground=theme.text,
            )
        self.image_counter.config(bg=theme.panel, fg=theme.muted)

    def render(self):
        entity = self.carousel.current
        if entity is None:
            self.name_label.config(text="Nenhum personagem encontrado")
            self.meta_label.config(
                text="Importe a base local ou altere os filtros de busca."
            )
            self._set_details(
                "A Ilha dos Heróis está funcional, mas não há registros que "
                "correspondam à pesquisa atual."
            )
            self.photo = None
            self._image_refs = []
            self.image_label.config(image="", text="SEM IMAGEM\nDE REFERÊNCIA")
            self.image_counter.config(text="0 / 0")
            self.counter_label.config(text="0 / 0")
            return

        self._apply_theme(entity)
        self.name_label.config(text=entity.name)
        meta = " • ".join(
            item
            for item in [entity.universe, entity.publisher, entity.species]
            if item
        )
        self.meta_label.config(text=meta or entity.category)

        lines = []
        real_name = entity.attributes.get("real_name") if entity.attributes else None
        if real_name:
            lines.append(f"Identidade / nome real: {real_name}")
        if entity.original_name and entity.original_name != entity.name:
            lines.append(f"Nome original: {entity.original_name}")
        if entity.aliases:
            lines.append("Aliases: " + ", ".join(entity.aliases))
        if entity.gender:
            lines.append(f"Gênero: {entity.gender}")
        if entity.species:
            lines.append(f"Espécie / tipo: {entity.species}")
        if entity.origin_place:
            lines.append(f"Local de origem: {entity.origin_place}")
        if entity.origin:
            lines.append(f"Origem: {entity.origin}")
        if entity.occupation:
            lines.append("Ocupação: " + ", ".join(entity.occupation))
        if entity.creators:
            lines.append("Criadores: " + ", ".join(entity.creators))
        if entity.team:
            lines.append("Equipes: " + ", ".join(entity.team))
        if entity.affiliations:
            lines.append("Afiliações: " + ", ".join(entity.affiliations))
        if entity.status:
            lines.append(f"Status / classificação: {entity.status}")
        if entity.tags:
            lines.append("Tags: " + ", ".join(entity.tags))
        if entity.first_appearance:
            lines.append("Primeira aparição: " + entity.first_appearance)
        if entity.description:
            description_kind = (
                entity.metadata or {}
            ).get("description_kind")
            if description_kind == "catalog_fallback":
                lines.append(
                    "\nDescrição básica do catálogo "
                    "(biografia verificada pendente):"
                )
            elif description_kind == "wikidata_short_description":
                lines.append("\nDescrição curta verificada (Wikidata):")
            else:
                lines.append("\nDescrição:")
            lines.append(entity.description)
        if entity.history_summary:
            lines.append("\nHistória resumida: " + entity.history_summary)
        if entity.personality:
            lines.append("Personalidade: " + entity.personality)
        if entity.powers:
            lines.append("\nPoderes: " + ", ".join(entity.powers))
        if entity.abilities:
            lines.append("Habilidades: " + ", ".join(entity.abilities))
        if entity.weaknesses:
            lines.append("Fraquezas: " + ", ".join(entity.weaknesses))
        if entity.equipment:
            lines.append("Equipamentos: " + ", ".join(entity.equipment))

        if entity.relationships:
            grouped = {}
            for relation in entity.relationships:
                grouped.setdefault(relation.predicate, []).append(relation.target_name)
            for predicate, names in grouped.items():
                lines.append(f"{predicate.title()}: " + ", ".join(names))

        if entity.sources:
            lines.append("\nFontes:")
            for source in entity.sources[:8]:
                page = f", pág. {source.page}" if source.page else ""
                url = f" — {source.url}" if source.url else ""
                lines.append(f"• {source.source_ref}{page}{url}")
            if len(entity.sources) > 8:
                lines.append(f"• +{len(entity.sources) - 8} fontes registradas")

        attributions = (
            (entity.metadata or {}).get("image_attribution", {})
            or {}
        )
        if isinstance(attributions, dict) and attributions:
            lines.append("\nCréditos de imagem:")
            seen_credits = set()
            for data in attributions.values():
                if not isinstance(data, dict):
                    continue
                author = str(
                    data.get("author")
                    or data.get("credit")
                    or "autor não informado"
                ).strip()
                license_name = str(
                    data.get("license")
                    or "licença registrada na fonte"
                ).strip()
                source_url = str(
                    data.get("source_url")
                    or ""
                ).strip()
                credit = f"{author} • {license_name}"
                if credit in seen_credits:
                    continue
                seen_credits.add(credit)
                lines.append("• " + credit)
                if source_url:
                    lines.append("  " + source_url)
                if len(seen_credits) >= 3:
                    break

        self._set_details(
            "\n".join(lines)
            or "Registro básico disponível; ainda sem detalhes adicionais nas fontes indexadas."
        )

        if self._rendered_entity_id != entity.id:
            self._rendered_entity_id = entity.id
            self._image_index = 0
            self._image_refs = visual_references(entity)
        self._render_image_reference()

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

    def _render_image_reference(self):
        self.photo = None
        if not self._image_refs:
            self.image_label.config(image="", text="SEM IMAGEM\nDE REFERÊNCIA")
            self.image_counter.config(text="0 / 0")
            return

        self._image_index %= len(self._image_refs)
        path = Path(self._image_refs[self._image_index])
        try:
            image = Image.open(path).convert("RGB")
            image.thumbnail((310, 430), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=self.photo, text="")
        except (OSError, ValueError, tk.TclError) as exc:
            log.debug("Imagem de personagem indisponível (%s): %s", path, exc)
            self.image_label.config(image="", text="IMAGEM INDISPONÍVEL")
        self.image_counter.config(
            text=f"{self._image_index + 1} / {len(self._image_refs)}"
        )
