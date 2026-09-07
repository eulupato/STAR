"""Parte modular dos ambientes funcionais do STAR WORLD 2D."""
from __future__ import annotations

import os
import platform
import shutil
import tkinter as tk

from gui.theme import (
    BG, PANEL_2, PANEL_3, BORDER, TEXT, MUTED, GOLD, PINK, BLUE,
    GREEN, BODY_FONT, BODY_BOLD, SMALL_FONT, SMALL_BOLD, PIXEL_LABEL,
)


class WorldSystemsMixin:
    def show_cura(self):
        self.current_screen = "cura"
        _root, content = self._scene(
            "CURA",
            "STAR WORLD",
            self.show_hub,
            "cura",
            subtitle="Diagnóstico · proposta · validação · teste",
        )
        try:
            disk = shutil.disk_usage(self._project_root())
            disk_text = f"{disk.free / 1024**3:.1f} GB livres"
        except Exception:
            disk_text = "DESCONHECIDO"
        try:
            packs = self.brain.packs.stats()
        except Exception:
            packs = {"packs": 0, "entries": 0}
        try:
            hero_catalog = self.brain.packs.catalog_stats("heroes")
        except Exception:
            hero_catalog = {"available": False, "total": 0}
        hero_catalog_text = (
            f"{hero_catalog.get('total', 0):,} registros LOCAIS".replace(",", ".")
            if hero_catalog.get("available")
            else "NÃO INSTALADO"
        )
        diagnostics = [
            ("CORE", "ATIVO"),
            ("MEMÓRIA", "INICIALIZADA"),
            ("STT", "PRONTO" if self.voice.stt_configured else "NÃO INSTALADO"),
            ("TTS", self.voice.mode.upper()),
            ("KNOWLEDGE", f"{packs.get('packs', 0)} packs / {packs.get('entries', 0)} fichas"),
            ("HERÓIS CATÁLOGO", hero_catalog_text),
            ("DISCO", disk_text),
            ("SISTEMA", platform.system()),
            ("DEVICE GATEWAY", "OPT-IN" if not os.getenv("STAR_DEVICE_GATEWAY") else "SOLICITADO"),
        ]
        panel = tk.Frame(content, bg="#07101B", highlightbackground=BORDER, highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=80, pady=12)
        banner = self._image_banner(panel, "cura", (820, 240))
        if banner:
            banner.pack(fill="x", padx=18, pady=(18, 4))
        tk.Label(panel, text="STAR STATUS · TELEMETRIA DISPONÍVEL", bg=PANEL_2, fg=BLUE, font=PIXEL_LABEL).pack(pady=14)
        for name, value in diagnostics:
            row = tk.Frame(panel, bg=PANEL_3)
            row.pack(fill="x", padx=18, pady=3)
            tk.Label(row, text=name, bg=PANEL_3, fg=MUTED, font=SMALL_BOLD).pack(side="left", padx=10, pady=8)
            tk.Label(row, text=value, bg=PANEL_3, fg=GREEN if value in {"ATIVO", "INICIALIZADA", "PRONTO"} else TEXT, font=BODY_BOLD).pack(side="right", padx=10)
        tk.Label(
            panel,
            text="CURA V1.9 não altera o sistema automaticamente. Fluxo: diagnóstico → identificação → proposta → validação → aplicação autorizada → teste.",
            bg=PANEL_2,
            fg=GOLD,
            font=BODY_FONT,
            wraplength=760,
            justify="center",
        ).pack(padx=20, pady=18)

    def show_mail(self):
        self.current_screen = "mail"
        _root, content = self._scene("CORREIOS", "STAR WORLD", self.show_hub, subtitle="Encomendas · objetos · inventário")
        left = tk.Frame(content, bg=PANEL_2)
        left.pack(side="left", fill="both", expand=True, padx=(0, 7), pady=8)
        tk.Label(left, text="ENCOMENDAS", bg=PANEL_2, fg=GOLD, font=PIXEL_LABEL).pack(pady=14)
        for item in self.world.get("mail", []):
            row = tk.Frame(left, bg=PANEL_3)
            row.pack(fill="x", padx=12, pady=4)
            tk.Label(row, text=f"{'●' if item['status'] == 'unread' else '○'} {item['title']}", bg=PANEL_3, fg=TEXT, font=BODY_FONT).pack(side="left", padx=8, pady=8)
            self._button(row, "ABRIR", lambda x=item: self._open_package(x), subtle=True).pack(side="right", padx=5)
        right = tk.Frame(content, bg=PANEL_2)
        right.pack(side="right", fill="both", expand=True, padx=(7, 0), pady=8)
        tk.Label(right, text="INVENTÁRIO", bg=PANEL_2, fg=PINK, font=PIXEL_LABEL).pack(pady=14)
        for item in self.world.get("inventory", []):
            tk.Label(right, text=f"◆ {item.get('name')}", bg=PANEL_3, fg=TEXT, font=BODY_FONT, padx=10, pady=8).pack(fill="x", padx=12, pady=3)

    def _open_package(self, item):
        mail = self.world.get("mail", [])
        for current in mail:
            if current.get("id") == item.get("id"):
                current["status"] = "read"
        inventory = self.world.get("inventory", [])
        if not any(current.get("source") == item.get("id") for current in inventory):
            inventory.append({"name": item.get("item"), "source": item.get("id"), "description": item.get("description")})
        self.world.set("mail", mail)
        self.world.set("inventory", inventory)
        self.show_mail()
        self.window.after(60, lambda: self._notice(item.get("title"), item.get("description")))

    def show_heroes(self):
        """Ilha dos Heróis: fichas curadas + inventário Marvel local sob demanda."""
        self.current_screen = "heroes"
        _root, content = self._scene(
            "HERÓIS",
            "STAR WORLD",
            self.show_hub,
            subtitle="Arquivo multiversal · catálogo local · consulta offline",
        )

        manager = getattr(self.brain, "packs", None)
        try:
            curated = manager.list_entries("heroes") if manager is not None else []
            pack_info = (manager.list() or {}).get("heroes", {}) if manager is not None else {}
            catalog_stats = manager.catalog_stats("heroes") if manager is not None else {}
        except Exception as exc:
            print(f"❌ HERÓIS: falha ao ler Knowledge Pack: {exc}")
            curated = []
            pack_info = {}
            catalog_stats = {}

        catalog_available = bool(catalog_stats.get("available"))
        expected_total = int(catalog_stats.get("expected_total") or 0)

        if not curated and not catalog_available:
            panel = tk.Frame(content, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
            panel.place(relx=.5, rely=.5, anchor="center", width=680, height=350)
            tk.Label(panel, text="🦸", bg=PANEL_2, fg=PINK, font=("Segoe UI Emoji", 44)).pack(pady=(36, 8))
            tk.Label(panel, text="ARQUIVO DE HERÓIS INDISPONÍVEL", bg=PANEL_2, fg=GOLD, font=PIXEL_LABEL).pack()
            tk.Label(
                panel,
                text=(
                    "Nenhuma ficha estruturada e nenhum catálogo local foram encontrados. "
                    "A STAR não inventa biografias nem usa a web para preencher lacunas."
                ),
                bg=PANEL_2,
                fg=TEXT,
                font=BODY_FONT,
                wraplength=560,
                justify="center",
            ).pack(pady=18)
            return

        root = tk.Frame(content, bg=BG)
        root.pack(fill="both", expand=True, padx=28, pady=10)

        top = tk.Frame(root, bg="#081321", highlightbackground=BORDER, highlightthickness=1)
        top.pack(fill="x", pady=(0, 10))
        title_row = tk.Frame(top, bg="#081321")
        title_row.pack(fill="x", padx=18, pady=(14, 5))
        tk.Label(
            title_row,
            text="★ HERO ARCHIVE · STAR",
            bg="#081321",
            fg=GOLD,
            font=PIXEL_LABEL,
        ).pack(side="left")
        storage = str(pack_info.get("storage", "local")).upper()
        tk.Label(
            title_row,
            text=f"{storage} · OFFLINE-FIRST",
            bg="#081321",
            fg=GREEN,
            font=SMALL_BOLD,
        ).pack(side="right")

        stats_row = tk.Frame(top, bg="#081321")
        stats_row.pack(fill="x", padx=18, pady=(2, 14))
        self._hero_stat_card(stats_row, "FICHAS", len(curated), PINK)
        if catalog_available:
            self._hero_stat_card(stats_row, "PERSONAGENS", catalog_stats.get("characters", 0), BLUE)
            self._hero_stat_card(stats_row, "EQUIPES", catalog_stats.get("teams", 0), GOLD)
            self._hero_stat_card(stats_row, "CATÁLOGO", catalog_stats.get("total", 0), GREEN)
        else:
            self._hero_stat_card(stats_row, "CATÁLOGO", "NÃO INSTALADO", GOLD)
            if expected_total:
                self._hero_stat_card(stats_row, "SNAPSHOT ESPERADO", expected_total, MUTED)

        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=PANEL_2, width=390, highlightbackground=BORDER, highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        right = tk.Frame(body, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        search_row = tk.Frame(left, bg=PANEL_2)
        search_row.pack(fill="x", padx=10, pady=(12, 6))
        query = tk.Entry(
            search_row,
            bg=PANEL_3,
            fg=TEXT,
            insertbackground=TEXT,
            relief=tk.FLAT,
            font=BODY_FONT,
        )
        query.pack(side="left", fill="x", expand=True, ipady=7)

        status_label = tk.Label(
            left,
            text="",
            bg=PANEL_2,
            fg=MUTED,
            font=SMALL_FONT,
            anchor="w",
        )
        status_label.pack(fill="x", padx=12, pady=(0, 4))

        filter_state = {"value": "TODOS"}
        filter_row = tk.Frame(left, bg=PANEL_2)
        filter_row.pack(fill="x", padx=8, pady=(0, 8))

        list_frame = tk.Frame(left, bg=PANEL_2)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        roster = tk.Listbox(
            list_frame,
            bg=PANEL_3,
            fg=TEXT,
            selectbackground="#243D5E",
            selectforeground=TEXT,
            relief=tk.FLAT,
            highlightthickness=0,
            font=BODY_FONT,
            yscrollcommand=scrollbar.set,
            activestyle="none",
        )
        roster.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=roster.yview)

        title_label = tk.Label(right, text="SELECIONE UM REGISTRO", bg=PANEL_2, fg=PINK, font=PIXEL_LABEL)
        title_label.pack(anchor="w", padx=20, pady=(20, 8))
        badge_label = tk.Label(right, text="", bg=PANEL_2, fg=GOLD, font=SMALL_BOLD, justify="left", anchor="w")
        badge_label.pack(fill="x", padx=20)
        meta_label = tk.Label(right, text="", bg=PANEL_2, fg=BLUE, font=SMALL_BOLD, justify="left", anchor="w")
        meta_label.pack(fill="x", padx=20, pady=(4, 0))
        answer_box = tk.Text(
            right,
            bg=PANEL_3,
            fg=TEXT,
            wrap="word",
            relief=tk.FLAT,
            font=BODY_FONT,
            padx=14,
            pady=14,
            height=14,
        )
        answer_box.pack(fill="both", expand=True, padx=20, pady=12)
        answer_box.config(state=tk.DISABLED)
        source_label = tk.Label(
            right,
            text="",
            bg=PANEL_2,
            fg=MUTED,
            font=SMALL_FONT,
            wraplength=700,
            justify="left",
            anchor="w",
        )
        source_label.pack(fill="x", padx=20, pady=(0, 16))

        visible_entries = []

        def set_answer(text):
            answer_box.config(state=tk.NORMAL)
            answer_box.delete("1.0", tk.END)
            answer_box.insert("1.0", text)
            answer_box.config(state=tk.DISABLED)

        def render_entry(entry):
            if not entry:
                return
            metadata = entry.get("metadata") or {}
            source = entry.get("source") or {}
            title = str(entry.get("title") or "SEM TÍTULO")
            title_label.config(text=title.upper())

            if metadata.get("catalog_only"):
                entity_type = str(entry.get("entity_type") or "").lower()
                badge = "PERSONAGEM · INVENTÁRIO" if entity_type == "character" else "EQUIPE · INVENTÁRIO"
                badge_label.config(text=badge, fg=GOLD if entity_type == "team" else BLUE)
                continuity = str(metadata.get("continuity") or "Marvel Database")
                meta_label.config(text=f"MARVEL · {continuity} · REGISTRO LOCAL")
                set_answer(
                    "Este registro faz parte do inventário local Marvel Database instalado na STAR. "
                    "O nome, o tipo de entidade e a continuidade foram preservados offline. "
                    "A ficha biográfica detalhada ainda não foi enriquecida; a STAR não inventa "
                    "história, poderes ou relações para preencher informações ausentes."
                )
                official = bool(source.get("official", False))
                source_label.config(
                    text=(
                        "Fonte do inventário: "
                        + str(source.get("reference") or "Marvel Database / Fandom")
                        + (" · oficial" if official else " · fonte comunitária, não oficial da Marvel")
                        + " · imagens não foram copiadas."
                    )
                )
                return

            badge_label.config(text="FICHA ENRIQUECIDA LOCAL", fg=PINK)
            meta_bits = [
                str(metadata.get("universe") or "").strip(),
                str(metadata.get("identity") or "").strip(),
                str(metadata.get("reality_class") or "").upper().strip(),
            ]
            meta_label.config(text=" · ".join(bit for bit in meta_bits if bit))
            set_answer(str(entry.get("answer") or "Informação indisponível."))
            source_text = str(source.get("reference") or "Proveniência local não informada")
            verification = str(source.get("verification") or "").strip()
            asset_status = str(metadata.get("image_status") or "").strip()
            suffix = []
            if verification:
                suffix.append(verification)
            if asset_status:
                suffix.append(f"imagem: {asset_status}")
            source_label.config(
                text="Fonte/proveniência: "
                + source_text
                + (" · " + " · ".join(suffix) if suffix else "")
            )

        def populate(items, message=None):
            nonlocal visible_entries
            visible_entries = list(items)
            roster.delete(0, tk.END)
            for entry in visible_entries:
                metadata = entry.get("metadata") or {}
                if metadata.get("catalog_only"):
                    prefix = "◆" if entry.get("entity_type") == "character" else "◇"
                else:
                    prefix = "★"
                roster.insert(tk.END, f"{prefix} {entry.get('title') or 'Sem título'}")
            if message is None:
                message = f"{len(visible_entries)} resultados exibidos"
                if catalog_available and len(visible_entries) >= 160:
                    message += " · refine a busca para ver mais"
            status_label.config(text=message)
            if visible_entries:
                roster.selection_set(0)
                render_entry(visible_entries[0])
            else:
                title_label.config(text="NENHUM RESULTADO LOCAL")
                badge_label.config(text="")
                meta_label.config(text="")
                set_answer(
                    "Nenhum registro correspondente foi encontrado no catálogo local. "
                    "A STAR não criou uma ficha artificial para preencher a lacuna."
                )
                source_label.config(text="Consulta local/offline preservada.")

        def on_select(_event=None):
            selection = roster.curselection()
            if selection and selection[0] < len(visible_entries):
                render_entry(visible_entries[selection[0]])

        def current_entity_type():
            value = filter_state["value"]
            if value == "PERSONAGENS":
                return "character"
            if value == "EQUIPES":
                return "team"
            return None

        def run_search(_event=None):
            text = query.get().strip()
            mode = filter_state["value"]

            if mode == "FICHAS":
                if not text:
                    populate(curated)
                    return
                try:
                    result = manager.search(text, pack_id="heroes") if manager else None
                except Exception as exc:
                    print(f"❌ HERÓIS: falha na busca de ficha: {exc}")
                    populate([], "Falha ao consultar fichas locais.")
                    return
                populate([result] if result else [])
                return

            if not catalog_available:
                if text:
                    try:
                        result = manager.search(text, pack_id="heroes") if manager else None
                    except Exception as exc:
                        print(f"❌ HERÓIS: falha na busca local: {exc}")
                        result = None
                    populate([result] if result else [], "Catálogo Marvel local ainda não instalado.")
                else:
                    populate(curated, "Catálogo Marvel local ainda não instalado · exibindo fichas disponíveis.")
                return

            status_label.config(text="Consultando catálogo local...")
            try:
                self.window.update_idletasks()
            except tk.TclError:
                return

            try:
                if text:
                    catalog_items = manager.catalog_search(
                        text,
                        "heroes",
                        entity_type=current_entity_type(),
                        limit=160,
                    )
                else:
                    catalog_items = manager.catalog_list(
                        "heroes",
                        entity_type=current_entity_type(),
                        limit=max(1, 160 - (len(curated) if mode == "TODOS" else 0)),
                    )
            except Exception as exc:
                print(f"❌ HERÓIS: falha no catálogo local: {exc}")
                populate([], "Falha ao consultar o catálogo local. Veja o terminal para o erro.")
                return

            items = list(catalog_items)
            if mode == "TODOS":
                if text:
                    try:
                        rich = manager.search(text, pack_id="heroes") if manager else None
                    except Exception as exc:
                        print(f"❌ HERÓIS: falha ao cruzar ficha enriquecida: {exc}")
                        rich = None
                    if rich:
                        rich_title = str(rich.get("title") or "").casefold()
                        items = [rich] + [
                            item for item in items
                            if str(item.get("title") or "").casefold() != rich_title
                        ]
                else:
                    items = list(curated) + items
            populate(items[:160])

        def select_filter(value):
            filter_state["value"] = value
            for name, button in filter_buttons.items():
                button.config(
                    bg="#243D5E" if name == value else PANEL_3,
                    fg=TEXT,
                )
            run_search()

        filter_buttons = {}
        for value in ("TODOS", "PERSONAGENS", "EQUIPES", "FICHAS"):
            button = tk.Button(
                filter_row,
                text=value,
                command=lambda v=value: select_filter(v),
                bg="#243D5E" if value == "TODOS" else PANEL_3,
                fg=TEXT,
                activebackground="#243D5E",
                activeforeground=TEXT,
                relief=tk.FLAT,
                font=SMALL_BOLD,
                padx=7,
                pady=5,
                cursor="hand2",
            )
            button.pack(side="left", padx=2)
            filter_buttons[value] = button

        self._button(search_row, "BUSCAR", run_search, accent=True).pack(side="left", padx=(6, 0))
        query.bind("<Return>", run_search)
        roster.bind("<<ListboxSelect>>", on_select)

        footer = tk.Frame(right, bg=PANEL_2)
        footer.pack(fill="x", padx=20, pady=(0, 16))
        if not catalog_available:
            tk.Label(
                footer,
                text="Para instalar o inventário completo: python tools/install_marvel_catalog.py",
                bg=PANEL_2,
                fg=GOLD,
                font=SMALL_FONT,
            ).pack(side="left")
        self._button(
            footer,
            "RECARREGAR CATÁLOGO",
            lambda: self._reload_heroes_catalog(manager),
            subtle=True,
        ).pack(side="right")

        run_search()

    def _hero_stat_card(self, parent, label, value, color):
        card = tk.Frame(parent, bg=PANEL_3, highlightbackground=BORDER, highlightthickness=1)
        card.pack(side="left", padx=(0, 8))
        display = f"{value:,}".replace(",", ".") if isinstance(value, int) else str(value)
        tk.Label(card, text=display, bg=PANEL_3, fg=color, font=BODY_BOLD).pack(padx=12, pady=(7, 0))
        tk.Label(card, text=label, bg=PANEL_3, fg=MUTED, font=SMALL_FONT).pack(padx=12, pady=(0, 7))

    def _reload_heroes_catalog(self, manager):
        if manager is None:
            self._notice("HERÓIS", "KnowledgePackManager indisponível.")
            return
        try:
            manager.scan()
        except Exception as exc:
            print(f"❌ HERÓIS: falha ao recarregar catálogo: {exc}")
            self._notice("HERÓIS", "Falha ao recarregar o catálogo local. Veja o terminal.")
            return
        self.show_heroes()

    def show_languages(self):
        self.current_screen = "languages"
        _root, content = self._scene("IDIOMAS", "STAR WORLD", self.show_hub, subtitle="Cartões · vocabulário · estudo local")
        body = self._scrollable(content)
        for lang in self.world.get("languages", []):
            card = self._card(body, f"{lang['name']} · {lang['status']}", "Cartões iniciais desta interface 2D.", BLUE)
            card.pack(fill="x", padx=60, pady=6)
            row = tk.Frame(card, bg=PANEL_2)
            row.pack(fill="x", padx=14, pady=(0, 12))
            for front, back in lang.get("cards", [])[:5]:
                self._button(row, front, lambda a=front, b=back: self._notice(a, b), subtle=True).pack(side="left", padx=3)
