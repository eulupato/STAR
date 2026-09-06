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
        diagnostics = [
            ("CORE", "ATIVO"),
            ("MEMÓRIA", "INICIALIZADA"),
            ("STT", "PRONTO" if self.voice.stt_configured else "NÃO INSTALADO"),
            ("TTS", self.voice.mode.upper()),
            ("KNOWLEDGE", f"{packs.get('packs', 0)} packs / {packs.get('entries', 0)} entradas"),
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
        """Ilha dos Heróis usando exclusivamente o Knowledge Pack local."""
        self.current_screen = "heroes"
        _root, content = self._scene(
            "HERÓIS",
            "STAR WORLD",
            self.show_hub,
            subtitle="Catálogo local · consulta offline · Knowledge Pack",
        )

        manager = getattr(self.brain, "packs", None)
        try:
            entries = manager.list_entries("heroes") if manager is not None else []
            pack_info = (manager.list() or {}).get("heroes", {}) if manager is not None else {}
        except Exception:
            entries = []
            pack_info = {}

        if not entries:
            panel = tk.Frame(content, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
            panel.place(relx=.5, rely=.5, anchor="center", width=650, height=320)
            tk.Label(panel, text="🦸", bg=PANEL_2, fg=PINK, font=("Segoe UI Emoji", 44)).pack(pady=(42, 10))
            tk.Label(panel, text="AGUARDANDO KNOWLEDGE PACK", bg=PANEL_2, fg=GOLD, font=PIXEL_LABEL).pack()
            tk.Label(
                panel,
                text="Nenhuma entrada estruturada foi carregada para Heróis. A interface não inventa biografias e não depende de internet para preencher lacunas.",
                bg=PANEL_2,
                fg=TEXT,
                font=BODY_FONT,
                wraplength=540,
                justify="center",
            ).pack(pady=20)
            return

        root = tk.Frame(content, bg=BG)
        root.pack(fill="both", expand=True, padx=34, pady=12)
        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", pady=(0, 8))
        storage = str(pack_info.get("storage", "local")).upper()
        tk.Label(header, text=f"CATÁLOGO {storage} · {len(entries)} ENTRADAS · EM EXPANSÃO", bg=BG, fg=GREEN, font=SMALL_BOLD).pack(side="left")
        tk.Label(header, text="Sem busca web em tempo de consulta", bg=BG, fg=MUTED, font=SMALL_FONT).pack(side="right")

        left = tk.Frame(root, bg=PANEL_2, width=310, highlightbackground=BORDER, highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        right = tk.Frame(root, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        search_row = tk.Frame(left, bg=PANEL_2)
        search_row.pack(fill="x", padx=10, pady=(12, 8))
        query = tk.Entry(search_row, bg=PANEL_3, fg=TEXT, insertbackground=TEXT, relief=tk.FLAT, font=BODY_FONT)
        query.pack(side="left", fill="x", expand=True, ipady=7)

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
        meta_label = tk.Label(right, text="", bg=PANEL_2, fg=BLUE, font=SMALL_BOLD, justify="left", anchor="w")
        meta_label.pack(fill="x", padx=20)
        answer_box = tk.Text(right, bg=PANEL_3, fg=TEXT, wrap="word", relief=tk.FLAT, font=BODY_FONT, padx=14, pady=14, height=14)
        answer_box.pack(fill="both", expand=True, padx=20, pady=12)
        answer_box.config(state=tk.DISABLED)
        source_label = tk.Label(right, text="", bg=PANEL_2, fg=MUTED, font=SMALL_FONT, wraplength=660, justify="left", anchor="w")
        source_label.pack(fill="x", padx=20, pady=(0, 16))

        visible_entries = list(entries)

        def render_entry(entry):
            if not entry:
                return
            metadata = entry.get("metadata") or {}
            source = entry.get("source") or {}
            title_label.config(text=str(entry.get("title") or "SEM TÍTULO").upper())
            meta_bits = [
                str(metadata.get("universe") or "").strip(),
                str(metadata.get("identity") or "").strip(),
                str(metadata.get("reality_class") or "").upper().strip(),
            ]
            meta_label.config(text=" · ".join(bit for bit in meta_bits if bit))
            answer_box.config(state=tk.NORMAL)
            answer_box.delete("1.0", tk.END)
            answer_box.insert("1.0", str(entry.get("answer") or "Informação indisponível."))
            answer_box.config(state=tk.DISABLED)
            source_text = str(source.get("reference") or "Proveniência local não informada")
            verification = str(source.get("verification") or "").strip()
            asset_status = str(metadata.get("image_status") or "").strip()
            suffix = []
            if verification:
                suffix.append(verification)
            if asset_status:
                suffix.append(f"imagem: {asset_status}")
            source_label.config(text="Fonte/proveniência: " + source_text + (" · " + " · ".join(suffix) if suffix else ""))

        def populate(items):
            nonlocal visible_entries
            visible_entries = list(items)
            roster.delete(0, tk.END)
            for entry in visible_entries:
                roster.insert(tk.END, entry.get("title") or "Sem título")
            if visible_entries:
                roster.selection_set(0)
                render_entry(visible_entries[0])

        def on_select(_event=None):
            selection = roster.curselection()
            if selection:
                render_entry(visible_entries[selection[0]])

        def run_search(_event=None):
            text = query.get().strip()
            if not text:
                populate(entries)
                return
            try:
                result = manager.search(text, pack_id="heroes")
            except Exception:
                result = None
            populate([result] if result else [])
            if not result:
                title_label.config(text="NENHUM RESULTADO LOCAL")
                meta_label.config(text="")
                answer_box.config(state=tk.NORMAL)
                answer_box.delete("1.0", tk.END)
                answer_box.insert("1.0", "Esta consulta não existe no catálogo local atual. A STAR não inventou uma ficha para preencher a lacuna.")
                answer_box.config(state=tk.DISABLED)
                source_label.config(text="Catálogo em expansão · funcionamento offline preservado")

        self._button(search_row, "BUSCAR", run_search, accent=True).pack(side="left", padx=(6, 0))
        query.bind("<Return>", run_search)
        roster.bind("<<ListboxSelect>>", on_select)
        populate(entries)

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
