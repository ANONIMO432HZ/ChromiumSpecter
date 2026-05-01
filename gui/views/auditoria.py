"""
Tab: Auditoría
──────────────
Controls to launch the Chrome credential audit:
  • Browser filter selector
  • Delay, output dir, stealth toggle
  • Run button with live log output
  • Stats bar (found / filtered / skipped)
"""

import threading
import tkinter as tk
from pathlib import Path
from datetime import datetime
import customtkinter as ctk

from gui.theme import (
    COLORS, FONTS, PAD,
    make_card, make_label, make_button, make_entry,
    make_section_header, make_badge, make_stat_card,
)


class AuditoriaView(ctk.CTkFrame):
    """Main audit control panel."""

    BROWSERS = ["Todos", "Chrome", "Edge", "Brave", "Vivaldi", "Opera", "Opera GX"]

    def __init__(self, parent, engine_ref):
        super().__init__(parent, fg_color="transparent")
        self._engine = engine_ref           # ChromiumDecryptor instance
        self._running = False
        self._results = []
        self._stats = {"total": 0, "filtered": 0, "browsers": 0}
        self._on_results_cb = None          # injected by App after construction

        self._build_ui()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_results_callback(self, cb):
        """Called with (results, html_path, csv_path) after a successful audit."""
        self._on_results_cb = cb

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Top stats row ─────────────────────────────────────────────────────
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=PAD["lg"], pady=(PAD["lg"], PAD["sm"]))

        self._stat_total   = make_stat_card(stats_row, "Credenciales", "0", "🔑", "accent")
        self._stat_filtered= make_stat_card(stats_row, "Filtradas",    "0", "🔕", "warning")
        self._stat_browser = make_stat_card(stats_row, "Navegadores",  "0", "🌐", "info")
        self._stat_time    = make_stat_card(stats_row, "Duración",     "—", "⏱️", "success")

        for card in (self._stat_total, self._stat_filtered, self._stat_browser, self._stat_time):
            card.pack(side="left", padx=PAD["sm"], expand=True, fill="x")

        # ── Config card ───────────────────────────────────────────────────────
        make_section_header(self, "Configuración de Auditoría", "⚙️")
        cfg_card = make_card(self)
        cfg_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["md"]))

        cfg_inner = ctk.CTkFrame(cfg_card, fg_color="transparent")
        cfg_inner.pack(fill="x", padx=PAD["md"], pady=PAD["md"])

        # Row 1: Browser + Output dir
        r1 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        r1.pack(fill="x", pady=(0, PAD["sm"]))

        make_label(r1, "Navegador:", style="small", color=COLORS["text_secondary"]).pack(side="left", padx=(0, PAD["sm"]))
        self._browser_var = ctk.StringVar(value="Todos")
        browser_menu = ctk.CTkOptionMenu(
            r1,
            values=self.BROWSERS,
            variable=self._browser_var,
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent_dim"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"],
            font=FONTS["body"],
            text_color=COLORS["text_primary"],
            width=160,
        )
        browser_menu.pack(side="left", padx=(0, PAD["lg"]))

        make_label(r1, "Directorio salida:", style="small", color=COLORS["text_secondary"]).pack(side="left", padx=(0, PAD["sm"]))
        self._outdir_var = ctk.StringVar(value=".audit")
        outdir_entry = make_entry(r1, placeholder=".audit", width=200)
        outdir_entry.configure(textvariable=self._outdir_var)
        outdir_entry.pack(side="left")

        # Row 2: Delay + toggles
        r2 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        r2.pack(fill="x", pady=(0, PAD["sm"]))

        make_label(r2, "Delay (seg):", style="small", color=COLORS["text_secondary"]).pack(side="left", padx=(0, PAD["sm"]))
        self._delay_var = ctk.StringVar(value="0")
        delay_entry = make_entry(r2, placeholder="0", width=70)
        delay_entry.configure(textvariable=self._delay_var)
        delay_entry.pack(side="left", padx=(0, PAD["lg"]))

        self._stealth_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            r2, text="Modo Stealth", variable=self._stealth_var,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=FONTS["body"], text_color=COLORS["text_primary"],
        ).pack(side="left", padx=(0, PAD["lg"]))

        self._skip_html_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            r2, text="Sin HTML", variable=self._skip_html_var,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=FONTS["body"], text_color=COLORS["text_primary"],
        ).pack(side="left", padx=(0, PAD["lg"]))

        self._skip_csv_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            r2, text="Sin CSV", variable=self._skip_csv_var,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=FONTS["body"], text_color=COLORS["text_primary"],
        ).pack(side="left")

        # Row 3: Action buttons
        r3 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        r3.pack(fill="x", pady=(PAD["sm"], 0))

        self._run_btn = make_button(r3, "▶  Iniciar Auditoría", command=self._start_audit, style="primary", width=180)
        self._run_btn.pack(side="left", padx=(0, PAD["sm"]))

        self._stop_btn = make_button(r3, "⏹  Detener", command=self._stop_audit, style="danger", width=110)
        self._stop_btn.pack(side="left", padx=(0, PAD["sm"]))
        self._stop_btn.configure(state="disabled")

        make_button(r3, "↺  Reset config", command=self._reset_config, style="secondary", width=130).pack(side="left", padx=(0, PAD["sm"]))
        make_button(r3, "🗑  Limpiar log",  command=self._clear_log,   style="secondary", width=120).pack(side="left", padx=(0, PAD["sm"]))
        make_button(r3, "📋  Copiar log",   command=self._copy_log,    style="secondary", width=115).pack(side="left")

        self._status_badge = make_badge(r3, "INACTIVO", "text_muted")
        self._status_badge.pack(side="right", padx=PAD["sm"])

        # ── Log output ────────────────────────────────────────────────────────
        make_section_header(self, "Log de Ejecución", "📋")
        log_card = make_card(self)
        log_card.pack(fill="both", expand=True, padx=PAD["lg"], pady=(0, PAD["lg"]))

        self._log = ctk.CTkTextbox(
            log_card,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            font=FONTS["code"],
            corner_radius=8,
            border_width=0,
            wrap="word",
            state="disabled",
        )
        self._log.pack(fill="both", expand=True, padx=PAD["sm"], pady=PAD["sm"])

        # Tag colours
        self._log._textbox.tag_configure("INFO",    foreground=COLORS["text_primary"])
        self._log._textbox.tag_configure("OK",      foreground=COLORS["success"])
        self._log._textbox.tag_configure("WARN",    foreground=COLORS["warning"])
        self._log._textbox.tag_configure("ERR",     foreground=COLORS["danger"])
        self._log._textbox.tag_configure("ACCENT",  foreground=COLORS["accent"])
        self._log._textbox.tag_configure("MUTED",   foreground=COLORS["text_muted"])

        self._log_line("INFO", "  Chromium Auditor Dashboard — listo para operar\n")
        self._log_line("MUTED", "  Configure los parámetros y presione 'Iniciar Auditoría'.\n")

    # ── Stat helpers ──────────────────────────────────────────────────────────

    def _refresh_stats(self):
        """Pull value labels from stat cards and update."""
        for card, val_str in (
            (self._stat_total,   str(self._stats["total"])),
            (self._stat_filtered,str(self._stats["filtered"])),
            (self._stat_browser, str(self._stats["browsers"])),
        ):
            # The 3rd child of each card is the value label (icon, value, label)
            card.winfo_children()[1].configure(text=val_str)

    def _set_duration(self, seconds: float):
        self._stat_time.winfo_children()[1].configure(text=f"{seconds:.1f}s")

    # ── Log helpers ───────────────────────────────────────────────────────────

    def _log_line(self, tag: str, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.configure(state="normal")
        self._log._textbox.insert("end", f"[{ts}] ", "MUTED")
        self._log._textbox.insert("end", msg + "\n", tag)
        self._log._textbox.see("end")
        self._log.configure(state="disabled")

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("0.0", "end")
        self._log.configure(state="disabled")

    def _copy_log(self):
        self._log.configure(state="normal")
        content = self._log.get("0.0", "end")
        self._log.configure(state="disabled")
        self.clipboard_clear()
        self.clipboard_append(content)

    def _reset_config(self):
        self._browser_var.set("Todos")
        self._outdir_var.set(".audit")
        self._delay_var.set("0")
        self._stealth_var.set(False)
        self._skip_html_var.set(False)
        self._skip_csv_var.set(False)
    # ── Audit execution ───────────────────────────────────────────────────────

    def _start_audit(self):
        if self._running:
            return
        self._running = True
        self._run_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._status_badge.configure(text="  EJECUTANDO  ", fg_color=COLORS["accent_dim"], text_color=COLORS["accent"])
        self._clear_log()
        self._log_line("ACCENT", "Iniciando auditoría de credenciales Chromium…")
        threading.Thread(target=self._audit_worker, daemon=True).start()

    def _stop_audit(self):
        self._running = False
        self._log_line("WARN", "Auditoría cancelada por el usuario.")
        self._finish_audit()

    def _finish_audit(self):
        self._running = False
        self._run_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")

    def _audit_worker(self):
        import time
        import sys
        # Respect delay
        try:
            delay = int(self._delay_var.get() or 0)
        except ValueError:
            delay = 0

        if delay > 0:
            self._log_line("INFO", f"Esperando {delay}s antes de iniciar…")
            for i in range(delay):
                if not self._running:
                    self._after_call(self._finish_audit)
                    return
                time.sleep(1)

        # Setup output dir
        from main import _setup_environment, ChromiumDecryptor
        out_dir = _setup_environment(self._outdir_var.get() or ".audit")

        browser_filter = None if self._browser_var.get() == "Todos" else self._browser_var.get()
        self._log_line("INFO", f"Navegador: {self._browser_var.get()} | Directorio: {out_dir}")

        t0 = time.time()
        try:
            decryptor = ChromiumDecryptor()
            self._log_line("INFO", "Buscando perfiles…")

            targets = decryptor.find_targets()
            if browser_filter:
                targets = [t for t in targets if browser_filter.lower() in t["name"].lower()]

            if not targets:
                self._log_line("WARN", "No se encontraron perfiles de navegador instalados o accesibles.")
                self._after_call(self._finish_audit)
                return

            browser_names = list({t["name"] for t in targets})
            self._stats["browsers"] = len(browser_names)
            self._log_line("OK", f"Perfiles encontrados: {', '.join(browser_names)}")

            results, hp, cp = decryptor.audit(
                out_dir,
                skip_html=self._skip_html_var.get(),
                skip_csv=self._skip_csv_var.get(),
                browser_filter=browser_filter,
            )

            elapsed = time.time() - t0

            if results is None:
                self._log_line("WARN", "No se encontraron credenciales guardadas.")
                self._stats["total"] = 0
                self._stats["filtered"] = 0
            else:
                valid   = [r for r in results if r[2].startswith(("http://", "https://"))]
                filtered= [r for r in results if not r[2].startswith(("http://", "https://"))]
                self._stats["total"]    = len(valid)
                self._stats["filtered"] = len(filtered)
                self._log_line("OK", f"✓ Credenciales válidas: {len(valid)}")
                self._log_line("INFO", f"  Filtradas (URL inválida): {len(filtered)}")
                if hp:
                    self._log_line("OK", f"  Reporte HTML → {hp}")
                if cp:
                    self._log_line("OK", f"  Reporte CSV  → {cp}")

                # Notify other tabs via callback
                if self._on_results_cb and results:
                    self._after_call(lambda: self._on_results_cb(results, hp, cp))

            self._after_call(lambda: self._set_duration(elapsed))
            self._after_call(self._refresh_stats)
            self._log_line("ACCENT", f"Auditoría completada en {elapsed:.2f}s")

        except Exception as exc:
            self._log_line("ERR", f"Error inesperado: {exc}")

        finally:
            self._after_call(self._finish_audit)
            badge_color = "success" if self._stats["total"] else "warning"
            badge_txt   = f"  {self._stats['total']} creds  " if self._stats["total"] else "  SIN DATOS  "
            self._after_call(
                lambda: self._status_badge.configure(
                    text=badge_txt,
                    fg_color=COLORS[f"{badge_color}_dim"],
                    text_color=COLORS[badge_color],
                )
            )

    def _after_call(self, fn):
        """Schedule fn on the main thread."""
        self.after(0, fn)
