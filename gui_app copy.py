import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from typing import Any

import customtkinter as ctk

# --- Hidden Imports for PyInstaller (ensure they are bundled) ---
try:
    import win32crypt
    import Cryptodome
    import requests
except ImportError:
    pass

# ── Apply theme before any widget creation ────────────────────────────────────
from gui.theme import COLORS, FONTS, PAD, make_label

from gui.views.audit           import AuditView
from gui.views.results         import ResultsView
from gui.views.reports         import ReportsView
from gui.views.post_audit      import PostAuditView
from gui.views.maintenance     import MaintenanceView
from gui.views.builder         import BuilderView
from gui.views.exit            import ExitView


class App(ctk.CTk):
    """Root application window with sidebar navigation."""

    NAV_ITEMS = [
        ("🔍", "Auditoría",     "audit"),
        ("📊", "Resultados",    "results"),
        ("📁", "Reportes",      "reports"),
        ("📤", "Exfiltración",    "post_audit"),
        ("🔧", "Mantenimiento", "maintenance"),
        ("🔨", "Builder",       "builder"),
        ("🚪", "Salir",         "exit"),
    ]

    def __init__(self):
        super().__init__()

        # Window Config
        self.title("ChromiumSpecter — Tactical Auditor Suite")
        self.after(0, lambda: self.state('zoomed')) # Full screen on start
        self.minsize(1100, 750)
        
        # Grid layout (1x2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._current_view_key: str | None = None
        self._audit_dir = Path(".audit")
        
        # Initialize environment (Passive mode - no log file locking on start)
        from main import _setup_environment
        _setup_environment(str(self._audit_dir), start_logging=False)

        self._build_sidebar()
        self._build_main_container()
        
        # Initial view
        self.select_view("audit")

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_sidebar(self):
        self._sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLORS["bg_sidebar"])
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_rowconfigure(len(self.NAV_ITEMS) + 2, weight=1)

        # Header / Logo
        logo_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=30)
        
        make_label(logo_frame, "ChromiumSpecter", style="heading", color=COLORS["accent"]).pack(anchor="w")
        make_label(logo_frame, "TACTICAL AUDITOR SUITE", style="small", color=COLORS["text_secondary"]).pack(anchor="w")

        # Nav Buttons
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        
        for icon, label, key in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                self._sidebar,
                text=f"  {icon}  {label}",
                anchor="w",
                height=45,
                corner_radius=8,
                fg_color="transparent",
                text_color=COLORS["text_secondary"],
                font=FONTS["body"],
                hover_color=COLORS["bg_card_hover"],
                command=lambda k=key: self.select_view(k)
            )
            btn.pack(fill="x", padx=15, pady=4)
            self._nav_buttons[key] = btn

        # Footer info
        version_lbl = make_label(self._sidebar, "v2.1.0-PRO", style="tiny", color=COLORS["text_muted"])
        version_lbl.pack(side="bottom", pady=20)

    def _build_main_container(self):
        self._views_container = ctk.CTkFrame(self, fg_color=COLORS["bg_root"], corner_radius=0)
        self._views_container.grid(row=0, column=1, sticky="nsew")
        
        # Initialize views
        self._views: dict[str, ctk.CTkFrame] = {
            "audit":           AuditView(self._views_container, None),
            "results":         ResultsView(self._views_container),
            "reports":         ReportsView(self._views_container),
            "post_audit":      PostAuditView(self._views_container),
            "maintenance":     MaintenanceView(self._views_container),
            "builder":         BuilderView(self._views_container),
            "exit":            ExitView(self._views_container),
        }

        # Inject real engine into AuditView
        from main import ChromiumDecryptor
        self._engine = ChromiumDecryptor()
        self._views["audit"]._engine = self._engine
        
        # Connect signals
        self._views["audit"].set_results_callback(self._on_audit_complete)

        # Sync audit directory across views
        for view in self._views.values():
            if hasattr(view, "set_audit_dir"):
                view.set_audit_dir(self._audit_dir)

        # Start all views hidden
        for view in self._views.values():
            view.pack_forget()

    # ── View Management ───────────────────────────────────────────────────────

    def select_view(self, key: str):
        if key == self._current_view_key:
            return
        
        # Update sidebar
        if self._current_view_key:
            self._nav_buttons[self._current_view_key].configure(
                fg_color="transparent", 
                text_color=COLORS["text_secondary"]
            )
            self._views[self._current_view_key].pack_forget()

        btn = self._nav_buttons[key]
        btn.configure(fg_color=COLORS["accent_dim"], text_color=COLORS["accent"])
        
        self._views[key].pack(fill="both", expand=True)
        self._current_view_key = key

    # ── Logic Handlers ────────────────────────────────────────────────────────

    def _on_audit_complete(self, results, html_path, csv_path, auto_exfiltrate=False):
        """Bridge results from Audit tab to Results tab."""
        self._views["results"].load_results(results)
        # Notify reports tab to refresh
        self._views["reports"].set_audit_dir(self._audit_dir)
        # Inject paths into Post-Audit tab
        self._views["post_audit"].set_report_paths(html_path, csv_path)
        
        if auto_exfiltrate:
            self._views["post_audit"].trigger_auto_exfiltrate()


if __name__ == "__main__":
    # Si se pasan argumentos (ej. desde el Builder interno), actuar como proxy de build.py
    if len(sys.argv) > 1 and sys.argv[1].endswith("build.py"):
        import build
        # Quitar el script proxy de los args para que argparse no se rompa
        sys.argv.pop(1)
        build.main()
    else:
        app = App()
        app.mainloop()
