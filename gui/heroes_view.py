"""Interface pixel-art funcional da Ilha dos Heróis.

A camada visual consome somente o KnowledgeEngine. Ela não executa SQL, não
descobre personagens e não inventa dados ausentes; o catálogo continua sendo
responsabilidade do subsistema KNOWLEDGE.
"""
from __future__ import annotations

import math
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk

from core.logging_config import get_logger
from gui.components.carousel import CarouselController
from knowledge.hero_visuals import theme_for_entity, visual_references
from knowledge.sources.marvel_catalog import MarvelMasterCatalog

log = get_logger("gui.heroes")

ROSTER_PAGE_SIZE = 8
TAB_LABELS = {
    "info": "INFORMAÇÕES",
    "biography": "BIOGRAFIA",
    "relations": "RELAÇÕES",
    "history": "HISTÓRIA",
    "appearances": "APARIÇÕES",
}

COLORS = {
    "bg": "#173D7C",
    "bg_deep": "#102F68",
    "panel": "#28569B",
    "panel_dark": "#193B76",
    "panel_soft": "#3565AD",
    "panel_selected": "#3C75C4",
    "cyan": "#78E7FF",
    "cyan_soft": "#B7F3FF",
    "pink": "#F2A8DD",
    "pink_soft": "#F8D2EC",
    "gold": "#FFD86A",
    "white": "#F7FBFF",
    "muted": "#C9D9F3",
    "outline": "#9BCBFF",
    "danger": "#FF91A8",
}

STAT_KEYS = (
    ("FORÇA", ("strength", "forca", "force")),
    ("DEFESA", ("defense", "defesa")),
    ("VELOCIDADE", ("speed", "velocidade")),
    ("ENERGIA", ("energy", "energia")),
    ("INTELIGÊNCIA", ("intelligence", "inteligencia")),
)


def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def _field(value, fallback="—") -> str:
    text = _as_text(value)
    return text if text else fallback


def _real_name(entity) -> str:
    return _as_text((getattr(entity, "attributes", {}) or {}).get("real_name"))


def _relationship_lines(entity) -> list[str]:
    grouped: dict[str, list[str]] = {}
    for relation in getattr(entity, "relationships", []) or []:
        name = _as_text(getattr(relation, "target_name", ""))
        predicate = _as_text(getattr(relation, "predicate", "")) or "relação"
        if name:
            grouped.setdefault(predicate, []).append(name)

    lines = []
    for predicate, names in grouped.items():
        lines.append(f"{predicate.upper()}: {', '.join(names)}")
    return lines


def hero_tab_text(entity, tab: str) -> str:
    """Texto puro das abas da ficha; útil também para testes e exportação."""
    if entity is None:
        return "NENHUM PERSONAGEM SELECIONADO."

    attributes = getattr(entity, "attributes", {}) or {}
    metadata = getattr(entity, "metadata", {}) or {}

    if tab == "biography":
        lines = []
        description = _as_text(getattr(entity, "description", ""))
        description_kind = metadata.get("description_kind")
        if description:
            if description_kind == "catalog_fallback":
                lines.append("DESCRIÇÃO BÁSICA DO CATÁLOGO")
                lines.append("(biografia verificada ainda pendente)\n")
            elif description_kind == "wikidata_short_description":
                lines.append("DESCRIÇÃO CURTA VERIFICADA\n")
            else:
                lines.append("BIOGRAFIA / DESCRIÇÃO\n")
            lines.append(description)
        personality = _as_text(getattr(entity, "personality", ""))
        if personality:
            lines.extend(["", "PERSONALIDADE", personality])
        return "\n".join(lines) if lines else (
            "BIOGRAFIA DETALHADA AINDA NÃO INDEXADA PARA ESTE PERSONAGEM."
        )

    if tab == "relations":
        lines = _relationship_lines(entity)
        teams = _as_text(getattr(entity, "team", []))
        affiliations = _as_text(getattr(entity, "affiliations", []))
        if teams:
            lines.insert(0, f"EQUIPES: {teams}")
        if affiliations:
            lines.insert(1 if teams else 0, f"AFILIAÇÕES: {affiliations}")
        return "\n\n".join(lines) if lines else (
            "RELAÇÕES DETALHADAS AINDA NÃO INDEXADAS PARA ESTE PERSONAGEM."
        )

    if tab == "history":
        lines = [
            f"ORIGEM: {_field(getattr(entity, 'origin', None))}",
            f"LOCAL DE ORIGEM: {_field(getattr(entity, 'origin_place', None))}",
            f"PRIMEIRA APARIÇÃO: {_field(getattr(entity, 'first_appearance', None))}",
            f"CRIADORES: {_field(getattr(entity, 'creators', []))}",
        ]
        history = _as_text(getattr(entity, "history_summary", ""))
        if history:
            lines.extend(["", "HISTÓRIA RESUMIDA", history])
        return "\n".join(lines)

    if tab == "appearances":
        raw = attributes.get("appearances") or metadata.get("appearances") or []
        appearances = _as_text(raw)
        lines = []
        if appearances:
            lines.extend(["APARIÇÕES INDEXADAS", appearances, ""])
        first = _as_text(getattr(entity, "first_appearance", ""))
        if first:
            lines.append(f"PRIMEIRA APARIÇÃO: {first}")
        source_count = len(getattr(entity, "sources", []) or [])
        if source_count:
            lines.append(f"FONTES / REFERÊNCIAS INDEXADAS: {source_count}")
        if not lines:
            return "APARIÇÕES DETALHADAS AINDA NÃO INDEXADAS PARA ESTE PERSONAGEM."
        return "\n".join(lines)

    publisher_origin = (
        _as_text(getattr(entity, "publisher", ""))
        or _as_text(getattr(entity, "origin", ""))
    )
    lines = [
        f"NOME REAL: {_field(_real_name(entity))}",
        f"NOME DE HERÓI: {_field(getattr(entity, 'name', None))}",
        f"UNIVERSO: {_field(getattr(entity, 'universe', None))}",
        f"EDITORA / ORIGEM: {_field(publisher_origin)}",
        f"ESPÉCIE: {_field(getattr(entity, 'species', None))}",
        "",
        f"PODERES: {_field(getattr(entity, 'powers', []))}",
        f"HABILIDADES: {_field(getattr(entity, 'abilities', []))}",
        f"EQUIPAMENTO: {_field(getattr(entity, 'equipment', []))}",
        f"AFILIAÇÕES: {_field(getattr(entity, 'affiliations', []))}",
        f"PRIMEIRA APARIÇÃO: {_field(getattr(entity, 'first_appearance', None))}",
        f"CLASSIFICAÇÃO: {_field(getattr(entity, 'status', None))}",
    ]
    return "\n".join(lines)


def hero_statistic_value(entity, aliases: tuple[str, ...]) -> float | None:
    """Lê somente estatísticas explícitas e já estruturadas (escala 0..10)."""
    if entity is None:
        return None
    attributes = getattr(entity, "attributes", {}) or {}
    metadata = getattr(entity, "metadata", {}) or {}
    stats = (
        attributes.get("statistics")
        or attributes.get("stats")
        or metadata.get("statistics")
        or {}
    )
    if not isinstance(stats, dict):
        stats = {}

    raw = None
    for key in aliases:
        if key in stats:
            raw = stats[key]
            break
        if key in attributes:
            raw = attributes[key]
            break

    if raw is None or isinstance(raw, bool):
        return None
    try:
        if isinstance(raw, str):
            raw = raw.strip()
            if raw.endswith("%"):
                value = float(raw[:-1]) / 10.0
            else:
                value = float(raw)
        else:
            value = float(raw)
    except (TypeError, ValueError):
        return None

    if value < 0 or value > 10:
        return None
    return value


def statistic_bar(value: float | None, blocks: int = 7) -> str:
    if value is None:
        return "—"
    blocks = max(1, int(blocks))
    filled = max(0, min(blocks, round(value / 10 * blocks)))
    return "▰" * filled + "▱" * (blocks - filled)


def full_profile_text(entity) -> str:
    if entity is None:
        return "Nenhum personagem selecionado."

    sections = []
    for tab in ("info", "biography", "relations", "history", "appearances"):
        sections.append(TAB_LABELS[tab])
        sections.append("=" * len(TAB_LABELS[tab]))
        sections.append(hero_tab_text(entity, tab))
        sections.append("")

    aliases = _as_text(getattr(entity, "aliases", []))
    weaknesses = _as_text(getattr(entity, "weaknesses", []))
    weapons = _as_text(getattr(entity, "weapons", []))
    tags = _as_text(getattr(entity, "tags", []))
    if any((aliases, weaknesses, weapons, tags)):
        sections.extend(
            [
                "DADOS COMPLEMENTARES",
                "===================",
                f"ALIASES: {_field(aliases)}",
                f"FRAQUEZAS: {_field(weaknesses)}",
                f"ARMAS: {_field(weapons)}",
                f"TAGS: {_field(tags)}",
                "",
            ]
        )

    sources = getattr(entity, "sources", []) or []
    if sources:
        sections.extend(["FONTES", "======"])
        for source in sources:
            page = f", pág. {source.page}" if getattr(source, "page", None) else ""
            url = f" — {source.url}" if getattr(source, "url", None) else ""
            sections.append(f"• {source.source_ref}{page}{url}")
    return "\n".join(sections).strip()


class HeroesIslandView(tk.Frame):
    def __init__(
        self,
        parent,
        *,
        knowledge,
        palette=None,
        on_selected=None,
        on_home=None,
        on_settings=None,
        on_chat=None,
    ):
        super().__init__(parent, bg=COLORS["bg_deep"])
        self.knowledge = knowledge
        self.palette = palette or {}
        self.on_selected = on_selected
        self.on_home = on_home
        self.on_settings = on_settings
        self.on_chat = on_chat

        self.carousel = CarouselController()
        self.photo = None
        self._thumb_cache: dict[str, ImageTk.PhotoImage] = {}
        self._search_job = None
        self._page = 0
        self._image_index = 0
        self._image_refs: list[str] = []
        self._rendered_entity_id = None
        self._active_tab = "info"
        self._filter_open = False
        self._coverage = self._read_coverage()

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
        self.refresh(reset_page=True)

    def _read_coverage(self) -> dict:
        try:
            return MarvelMasterCatalog().source_metadata().get("coverage", {}) or {}
        except Exception as exc:
            log.debug("Metadados do catálogo Marvel indisponíveis: %s", exc)
            return {}

    def _retro_font(self, size=10, weight="normal"):
        return ("Consolas", size, weight)

    def _build(self):
        self._build_backdrop()
        self._build_header()

        self.main = tk.Frame(self, bg=COLORS["bg"])
        self.main.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        self._build_sidebar(self.main)

        self.workspace = tk.Frame(
            self.main,
            bg=COLORS["bg"],
            highlightbackground=COLORS["outline"],
            highlightthickness=1,
        )
        self.workspace.pack(side="left", fill="both", expand=True, padx=(10, 0))

        self.top = tk.Frame(self.workspace, bg=COLORS["bg"])
        self.top.pack(fill="both", expand=True, padx=8, pady=8)
        self._build_data_panel(self.top)
        self._build_stage(self.top)
        self._build_summary(self.workspace)
        self._build_footer()

        self._build_filter_popup()

    def _build_backdrop(self):
        self.backdrop = tk.Canvas(self, highlightthickness=0, bd=0)
        self.backdrop.place(x=0, y=0, relwidth=1, relheight=1)
        self.backdrop.lower()

        def draw(_event=None):
            width = max(self.backdrop.winfo_width(), 1)
            height = max(self.backdrop.winfo_height(), 1)
            self.backdrop.delete("hero-bg")
            top = (18, 59, 127)
            bottom = (210, 126, 194)
            steps = 54
            for index in range(steps):
                t = index / max(steps - 1, 1)
                rgb = tuple(
                    round(a * (1 - t) + b * t)
                    for a, b in zip(top, bottom)
                )
                y0 = round(index * height / steps)
                y1 = round((index + 1) * height / steps) + 1
                color = "#" + "".join(f"{channel:02X}" for channel in rgb)
                self.backdrop.create_rectangle(
                    0, y0, width, y1, fill=color, outline="", tags="hero-bg"
                )
            stars = (
                (0.02, 0.03), (0.12, 0.07), (0.30, 0.025), (0.63, 0.06),
                (0.78, 0.025), (0.91, 0.08), (0.97, 0.03), (0.03, 0.93),
                (0.26, 0.96), (0.67, 0.94), (0.97, 0.90),
            )
            for x, y in stars:
                px, py = int(width * x), int(height * y)
                self.backdrop.create_text(
                    px, py, text="✦", fill=COLORS["cyan_soft"],
                    font=self._retro_font(10, "bold"), tags="hero-bg"
                )

        self.backdrop.bind("<Configure>", draw)

    def _build_header(self):
        header = tk.Frame(self, bg=COLORS["bg_deep"], height=72)
        header.pack(fill="x", padx=14, pady=(10, 6))
        header.pack_propagate(False)

        left = tk.Frame(header, bg=COLORS["bg_deep"])
        left.pack(side="left", fill="y")
        tk.Label(
            left,
            text="★",
            bg=COLORS["bg_deep"],
            fg=COLORS["gold"],
            font=self._retro_font(30, "bold"),
        ).pack(side="left", padx=(8, 10))
        titles = tk.Frame(left, bg=COLORS["bg_deep"])
        titles.pack(side="left", fill="y")
        tk.Label(
            titles,
            text="STAR WORLD",
            bg=COLORS["bg_deep"],
            fg=COLORS["cyan"],
            font=self._retro_font(20, "bold"),
            anchor="w",
        ).pack(anchor="w", pady=(6, 0))
        tk.Label(
            titles,
            text="ILHA DOS HERÓIS",
            bg=COLORS["bg_deep"],
            fg=COLORS["white"],
            font=self._retro_font(11, "bold"),
            anchor="w",
        ).pack(anchor="w")

        right = tk.Frame(header, bg=COLORS["bg_deep"])
        right.pack(side="right", fill="y", padx=6)

        self.header_count = tk.Label(
            right,
            text="CATÁLOGO DE HERÓIS",
            bg=COLORS["bg_deep"],
            fg=COLORS["cyan"],
            justify="right",
            font=self._retro_font(10, "bold"),
        )
        self.header_count.pack(side="left", padx=(0, 12), pady=8)

        if self.on_chat:
            self._icon_button(right, "💬", self.on_chat).pack(
                side="left", padx=2, pady=12
            )
        if self.on_settings:
            self._icon_button(right, "⚙", self.on_settings).pack(
                side="left", padx=2, pady=12
            )
        if self.on_home:
            self._icon_button(right, "⌂", self.on_home, width=3).pack(
                side="left", padx=(5, 0), pady=10
            )

    def _icon_button(self, parent, text, command, width=2):
        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            bg=COLORS["panel_dark"],
            fg=COLORS["white"],
            activebackground=COLORS["panel_selected"],
            activeforeground=COLORS["white"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            font=self._retro_font(14, "bold"),
        )

    def _build_sidebar(self, parent):
        self.sidebar = tk.Frame(
            parent,
            bg=COLORS["panel_dark"],
            width=270,
            highlightbackground=COLORS["outline"],
            highlightthickness=1,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        search_wrap = tk.Frame(self.sidebar, bg=COLORS["panel_dark"])
        search_wrap.pack(fill="x", padx=10, pady=(10, 6))

        self.search = tk.Entry(
            search_wrap,
            textvariable=self.search_var,
            bg=COLORS["white"],
            fg="#1A2842",
            insertbackground="#1A2842",
            relief=tk.FLAT,
            font=self._retro_font(9, "bold"),
        )
        self.search.pack(side="left", fill="x", expand=True, ipady=8)
        self.search.bind("<KeyRelease>", self._schedule_refresh)

        tk.Button(
            search_wrap,
            text="⌕",
            command=lambda: self.refresh(reset_page=True),
            bg=COLORS["white"],
            fg="#6076B5",
            activebackground=COLORS["cyan_soft"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            font=self._retro_font(14, "bold"),
            width=2,
        ).pack(side="left", ipady=3)

        tools = tk.Frame(self.sidebar, bg=COLORS["panel_dark"])
        tools.pack(fill="x", padx=10, pady=(0, 6))
        tk.Label(
            tools,
            text="PESQUISA DE HERÓIS",
            bg=COLORS["panel_dark"],
            fg=COLORS["muted"],
            font=self._retro_font(7, "bold"),
        ).pack(side="left")
        tk.Button(
            tools,
            text="⚙ FILTROS",
            command=self._toggle_filters,
            bg=COLORS["panel"],
            fg=COLORS["cyan_soft"],
            activebackground=COLORS["panel_selected"],
            activeforeground=COLORS["white"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            font=self._retro_font(7, "bold"),
            padx=8,
            pady=3,
        ).pack(side="right")

        self.roster = tk.Frame(self.sidebar, bg=COLORS["panel_dark"])
        self.roster.pack(fill="both", expand=True, padx=8)
        self._roster_buttons: list[tk.Button] = []

        pager = tk.Frame(self.sidebar, bg=COLORS["panel_dark"])
        pager.pack(fill="x", padx=10, pady=(6, 10))
        self.page_prev = tk.Button(
            pager,
            text="‹",
            command=lambda: self.change_page(-1),
            bg=COLORS["panel"],
            fg=COLORS["white"],
            activebackground=COLORS["panel_selected"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            font=self._retro_font(15, "bold"),
            width=3,
        )
        self.page_prev.pack(side="left")
        self.page_label = tk.Label(
            pager,
            text="0 / 0",
            bg=COLORS["panel"],
            fg=COLORS["white"],
            font=self._retro_font(9, "bold"),
            padx=14,
            pady=7,
        )
        self.page_label.pack(side="left", fill="x", expand=True, padx=4)
        self.page_next = tk.Button(
            pager,
            text="›",
            command=lambda: self.change_page(1),
            bg=COLORS["panel"],
            fg=COLORS["white"],
            activebackground=COLORS["panel_selected"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            font=self._retro_font(15, "bold"),
            width=3,
        )
        self.page_next.pack(side="right")

        self.coverage_label = tk.Label(
            self.sidebar,
            text="",
            bg=COLORS["panel_dark"],
            fg=COLORS["muted"],
            font=self._retro_font(6, "bold"),
            wraplength=248,
            justify="left",
        )
        self.coverage_label.pack(fill="x", padx=10, pady=(0, 8))

    def _build_filter_popup(self):
        self.filter_popup = tk.Frame(
            self,
            bg=COLORS["panel_dark"],
            highlightbackground=COLORS["cyan"],
            highlightthickness=1,
        )
        top = tk.Frame(self.filter_popup, bg=COLORS["panel_dark"])
        top.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(
            top,
            text="FILTROS AVANÇADOS",
            bg=COLORS["panel_dark"],
            fg=COLORS["cyan"],
            font=self._retro_font(9, "bold"),
        ).pack(side="left")
        tk.Button(
            top,
            text="×",
            command=self._toggle_filters,
            bg=COLORS["panel_dark"],
            fg=COLORS["white"],
            activebackground=COLORS["panel_selected"],
            relief=tk.FLAT,
            bd=0,
            font=self._retro_font(13, "bold"),
        ).pack(side="right")

        universe = tk.Frame(self.filter_popup, bg=COLORS["panel_dark"])
        universe.pack(fill="x", padx=10, pady=3)
        tk.Label(
            universe,
            text="UNIVERSO",
            bg=COLORS["panel_dark"],
            fg=COLORS["muted"],
            font=self._retro_font(7, "bold"),
            width=13,
            anchor="w",
        ).pack(side="left")
        option = tk.OptionMenu(
            universe,
            self.universe_var,
            "Todos",
            "Marvel",
            "DC",
            command=lambda _value: self.refresh(reset_page=True),
        )
        option.config(
            bg=COLORS["panel"],
            fg=COLORS["white"],
            activebackground=COLORS["panel_selected"],
            activeforeground=COLORS["white"],
            relief=tk.FLAT,
            highlightthickness=0,
            font=self._retro_font(8, "bold"),
        )
        option["menu"].config(
            bg=COLORS["panel_dark"], fg=COLORS["white"],
            font=self._retro_font(8)
        )
        option.pack(side="left", fill="x", expand=True)

        fields = (
            ("EQUIPE", "team"),
            ("PODER", "power"),
            ("HABILIDADE", "ability"),
            ("TAG", "tag"),
            ("TIPO / ESPÉCIE", "species"),
            ("RELAÇÃO COM", "relationship"),
        )
        for label, key in fields:
            row = tk.Frame(self.filter_popup, bg=COLORS["panel_dark"])
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(
                row,
                text=label,
                bg=COLORS["panel_dark"],
                fg=COLORS["muted"],
                font=self._retro_font(7, "bold"),
                width=13,
                anchor="w",
            ).pack(side="left")
            entry = tk.Entry(
                row,
                textvariable=self.filter_vars[key],
                bg=COLORS["white"],
                fg="#1A2842",
                insertbackground="#1A2842",
                relief=tk.FLAT,
                font=self._retro_font(8),
            )
            entry.pack(side="left", fill="x", expand=True, ipady=4)
            entry.bind("<KeyRelease>", self._schedule_refresh)

        bottom = tk.Frame(self.filter_popup, bg=COLORS["panel_dark"])
        bottom.pack(fill="x", padx=10, pady=8)
        tk.Button(
            bottom,
            text="LIMPAR",
            command=self._clear_filters,
            bg=COLORS["panel"],
            fg=COLORS["white"],
            activebackground=COLORS["panel_selected"],
            relief=tk.FLAT,
            bd=0,
            font=self._retro_font(7, "bold"),
            padx=10,
            pady=5,
        ).pack(side="left")
        tk.Button(
            bottom,
            text="APLICAR",
            command=lambda: self.refresh(reset_page=True),
            bg=COLORS["panel_selected"],
            fg=COLORS["white"],
            activebackground=COLORS["cyan"],
            activeforeground=COLORS["bg_deep"],
            relief=tk.FLAT,
            bd=0,
            font=self._retro_font(7, "bold"),
            padx=10,
            pady=5,
        ).pack(side="right")

    def _build_data_panel(self, parent):
        self.data_panel = tk.Frame(
            parent,
            bg=COLORS["panel"],
            width=300,
            highlightbackground=COLORS["pink_soft"],
            highlightthickness=1,
        )
        self.data_panel.pack(side="left", fill="y")
        self.data_panel.pack_propagate(False)

        self.data_title = tk.Label(
            self.data_panel,
            text="✦ DADOS DO PERSONAGEM ✦",
            bg=COLORS["panel"],
            fg=COLORS["cyan_soft"],
            font=self._retro_font(10, "bold"),
            pady=10,
        )
        self.data_title.pack(fill="x")

        self.details = tk.Text(
            self.data_panel,
            bg=COLORS["panel"],
            fg=COLORS["white"],
            insertbackground=COLORS["white"],
            relief=tk.FLAT,
            bd=0,
            wrap="word",
            state=tk.DISABLED,
            font=self._retro_font(8),
            padx=12,
            pady=4,
        )
        self.details.pack(fill="both", expand=True, padx=4, pady=(0, 8))
        self.details.tag_configure(
            "label", foreground=COLORS["cyan_soft"],
            font=self._retro_font(8, "bold")
        )

    def _build_stage(self, parent):
        self.stage = tk.Frame(
            parent,
            bg=COLORS["panel_soft"],
            highlightbackground=COLORS["pink_soft"],
            highlightthickness=1,
        )
        self.stage.pack(side="left", fill="both", expand=True, padx=(8, 0))

        self.name_label = tk.Label(
            self.stage,
            text="",
            bg=COLORS["panel_soft"],
            fg=COLORS["white"],
            font=self._retro_font(17, "bold"),
            pady=7,
        )
        self.name_label.pack(fill="x", padx=54)

        self.stage_rule = tk.Label(
            self.stage,
            text="────────  ☆  ────────",
            bg=COLORS["panel_soft"],
            fg=COLORS["pink_soft"],
            font=self._retro_font(10, "bold"),
        )
        self.stage_rule.pack(fill="x")

        image_area = tk.Frame(self.stage, bg=COLORS["panel_soft"])
        image_area.pack(fill="both", expand=True, padx=8, pady=(0, 2))

        self.hero_prev = tk.Button(
            image_area,
            text="❮",
            command=lambda: self.move(-1),
            bg=COLORS["panel_soft"],
            fg=COLORS["white"],
            activebackground=COLORS["panel_selected"],
            activeforeground=COLORS["white"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            font=self._retro_font(22, "bold"),
            width=2,
        )
        self.hero_prev.pack(side="left", fill="y")

        center = tk.Frame(image_area, bg=COLORS["panel_soft"])
        center.pack(side="left", fill="both", expand=True)

        self.image_label = tk.Label(
            center,
            bg=COLORS["panel_soft"],
            fg=COLORS["muted"],
            text="SEM IMAGEM\nDE REFERÊNCIA",
            justify="center",
            compound="center",
            font=self._retro_font(10, "bold"),
        )
        self.image_label.pack(fill="both", expand=True)

        self.pedestal = tk.Canvas(
            center,
            height=46,
            bg=COLORS["panel_soft"],
            highlightthickness=0,
            bd=0,
        )
        self.pedestal.pack(fill="x", padx=22)
        self.pedestal.bind("<Configure>", self._draw_pedestal)

        image_nav = tk.Frame(center, bg=COLORS["panel_soft"])
        image_nav.pack(fill="x", pady=(0, 5))
        self.image_prev = tk.Button(
            image_nav,
            text="‹ IMG",
            command=lambda: self.move_image(-1),
            bg=COLORS["panel"],
            fg=COLORS["cyan_soft"],
            activebackground=COLORS["panel_selected"],
            relief=tk.FLAT,
            bd=0,
            font=self._retro_font(7, "bold"),
            padx=7,
            pady=3,
        )
        self.image_prev.pack(side="left")
        self.image_counter = tk.Label(
            image_nav,
            text="0 / 0",
            bg=COLORS["panel_soft"],
            fg=COLORS["muted"],
            font=self._retro_font(7, "bold"),
        )
        self.image_counter.pack(side="left", expand=True)
        self.image_next = tk.Button(
            image_nav,
            text="IMG ›",
            command=lambda: self.move_image(1),
            bg=COLORS["panel"],
            fg=COLORS["cyan_soft"],
            activebackground=COLORS["panel_selected"],
            relief=tk.FLAT,
            bd=0,
            font=self._retro_font(7, "bold"),
            padx=7,
            pady=3,
        )
        self.image_next.pack(side="right")

        self.hero_next = tk.Button(
            image_area,
            text="❯",
            command=lambda: self.move(1),
            bg=COLORS["panel_soft"],
            fg=COLORS["white"],
            activebackground=COLORS["panel_selected"],
            activeforeground=COLORS["white"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            font=self._retro_font(22, "bold"),
            width=2,
        )
        self.hero_next.pack(side="right", fill="y")

    def _build_summary(self, parent):
        self.summary = tk.Frame(parent, bg=COLORS["bg"], height=118)
        self.summary.pack(fill="x", padx=8, pady=(0, 8))
        self.summary.pack_propagate(False)

        self.summary_labels = {}
        for column, (key, title) in enumerate(
            (
                ("powers", "⚡ PODERES"),
                ("equipment", "▣ EQUIPAMENTO"),
                ("affiliations", "☆ AFILIAÇÕES"),
                ("stats", "ESTATÍSTICAS"),
            )
        ):
            card = tk.Frame(
                self.summary,
                bg=COLORS["panel"],
                highlightbackground=COLORS["pink_soft"],
                highlightthickness=1,
            )
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 4, 0))
            tk.Label(
                card,
                text=title,
                bg=COLORS["panel"],
                fg=COLORS["cyan_soft"],
                font=self._retro_font(8, "bold"),
                pady=5,
            ).pack(fill="x")
            label = tk.Label(
                card,
                text="—",
                bg=COLORS["panel"],
                fg=COLORS["white"],
                font=self._retro_font(7),
                justify="left",
                anchor="nw",
                wraplength=185,
                padx=8,
                pady=2,
            )
            label.pack(fill="both", expand=True)
            self.summary_labels[key] = label

        for column in range(4):
            self.summary.grid_columnconfigure(column, weight=1, uniform="summary")
        self.summary.grid_rowconfigure(0, weight=1)

    def _build_footer(self):
        footer = tk.Frame(self, bg=COLORS["bg_deep"], height=52)
        footer.pack(fill="x", padx=14, pady=(0, 10))
        footer.pack_propagate(False)

        tk.Button(
            footer,
            text="← VOLTAR AO HUB",
            command=self.on_home or (lambda: None),
            bg=COLORS["panel_dark"],
            fg=COLORS["white"],
            activebackground=COLORS["panel_selected"],
            activeforeground=COLORS["white"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            font=self._retro_font(8, "bold"),
            padx=12,
            pady=7,
        ).pack(side="left", padx=6, pady=7)

        tk.Button(
            footer,
            text="▣ ABRIR FICHA COMPLETA",
            command=self.open_full_profile,
            bg=COLORS["panel_dark"],
            fg=COLORS["white"],
            activebackground=COLORS["panel_selected"],
            activeforeground=COLORS["white"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            font=self._retro_font(8, "bold"),
            padx=12,
            pady=7,
        ).pack(side="right", padx=6, pady=7)

        tabs = tk.Frame(footer, bg=COLORS["bg_deep"])
        tabs.pack(fill="x", expand=True, padx=6)
        self.tab_buttons = {}
        for key, label in TAB_LABELS.items():
            button = tk.Button(
                tabs,
                text=label,
                command=lambda value=key: self.set_tab(value),
                bg=COLORS["panel"],
                fg=COLORS["white"],
                activebackground=COLORS["panel_selected"],
                activeforeground=COLORS["white"],
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                font=self._retro_font(7, "bold"),
                padx=8,
                pady=7,
            )
            button.pack(side="left", fill="x", expand=True, padx=1, pady=7)
            self.tab_buttons[key] = button
        self._refresh_tab_buttons()

    def _schedule_refresh(self, _event=None):
        if self._search_job is not None:
            try:
                self.after_cancel(self._search_job)
            except tk.TclError:
                pass
        self._search_job = self.after(140, lambda: self.refresh(reset_page=True))

    def _toggle_filters(self):
        self._filter_open = not self._filter_open
        if self._filter_open:
            self.filter_popup.place(
                in_=self.sidebar,
                x=8,
                y=72,
                relwidth=0.94,
                height=302,
            )
            self.filter_popup.lift()
        else:
            self.filter_popup.place_forget()

    def _clear_filters(self):
        self.search_var.set("")
        self.universe_var.set("Todos")
        for variable in self.filter_vars.values():
            variable.set("")
        self.refresh(reset_page=True)

    def refresh(self, reset_page=False):
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
        try:
            items = self.knowledge.search_entities(
                query,
                filters=filters,
                limit=5000,
            )
        except Exception as exc:
            log.exception("Falha ao pesquisar catálogo de heróis: %s", exc)
            items = []

        self.carousel.set_items(items, keep_id=previous_id)
        if reset_page:
            self._page = 0
        else:
            self._sync_page_to_selection()
        self._refresh_catalog_header()
        self._render_roster()
        self.render()

    def _catalog_total(self) -> int:
        try:
            status = self.knowledge.status()
            return int(status.get("heroes") or 0)
        except Exception:
            return len(self.carousel.items)

    def _refresh_catalog_header(self):
        total = self._catalog_total()
        filtered = len(self.carousel.items)
        query_active = bool(
            self.search_var.get().strip()
            or self.universe_var.get() != "Todos"
            or any(value.get().strip() for value in self.filter_vars.values())
        )
        count_line = f"{total:,} HERÓIS REGISTRADOS".replace(",", ".")
        if query_active:
            count_line += f"\n{filtered:,} NO FILTRO ATUAL".replace(",", ".")
        self.header_count.config(text=f"CATÁLOGO DE HERÓIS\n{count_line}")

        snapshot = int(self._coverage.get("snapshot_records") or 0)
        official = int(self._coverage.get("official_site_reported_results") or 0)
        gap = int(self._coverage.get("verified_snapshot_results_gap") or 0)
        if snapshot and official:
            coverage = (
                f"MARVEL • {snapshot:,}/{official:,} perfis observados"
                f" • lacuna {gap:,} • catálogo parcial"
            ).replace(",", ".")
        elif snapshot:
            coverage = (
                f"MARVEL • {snapshot:,} registros verificados • catálogo parcial"
            ).replace(",", ".")
        else:
            coverage = "Cobertura Marvel ainda não certificada."
        self.coverage_label.config(text=coverage)

    def _page_count(self) -> int:
        if not self.carousel.items:
            return 0
        return math.ceil(len(self.carousel.items) / ROSTER_PAGE_SIZE)

    def _sync_page_to_selection(self):
        if self.carousel.items:
            self._page = self.carousel.index // ROSTER_PAGE_SIZE
        else:
            self._page = 0

    def change_page(self, step):
        pages = self._page_count()
        if pages <= 0:
            return
        self._page = (self._page + int(step)) % pages
        self._render_roster()

    def _render_roster(self):
        for child in self.roster.winfo_children():
            child.destroy()
        self._roster_buttons.clear()

        pages = self._page_count()
        if not pages:
            self.page_label.config(text="0 / 0")
            tk.Label(
                self.roster,
                text="NENHUM HERÓI\nENCONTRADO",
                bg=COLORS["panel_dark"],
                fg=COLORS["muted"],
                justify="center",
                font=self._retro_font(9, "bold"),
            ).pack(fill="both", expand=True, pady=40)
            return

        self._page %= pages
        start = self._page * ROSTER_PAGE_SIZE
        end = min(start + ROSTER_PAGE_SIZE, len(self.carousel.items))
        current_id = getattr(self.carousel.current, "id", None)

        for global_index in range(start, end):
            entity = self.carousel.items[global_index]
            selected = getattr(entity, "id", None) == current_id
            bg = COLORS["panel_selected"] if selected else COLORS["panel"]
            thumb = self._thumbnail_for(entity)
            subtitle = _field(
                getattr(entity, "universe", None)
                or getattr(entity, "publisher", None),
                "Universo não informado",
            )
            button = tk.Button(
                self.roster,
                text=f"{entity.name}\n{subtitle}",
                image=thumb or "",
                compound="left",
                anchor="w",
                justify="left",
                command=lambda index=global_index: self.select(index),
                bg=bg,
                fg=COLORS["white"],
                activebackground=COLORS["panel_selected"],
                activeforeground=COLORS["white"],
                relief=tk.FLAT,
                bd=0,
                highlightbackground=COLORS["cyan"] if selected else COLORS["panel_dark"],
                highlightthickness=1 if selected else 0,
                cursor="hand2",
                font=self._retro_font(8, "bold"),
                padx=7,
                pady=5,
            )
            if thumb is not None:
                button.image = thumb
            button.pack(fill="x", pady=(0, 3))
            self._roster_buttons.append(button)

        self.page_label.config(text=f"{self._page + 1} / {pages}")

    def _thumbnail_for(self, entity):
        refs = visual_references(entity)
        if not refs:
            return None
        path = Path(refs[0])
        try:
            stat = path.stat()
            cache_key = f"{entity.id}|{path}|{stat.st_mtime_ns}"
        except OSError:
            return None

        cached = self._thumb_cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            with Image.open(path) as source:
                image = source.convert("RGBA")
                image.thumbnail((44, 50), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
        except (OSError, ValueError, tk.TclError) as exc:
            log.debug("Miniatura indisponível (%s): %s", path, exc)
            return None

        self._thumb_cache[cache_key] = photo
        if len(self._thumb_cache) > 96:
            oldest = next(iter(self._thumb_cache))
            self._thumb_cache.pop(oldest, None)
        return photo

    def select(self, index: int):
        self.carousel.select(index)
        self._sync_page_to_selection()
        self._render_roster()
        self.render()

    def move(self, step):
        self.carousel.move(step)
        self._sync_page_to_selection()
        self._render_roster()
        self.render()

    def move_image(self, step):
        if not self._image_refs:
            return
        self._image_index = (self._image_index + int(step)) % len(self._image_refs)
        self._render_image_reference()

    def set_tab(self, tab):
        if tab not in TAB_LABELS:
            return
        self._active_tab = tab
        self._refresh_tab_buttons()
        self._render_details()

    def _refresh_tab_buttons(self):
        for key, button in getattr(self, "tab_buttons", {}).items():
            active = key == self._active_tab
            button.config(
                bg=COLORS["panel_selected"] if active else COLORS["panel"],
                fg=COLORS["cyan_soft"] if active else COLORS["white"],
            )

    def _apply_theme(self, entity):
        theme = theme_for_entity(entity)
        self.name_label.config(fg=theme.accent_secondary or COLORS["white"])
        self.stage_rule.config(fg=theme.accent or COLORS["pink_soft"])
        self.stage.config(highlightbackground=theme.accent or COLORS["pink_soft"])
        self.image_counter.config(fg=theme.accent_secondary or COLORS["muted"])

    def render(self):
        entity = self.carousel.current
        if entity is None:
            self._rendered_entity_id = None
            self._image_refs = []
            self.photo = None
            self.name_label.config(text="NENHUM PERSONAGEM ENCONTRADO")
            self.image_label.config(image="", text="SEM IMAGEM\nDE REFERÊNCIA")
            self.image_counter.config(text="0 / 0")
            self._render_details()
            self._render_summary(None)
            return

        self._apply_theme(entity)
        self.name_label.config(text=str(entity.name).upper())

        if self._rendered_entity_id != entity.id:
            self._rendered_entity_id = entity.id
            self._image_index = 0
            self._image_refs = visual_references(entity)
        self._render_image_reference()
        self._render_details()
        self._render_summary(entity)

        if self.on_selected:
            self.on_selected(entity)

    def _render_details(self):
        entity = self.carousel.current
        titles = {
            "info": "✦ DADOS DO PERSONAGEM ✦",
            "biography": "✦ BIOGRAFIA ✦",
            "relations": "✦ RELAÇÕES ✦",
            "history": "✦ HISTÓRIA ✦",
            "appearances": "✦ APARIÇÕES ✦",
        }
        self.data_title.config(text=titles.get(self._active_tab, titles["info"]))
        self._set_details(hero_tab_text(entity, self._active_tab))

    def _set_details(self, text):
        self.details.config(state=tk.NORMAL)
        self.details.delete("1.0", tk.END)
        for raw_line in str(text).splitlines():
            if ":" in raw_line and not raw_line.startswith(("http://", "https://")):
                label, value = raw_line.split(":", 1)
                self.details.insert(tk.END, label + ":", "label")
                self.details.insert(tk.END, value + "\n")
            else:
                self.details.insert(tk.END, raw_line + "\n")
        self.details.config(state=tk.DISABLED)

    def _render_summary(self, entity):
        if entity is None:
            for label in self.summary_labels.values():
                label.config(text="—")
            return

        powers = list(getattr(entity, "powers", []) or [])
        equipment = list(getattr(entity, "equipment", []) or [])
        affiliations = list(getattr(entity, "affiliations", []) or [])
        if not affiliations:
            affiliations = list(getattr(entity, "team", []) or [])

        self.summary_labels["powers"].config(
            text="\n".join(f"• {item}" for item in powers[:4]) or "—"
        )
        self.summary_labels["equipment"].config(
            text="\n".join(f"• {item}" for item in equipment[:4]) or "—"
        )
        self.summary_labels["affiliations"].config(
            text="\n".join(f"• {item}" for item in affiliations[:4]) or "—"
        )

        stats = []
        for label, aliases in STAT_KEYS:
            value = hero_statistic_value(entity, aliases)
            stats.append(f"{label:<12} {statistic_bar(value)}")
        self.summary_labels["stats"].config(text="\n".join(stats))

    def _render_image_reference(self):
        self.photo = None
        if not self._image_refs:
            self.image_label.config(image="", text="SEM IMAGEM\nDE REFERÊNCIA")
            self.image_counter.config(text="0 / 0")
            self.image_prev.config(state=tk.DISABLED)
            self.image_next.config(state=tk.DISABLED)
            return

        self._image_index %= len(self._image_refs)
        path = Path(self._image_refs[self._image_index])
        try:
            with Image.open(path) as source:
                image = source.convert("RGBA")
                image.thumbnail((390, 310), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=self.photo, text="")
        except (OSError, ValueError, tk.TclError) as exc:
            log.debug("Imagem de personagem indisponível (%s): %s", path, exc)
            self.image_label.config(image="", text="IMAGEM INDISPONÍVEL")

        enabled = tk.NORMAL if len(self._image_refs) > 1 else tk.DISABLED
        self.image_prev.config(state=enabled)
        self.image_next.config(state=enabled)
        self.image_counter.config(
            text=f"{self._image_index + 1} / {len(self._image_refs)}"
        )

    def _draw_pedestal(self, _event=None):
        canvas = self.pedestal
        canvas.delete("all")
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)
        cx = width / 2
        canvas.create_oval(
            cx - width * 0.34, height * 0.18,
            cx + width * 0.34, height * 0.82,
            outline=COLORS["cyan"], width=2,
        )
        canvas.create_oval(
            cx - width * 0.27, height * 0.28,
            cx + width * 0.27, height * 0.72,
            outline=COLORS["pink_soft"], width=1,
        )

    def open_full_profile(self):
        entity = self.carousel.current
        if entity is None:
            return

        top = tk.Toplevel(self.winfo_toplevel())
        top.title(f"STAR • Ficha completa • {entity.name}")
        top.geometry("760x620")
        top.minsize(560, 420)
        top.configure(bg=COLORS["bg_deep"])
        top.transient(self.winfo_toplevel())

        tk.Label(
            top,
            text=str(entity.name).upper(),
            bg=COLORS["bg_deep"],
            fg=COLORS["cyan"],
            font=self._retro_font(16, "bold"),
            pady=12,
        ).pack(fill="x")

        body = tk.Frame(top, bg=COLORS["panel_dark"])
        body.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        scrollbar = tk.Scrollbar(body)
        scrollbar.pack(side="right", fill="y")
        text = tk.Text(
            body,
            bg=COLORS["panel_dark"],
            fg=COLORS["white"],
            insertbackground=COLORS["white"],
            relief=tk.FLAT,
            wrap="word",
            font=self._retro_font(9),
            padx=14,
            pady=12,
            yscrollcommand=scrollbar.set,
        )
        text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text.yview)
        text.insert("1.0", full_profile_text(entity))
        text.config(state=tk.DISABLED)

        tk.Button(
            top,
            text="FECHAR",
            command=top.destroy,
            bg=COLORS["panel_selected"],
            fg=COLORS["white"],
            activebackground=COLORS["cyan"],
            activeforeground=COLORS["bg_deep"],
            relief=tk.FLAT,
            bd=0,
            font=self._retro_font(9, "bold"),
            padx=18,
            pady=7,
        ).pack(pady=(0, 12))
