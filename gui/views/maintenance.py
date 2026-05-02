"""
Tab: Mantenimiento
──────────────────
System health panel:
  • Log viewer for pentest_audit.log
  • One-click cleanup of all audit files
  • Directory size info
  • Dependency checker (win32crypt, Cryptodome)
"""

import subprocess
import sys
import threading
import shutil
from pathlib import Path
import customtkinter as ctk

from gui.theme import (
    COLORS, FONTS, PAD,
    make_card, make_label, make_button,
    make_section_header, make_badge,
)


class MaintenanceView(ctk.CTkFrame):
    """System health and maintenance panel."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._audit_dir: Path | None = None
        self._build_ui()
        self.after(100, self._check_deps)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_audit_dir(self, path: Path):
        self._audit_dir = path
        self._refresh_dir_stats()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Dependency check ─────────────────────────────────────────────────
        make_section_header(self, "Estado de Dependencias", "🧩")
        dep_card = make_card(self)
        dep_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["md"]))

        dep_inner = ctk.CTkFrame(dep_card, fg_color="transparent")
        dep_inner.pack(fill="x", padx=PAD["md"], pady=PAD["md"])

        DEPS = [
            ("win32crypt",           "PyWin32",         "pywin32"),
            ("Cryptodome.Cipher",    "PyCryptodome",    "pycryptodomex"),
            ("requests",             "Requests",        "requests"),
            ("customtkinter",        "CustomTkinter",   "customtkinter"),
            ("PyInstaller",          "PyInstaller",     "pyinstaller"),
            ("pyarmor",              "PyArmor",         "pyarmor"),
        ]
        self._dep_badges: dict[str, ctk.CTkLabel] = {}
        self._missing_deps: list[str] = []

        grid = ctk.CTkFrame(dep_inner, fg_color="transparent")
        grid.pack(fill="x")

        for i, (mod, label, pkg) in enumerate(DEPS):
            row, col = divmod(i, 3) # 3 columns for better width usage
            f = ctk.CTkFrame(grid, fg_color="transparent")
            f.grid(row=row, column=col, sticky="w", padx=PAD["md"], pady=5)
            make_label(f, f"  {label}", style="body", color=COLORS["text_primary"], width=130, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
            badge = make_badge(f, "verificando…", "text_muted")
            badge.pack(side="left")
            self._dep_badges[mod] = badge

        self._dep_actions = ctk.CTkFrame(dep_inner, fg_color="transparent")
        self._dep_actions.pack(fill="x", pady=(PAD["md"], 0))

        make_button(self._dep_actions, "🔄 Re-verificar", command=self._check_deps, style="secondary", width=140).pack(side="left", padx=(0, PAD["sm"]))
        self._repair_btn = make_button(self._dep_actions, "🔧 Reparar Entorno", command=self._install_missing, style="primary", width=160)
        
        self._dep_log = None # Redundant, will use system log

        # ── Directory stats ───────────────────────────────────────────────────
        make_section_header(self, "Directorio de Auditoría", "📂")
        dir_card = make_card(self)
        dir_card.pack(fill="x", padx=PAD["lg"], pady=(0, PAD["md"]))

        dir_inner = ctk.CTkFrame(dir_card, fg_color="transparent")
        dir_inner.pack(fill="x", padx=PAD["md"], pady=PAD["md"])

        stats_row = ctk.CTkFrame(dir_inner, fg_color="transparent")
        stats_row.pack(fill="x")

        self._dir_path_lbl  = make_label(stats_row, "Ruta: —", style="small", color=COLORS["text_secondary"])
        self._dir_path_lbl.pack(side="left", padx=(0, PAD["lg"]))
        self._dir_size_badge = make_badge(stats_row, "0 KB", "info")
        self._dir_size_badge.pack(side="left", padx=(0, PAD["sm"]))
        self._dir_count_badge= make_badge(stats_row, "0 archivos", "accent")
        self._dir_count_badge.pack(side="left")

        btn_row = ctk.CTkFrame(dir_inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(PAD["sm"], 0))
        make_button(btn_row, "🔄 Actualizar", command=self._refresh_dir_stats, style="secondary", width=110).pack(side="left", padx=(0, PAD["sm"]))
        make_button(btn_row, "📦 Exportar",    command=self._export_audit,      style="action",    width=110).pack(side="left", padx=(0, PAD["sm"]))
        make_button(btn_row, "🗑 Limpiar audits", command=self._clean_audits, style="danger", width=130).pack(side="left", padx=(0, PAD["sm"]))
        make_button(btn_row, "🧹 Limpiar sistema", command=self._clean_system, style="danger", width=130).pack(side="left", padx=(0, PAD["sm"]))
        make_button(btn_row, "📂 Abrir carpeta", command=self._open_dir, style="secondary", width=125).pack(side="left")

        # ── Global Event Stream ───────────────────────────────────────────────
        make_section_header(self, "Consola de Eventos Globales", "📟")
        log_card = make_card(self)
        log_card.pack(fill="both", expand=True, padx=PAD["lg"], pady=(0, PAD["md"]))

        log_toolbar = ctk.CTkFrame(log_card, fg_color="transparent")
        log_toolbar.pack(fill="x", padx=PAD["sm"], pady=(PAD["sm"], 0))
        
        # Filter badges/buttons
        self._filter_var = ctk.StringVar(value="ALL")
        filters = [("TODOS", "ALL", "accent"), ("INFO", "INFO", "info"), ("AVISOS", "WARNING", "warning"), ("ERRORES", "ERROR", "danger")]
        
        filter_frame = ctk.CTkFrame(log_toolbar, fg_color="transparent")
        filter_frame.pack(side="left")
        
        for label, val, style in filters:
            btn = make_button(filter_frame, label, command=lambda v=val: self._set_filter(v), style="secondary", width=80, height=24)
            btn.pack(side="left", padx=2)

        make_button(log_toolbar, "🗑 Limpiar", command=self._clear_log_file, style="danger", width=100, height=24).pack(side="right", padx=PAD["sm"])
        make_button(log_toolbar, "📋 Copiar", command=self._copy_log, style="secondary", width=100, height=24).pack(side="right")
        
        self._log_box = ctk.CTkTextbox(
            log_card,
            fg_color=COLORS["bg_terminal"],
            text_color=COLORS["text_terminal"],
            font=FONTS["code"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            state="disabled",
            wrap="word"
        )
        self._log_box.pack(fill="both", expand=True, padx=PAD["sm"], pady=PAD["sm"])
        
        # Terminal tags
        self._log_box._textbox.tag_configure("INFO",    foreground=COLORS["info"])
        self._log_box._textbox.tag_configure("WARNING", foreground=COLORS["warning"])
        self._log_box._textbox.tag_configure("ERROR",   foreground=COLORS["danger"])
        self._log_box._textbox.tag_configure("SYSTEM",  foreground=COLORS["accent"])
        self._log_box._textbox.tag_configure("TIMESTAMP", foreground=COLORS["text_muted"])

        # Start auto-tail
        self._last_log_size = 0
        self._tail_active = True
        self._schedule_tail()

    # ── Dependency checker ────────────────────────────────────────────────────

    def _log_dep(self, msg: str, clear=False):
        # Solo escribir al log si tiene handlers activos (post-auditoría)
        import logging
        root = logging.getLogger()
        if root.handlers:
            from main import logger
            logger.info(f"[DEPS] {msg}")
            self.after(0, self._load_log)
        # El panel de dependencias siempre muestra en consola interna via badge

    def _check_deps(self):
        # Resetear estado antes de re-verificar para evitar acumulación
        self._missing_deps.clear()
        def _do():
            import importlib
            DEPS = [
                ("win32crypt",         "pywin32"),
                ("Cryptodome.Cipher",  "pycryptodomex"),
                ("requests",           "requests"),
                ("customtkinter",      "customtkinter"),
                ("PyInstaller",        "pyinstaller"),
                ("pyarmor",            "pyarmor"),
            ]
            for mod, pkg in DEPS:
                ok = False
                # Especial handling for CLI tools when frozen
                if pkg in ["pyinstaller", "pyarmor"]:
                    # Check if the command exists in PATH
                    if shutil.which(pkg) or shutil.which(f"{pkg}.exe"):
                        ok = True
                    else:
                        # Fallback to module check
                        try:
                            importlib.import_module(mod)
                            ok = True
                        except ImportError:
                            ok = False
                else:
                    # Standard module check
                    try:
                        importlib.import_module(mod)
                        ok = True
                    except ImportError:
                        ok = False
                
                if not ok:
                    self._missing_deps.append(pkg)
                
                badge = self._dep_badges.get(mod)
                if badge:
                    self.after(0, lambda b=badge, o=ok: b.configure(
                        text="  ✓ OK  " if o else "  ✗ FALTA  ",
                        fg_color=COLORS["success_dim"] if o else COLORS["danger_dim"],
                        text_color=COLORS["success"] if o else COLORS["danger"],
                    ))
            
            if self._missing_deps:
                self.after(0, lambda: self._repair_btn.pack(side="left"))
                self.after(0, lambda: self._log_dep(f"⚠ Faltan dependencias: {', '.join(self._missing_deps)}"))
            else:
                self.after(0, lambda: self._repair_btn.pack_forget())

        threading.Thread(target=_do, daemon=True).start()

    def _install_missing(self):
        if not self._missing_deps: return
        
        # Check if frozen (EXE mode)
        if getattr(sys, 'frozen', False):
            from tkinter import messagebox
            messagebox.showwarning("Modo Congelado", 
                "Estás ejecutando la versión compilada (.exe).\n\n"
                "Para instalar dependencias faltantes, debés hacerlo manualmente en tu sistema "
                "usando: pip install " + " ".join(self._missing_deps))
            return

        def _do():
            self._repair_btn.configure(state="disabled", text="🔨 Instalando…")
            self.after(0, lambda: self._log_dep("--- Iniciando reparación ---", clear=True))
            
            for pkg in self._missing_deps:
                self.after(0, lambda p=pkg: self._log_dep(f"[*] Instalando {p}..."))
                try:
                    proc = subprocess.Popen(
                        [sys.executable, "-m", "pip", "install", pkg],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    )
                    for line in proc.stdout:
                        line = line.strip()
                        if line: self.after(0, lambda l=line: self._log_dep(f"  {l}"))
                    proc.wait()
                    
                    if proc.returncode == 0:
                        self.after(0, lambda p=pkg: self._log_dep(f"✓ {p} instalado correctamente."))
                    else:
                        self.after(0, lambda p=pkg: self._log_dep(f"✗ Error al instalar {p}."))
                except Exception as e:
                    self.after(0, lambda ex=e: self._log_dep(f"⚠ Excepción: {ex}"))
            
            self.after(0, lambda: self._log_dep("--- Proceso finalizado ---"))
            self.after(0, self._check_deps)
            self.after(0, lambda: self._repair_btn.configure(state="normal", text="🔧 Reparar Entorno"))
            
        threading.Thread(target=_do, daemon=True).start()

    # ── Directory stats ───────────────────────────────────────────────────────

    def _refresh_dir_stats(self):
        d = self._audit_dir or Path(".audit")
        if not d.exists():
            self._dir_path_lbl.configure(text=f"Ruta: {d} (no existe)")
            return
        files = list(d.iterdir())
        total = sum(f.stat().st_size for f in files if f.is_file())
        size_str = f"{total/1024:.1f} KB" if total >= 1024 else f"{total} B"
        self._dir_path_lbl.configure(text=f"Ruta: {d.resolve()}")
        self._dir_size_badge.configure(text=f"  {size_str}  ")
        self._dir_count_badge.configure(text=f"  {len(files)} archivos  ")

    def _clean_audits(self):
        """Borrado físico forzado del directorio de auditoría."""
        from tkinter import messagebox
        import logging
        import shutil
        from main import _setup_environment

        if not messagebox.askyesno("Limpieza de Auditoría", "¿Confirmar borrado físico TOTAL de .audit?\n\nSe eliminarán logs, reportes y temporales."):
            return

        # 1. Detener procesos que bloquean archivos
        self._tail_active = False
        logging.shutdown()

        d = self._audit_dir or Path(".audit")
        success = False
        try:
            if d.exists():
                shutil.rmtree(d, ignore_errors=True)
                d.mkdir(parents=True, exist_ok=True)
                success = True
        except Exception as e:
            from main import logger
            logger.error(f"Error en limpieza forzada: {e}")

        # 2. Re-levantar el sistema en modo pasivo (sin bloquear el log)
        _setup_environment(str(d), start_logging=False)
        self._tail_active = True
        self._last_log_size = 0
        self._schedule_tail()
        
        self._refresh_dir_stats()
        if success:
            messagebox.showinfo("Éxito", "Directorio .audit saneado y re-inicializado.")
        else:
            messagebox.showwarning("Aviso", "Se limpiaron la mayoría de los archivos, pero algunos podrían seguir bloqueados por el sistema.")

    def _export_audit(self):
        """Empaqueta el directorio .audit en un ZIP en una ubicación personalizada."""
        import shutil, tempfile
        from tkinter import filedialog, messagebox
        from datetime import datetime
        from main import logger

        d = self._audit_dir or Path(".audit")
        if not d.exists() or not any(d.iterdir()):
            messagebox.showwarning("Exportar", "No hay datos de auditoría para exportar.")
            return

        # 1. Sugerir nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suggested_name = f"auditoria_chromium_{timestamp}.zip"
        
        save_path = filedialog.asksaveasfilename(
            title="Exportar Evidencia (ZIP)",
            initialfile=suggested_name,
            defaultextension=".zip",
            filetypes=[("Archivo ZIP", "*.zip")]
        )

        if not save_path:
            return

        def _do_export():
            try:
                self.after(0, lambda: logger.info(f"[SYSTEM] Iniciando exportación de evidencia a: {Path(save_path).name}"))
                
                # Crear ZIP en una ubicación temporal primero para evitar conflictos
                with tempfile.TemporaryDirectory() as tmp_dir:
                    zip_base = Path(tmp_dir) / "export"
                    shutil.make_archive(str(zip_base), 'zip', d)
                    
                    # Mover a la ubicación final
                    shutil.move(str(zip_base) + ".zip", save_path)

                self.after(0, lambda: logger.info(f"OK [SYSTEM] Exportación completada exitosamente: {save_path}"))
                self.after(0, lambda: messagebox.showinfo("Exportar", f"Evidencia exportada correctamente en:\n{save_path}"))
            except Exception as e:
                self.after(0, lambda: logger.error(f"ERR [SYSTEM] Error al exportar: {e}"))
                self.after(0, lambda: messagebox.showerror("Error", f"No se pudo exportar la auditoría:\n{e}"))

        threading.Thread(target=_do_export, daemon=True).start()

    def _clean_system(self):
        """Limpieza profunda de archivos temporales del sistema y compilación."""
        import shutil, os
        from tkinter import messagebox
        
        if not messagebox.askyesno("Limpiar Sistema", "¿Estás seguro de eliminar todos los archivos temporales (__pycache__, temp, spec, etc)?"):
            return

        # 0. Limpiar portapapeles
        try:
            self.winfo_toplevel().clipboard_clear()
        except: pass

        # 1. Carpetas temporales conocidas en el proyecto
        targets = [
            "build", "dist", "tmp", "temp", 
            ".pytest_cache", ".pyarmor", ".venv/target", 
            "gui/__pycache__", "gui/views/__pycache__"
        ]
        for t in targets:
            p = Path(t)
            if p.exists():
                try:
                    if p.is_dir(): shutil.rmtree(p)
                    else: p.unlink()
                except: pass

        # 2. Archivos .spec y .pyc huérfanos
        for ext in ["*.spec", "*.pyc", "*.pyo"]:
            for f in Path(".").rglob(ext):
                try: f.unlink()
                except: pass

        # 3. __pycache__ recursivo (fuerza bruta)
        for p in Path(".").rglob("__pycache__"):
            if p.is_dir():
                try: shutil.rmtree(p, ignore_errors=True)
                except: pass

        self._refresh_dir_stats()
        from main import logger
        logger.info("[SYSTEM] Limpieza profunda de sistema completada.")
        messagebox.showinfo("Limpieza Completada", "Se han eliminado los archivos temporales y caches del proyecto.")

    def _open_dir(self):
        import os
        d = self._audit_dir or Path(".audit")
        d.mkdir(parents=True, exist_ok=True)
        os.startfile(str(d.resolve()))

    # ── Terminal Logic ────────────────────────────────────────────────────────

    def _set_filter(self, val: str):
        self._filter_var.set(val)
        self._last_log_size = 0 # Force full reload on next tick
        self._load_log(clear=True)

    def _schedule_tail(self):
        if not self._tail_active: return
        self._load_log()
        self.after(1000, self._schedule_tail)

    def _get_log_path(self) -> Path:
        d = self._audit_dir or Path(".audit")
        return d / "pentest_audit.log"

    def _load_log(self, clear=False):
        log_path = self._get_log_path()
        if not log_path.exists(): return

        current_size = log_path.stat().st_size
        if current_size == self._last_log_size and not clear:
            return

        self._log_box.configure(state="normal")
        if clear or current_size < self._last_log_size:
            self._log_box.delete("0.0", "end")
            self._last_log_size = 0

        # Read only new content if possible, but for filters we might need full
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            if not clear and self._last_log_size > 0:
                f.seek(self._last_log_size)
            
            lines = f.readlines()
            for line in lines:
                self._append_styled_line(line)

        self._last_log_size = current_size
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _append_styled_line(self, line: str):
        # Format: 2026-05-01 19:00:02,123 - [LEVEL] Message
        # Simple parsing for tagging
        import re
        match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - (.*)", line)
        if match:
            ts, rest = match.groups()
            self._log_box.insert("end", f"[{ts}] ", "TIMESTAMP")
            
            tag = "INFO"
            if "ERROR" in rest: tag = "ERROR"
            elif "WARNING" in rest: tag = "WARNING"
            elif "[DEPS]" in rest: tag = "SYSTEM"
            
            self._log_box.insert("end", rest + "\n", tag)
        else:
            self._log_box.insert("end", line, "INFO")

    def _clear_log_file(self):
        from main import shutdown_logging, _setup_environment
        log_path = self._get_log_path()
        try: 
            # 1. Soltar el archivo (Cerrar handlers de logging)
            shutdown_logging()
            
            # 2. Eliminar el archivo físicamente
            if log_path.exists():
                log_path.unlink()
            
            # 3. Re-inicializar entorno pasivo (sin re-abrir el log)
            _setup_environment(str(self._audit_dir or ".audit"), start_logging=False)
            
            self._load_log(clear=True)
        except Exception as e:
            print(f"Error al limpiar log: {e}")

    def _copy_log(self):
        self._log_box.configure(state="normal")
        content = self._log_box.get("0.0", "end")
        self._log_box.configure(state="disabled")
        self.clipboard_clear()
        self.clipboard_append(content)
