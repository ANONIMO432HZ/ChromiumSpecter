"""
Tab: Resultados
───────────────
Displays the credential table from the last audit run.
Features:
  • Searchable / filterable table (browser, URL, user)
  • Inline password reveal toggle
  • Row count badge
  • Copy-to-clipboard on row click
  • Export to clipboard (JSON)
"""

import tkinter as tk
import json
import customtkinter as ctk

from gui.theme import (
    COLORS, FONTS, PAD,
    make_card, make_label, make_button, make_entry,
    make_section_header, make_badge,
)


class ResultadosView(ctk.CTkFrame):
    """Credential results table with search and reveal."""

    COLS = ("Navegador", "Perfil", "URL", "Usuario", "Contraseña")
    COL_WIDTHS = (100, 90, 300, 180, 180)

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._all_rows: list[list] = []
        self._shown_rows: list[list] = []
        self._reveal = False
        self._build_ui()

    # ── Public API ────────────────────────────────────────────────────────────

    def load_results(self, results: list):
        """Called by the App with raw audit result rows."""
        self._all_rows = list(results) if results else []
        self._apply_filter()
        self._count_badge.configure(text=f"  {len(self._all_rows)} total  ")

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = make_card(self)
        toolbar.pack(fill="x", padx=PAD["lg"], pady=(PAD["lg"], PAD["sm"]))

        tb = ctk.CTkFrame(toolbar, fg_color="transparent")
        tb.pack(fill="x", padx=PAD["md"], pady=PAD["sm"])

        make_label(tb, "🔍", style="subtitle").pack(side="left", padx=(0, PAD["sm"]))
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        search = make_entry(tb, placeholder="Buscar por URL, usuario, navegador…", width=320)
        search.configure(textvariable=self._search_var)
        search.pack(side="left", padx=(0, PAD["lg"]))

        make_label(tb, "Navegador:", style="small", color=COLORS["text_secondary"]).pack(side="left", padx=(0, PAD["sm"]))
        self._filter_browser = ctk.StringVar(value="Todos")
        ctk.CTkOptionMenu(
            tb,
            values=["Todos", "Chrome", "Edge", "Brave", "Vivaldi", "Opera", "Opera GX"],
            variable=self._filter_browser,
            command=lambda _: self._apply_filter(),
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent_dim"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"],
            font=FONTS["small"],
            text_color=COLORS["text_primary"],
            width=140,
        ).pack(side="left", padx=(0, PAD["lg"]))

        # Reveal toggle
        self._reveal_btn = make_button(tb, "👁  Mostrar", command=self._toggle_reveal, style="secondary", width=110)
        self._reveal_btn.pack(side="left", padx=(0, PAD["sm"]))

        make_button(tb, "📋  Copiar JSON", command=self._copy_json, style="secondary", width=130).pack(side="left", padx=(0, PAD["sm"]))
        make_button(tb, "🗑  Limpiar",      command=self._clear_results, style="danger",    width=100).pack(side="left")

        self._count_badge = make_badge(tb, "0 total", "text_muted")
        self._count_badge.pack(side="right", padx=PAD["sm"])

        # ── Table ────────────────────────────────────────────────────────────
        make_section_header(self, "Credenciales Encontradas", "🔑")

        table_card = make_card(self)
        table_card.pack(fill="both", expand=True, padx=PAD["lg"], pady=(0, PAD["lg"]))

        # Outer frame for canvas + scrollbars
        frame = ctk.CTkFrame(table_card, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=PAD["sm"], pady=PAD["sm"])

        # Header row (fake)
        hdr = ctk.CTkFrame(frame, fg_color=COLORS["accent_dim"], corner_radius=6)
        hdr.pack(fill="x", pady=(0, 2))
        for col, width in zip(self.COLS, self.COL_WIDTHS):
            ctk.CTkLabel(
                hdr, text=col, font=FONTS["heading"],
                text_color=COLORS["accent"], width=width, anchor="w",
            ).pack(side="left", padx=PAD["sm"], pady=PAD["sm"])

        # Scrollable body
        self._body = ctk.CTkScrollableFrame(
            frame,
            fg_color=COLORS["bg_input"],
            corner_radius=6,
            scrollbar_button_color=COLORS["accent_dim"],
            scrollbar_button_hover_color=COLORS["accent"],
        )
        self._body.pack(fill="both", expand=True)

        self._render_rows()

    # ── Data helpers ──────────────────────────────────────────────────────────

    def _apply_filter(self):
        query  = self._search_var.get().lower()
        browser= self._filter_browser.get()
        rows   = self._all_rows

        if browser != "Todos":
            rows = [r for r in rows if str(r[0]).lower() == browser.lower()]
        if query:
            rows = [r for r in rows if any(query in str(cell).lower() for cell in r)]

        self._shown_rows = rows
        self._render_rows()
        self._count_badge.configure(text=f"  {len(self._shown_rows)} / {len(self._all_rows)}  ")

    def _render_rows(self):
        for w in self._body.winfo_children():
            w.destroy()

        if not self._shown_rows:
            ctk.CTkLabel(
                self._body,
                text="Sin resultados — ejecutá una auditoría primero.",
                font=FONTS["body"],
                text_color=COLORS["text_muted"],
            ).pack(pady=PAD["xl"])
            return

        BROWSER_COLORS = {
            "chrome": "warning", "edge": "info", "brave": "danger",
            "opera": "danger", "opera gx": "danger", "vivaldi": "accent",
        }

        for i, row in enumerate(self._shown_rows):
            bg = COLORS["bg_card"] if i % 2 == 0 else COLORS["bg_panel"]
            r_frame = ctk.CTkFrame(self._body, fg_color=bg, corner_radius=4)
            r_frame.pack(fill="x", pady=1)
            r_frame.bind("<Button-1>", lambda e, r=row: self._copy_row(r))

            for j, (val, width) in enumerate(zip(row, self.COL_WIDTHS)):
                text = str(val) if val else "—"
                if j == 4 and not self._reveal:  # password col
                    text = "••••••••"
                if j == 0:  # browser badge col
                    color_key = BROWSER_COLORS.get(str(val).lower(), "accent")
                    lbl = make_badge(r_frame, text, color_key)
                else:
                    lbl = ctk.CTkLabel(
                        r_frame, text=text,
                        font=FONTS["mono_sm"] if j == 4 else FONTS["small"],
                        text_color=COLORS["success"] if (j == 4 and self._reveal) else COLORS["text_primary"],
                        width=width, anchor="w",
                    )
                lbl.pack(side="left", padx=PAD["sm"], pady=5)
                lbl.bind("<Button-1>", lambda e, r=row: self._copy_row(r))

    def _toggle_reveal(self):
        self._reveal = not self._reveal
        self._reveal_btn.configure(
            text="🙈  Ocultar" if self._reveal else "👁  Mostrar",
            fg_color=COLORS["success_dim"] if self._reveal else COLORS["bg_card"],
            text_color=COLORS["success"] if self._reveal else COLORS["text_secondary"],
        )
        self._render_rows()

    def _copy_row(self, row):
        text = "\t".join(str(c) for c in row)
        self.clipboard_clear()
        self.clipboard_append(text)

    def _copy_json(self):
        if not self._shown_rows:
            return
        keys = ["navegador", "perfil", "url", "usuario", "contraseña"]
        data = [dict(zip(keys, row)) for row in self._shown_rows]
        self.clipboard_clear()
        self.clipboard_append(json.dumps(data, ensure_ascii=False, indent=2))

    def _clear_results(self):
        self._all_rows = []
        self._shown_rows = []
        self._count_badge.configure(text="  0 total  ")
        self._render_rows()
