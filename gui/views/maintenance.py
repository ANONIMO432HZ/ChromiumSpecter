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

        split = ctk.CTkFrame(dep_inner, fg_color="transparent")
        split.pack(fill="x")

        left_col = ctk.CTkFrame(split, fg_color="transparent")
        left_col.pack(side="left", fill="y", padx=(0, PAD["md"]))

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

        grid = ctk.CTkFrame(left_col, fg_color="transparent")
        grid.pack(fill="x")

        for i, (mod, label, pkg) in enumerate(DEPS):
            row, col = divmod(i, 2)
            f = ctk.CTkFrame(grid, fg_color="transparent")
            f.grid(row=row, column=col, sticky="w", padx=PAD["sm"], pady=2)
            make_label(f, f"  {label}", style="body", color=COLORS["text_primary"], width=110, anchor="w").pack(side="left", padx=(0, PAD["sm"]))
            badge = make_badge(f, "verificando…", "text_muted")
            badge.pack(side="left")
            self._dep_badges[mod] = badge

        self._dep_actions = ctk.CTkFrame(left_col, fg_color="transparent")
        self._dep_actions.pack(fill="x", pady=(PAD["sm"], 0))

        make_button(self._dep_actions, "🔄 Re-verificar", command=self._check_deps, style="secondary", width=140).pack(side="left", padx=(0, PAD["sm"]))
        self._repair_btn = make_button(self._dep_actions, "🔧 Reparar Entorno", command=self._install_missing, style="primary", width=160)
        
        right_col = ctk.CTkFrame(split, fg_color=COLORS["bg_input"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        right_col.pack(side="left", fill="both", expand=True)

        self._dep_log = ctk.CTkTextbox(
            right_col,
            fg_color="transparent",
            text_color=COLORS["text_secondary"],
            font=FONTS["mono_sm"],
            height=120,
            state="disabled",
            border_width=0,
        )
        self._dep_log.pack(fill="both", expand=True, padx=2, pady=2)

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
        make_button(btn_row, "🔄 Actualizar", command=self._refresh_dir_stats, style="secondary", width=120).pack(side="left", padx=(0, PAD["sm"]))
        make_button(btn_row, "🗑 Limpiar audits", command=self._clean_audits, style="danger", width=140).pack(side="left", padx=(0, PAD["sm"]))
        make_button(btn_row, "🧹 Limpiar sistema", command=self._clean_system, style="danger", width=140).pack(side="left", padx=(0, PAD["sm"]))
        make_button(btn_row, "📂 Abrir carpeta", command=self._open_dir, style="secondary", width=130).pack(side="left")

        # ── Log viewer ────────────────────────────────────────────────────────
        make_section_header(self, "Log del Sistema (pentest_audit.log)", "📋")
        log_card = make_card(self)
        log_card.pack(fill="both", expand=True, padx=PAD["lg"], pady=(0, PAD["md"]))

        log_toolbar = ctk.CTkFrame(log_card, fg_color="transparent")
        log_toolbar.pack(fill="x", padx=PAD["sm"], pady=(PAD["sm"], 0))
        make_button(log_toolbar, "🔄 Cargar log", command=self._load_log, style="secondary", width=120).pack(side="left", padx=(0, PAD["sm"]))
        make_button(log_toolbar, "🗑 Limpiar log", command=self._clear_log_file, style="danger", width=120).pack(side="left", padx=(0, PAD["sm"]))
        make_button(log_toolbar, "📋 Copiar todo", command=self._copy_log, style="secondary", width=120).pack(side="left")
        self._log_size_badge = make_badge(log_toolbar, "—", "text_muted")
        self._log_size_badge.pack(side="right", padx=PAD["sm"])

        self._log_box = ctk.CTkTextbox(
            log_card,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            font=FONTS["code"],
            corner_radius=8,
            border_width=0,
            state="disabled",
        )
        self._log_box.pack(fill="both", expand=True, padx=PAD["sm"], pady=PAD["sm"])

    # ── Dependency checker ────────────────────────────────────────────────────

    def _log_dep(self, msg: str, clear=False):
        self._dep_log.configure(state="normal")
        if clear: self._dep_log.delete("0.0", "end")
        self._dep_log.insert("end", f" {msg}\n")
        self._dep_log.see("end")
        self._dep_log.configure(state="disabled")

    def _check_deps(self):
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
            self._missing_deps = []
            for mod, pkg in DEPS:
                try:
                    importlib.import_module(mod)
                    ok = True
                except ImportError:
                    ok = False
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
                        errors="replace"
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
        d = self._audit_dir or Path(".audit")
        if not d.exists(): return
        for f in d.iterdir():
            if f.is_file():
                try: f.unlink(missing_ok=True)
                except Exception: pass
        self._refresh_dir_stats()

    def _clean_system(self):
        """Limpieza profunda de archivos temporales del sistema y compilación."""
        import shutil, os
        from tkinter import messagebox
        
        if not messagebox.askyesno("Limpiar Sistema", "¿Estás seguro de eliminar todos los archivos temporales (__pycache__, temp, spec, etc)?"):
            return

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
                try: shutil.rmtree(p)
                except: pass

        self._refresh_dir_stats()
        messagebox.showinfo("Limpieza Completada", "Se han eliminado los archivos temporales y caches del proyecto.")

    def _open_dir(self):
        import os
        d = self._audit_dir or Path(".audit")
        d.mkdir(parents=True, exist_ok=True)
        os.startfile(str(d.resolve()))

    # ── Log viewer ────────────────────────────────────────────────────────────

    def _get_log_path(self) -> Path:
        d = self._audit_dir or Path(".audit")
        return d / "pentest_audit.log"

    def _load_log(self):
        log_path = self._get_log_path()
        self._log_box.configure(state="normal")
        self._log_box.delete("0.0", "end")
        if not log_path.exists():
            self._log_box.insert("0.0", f"[Log no encontrado: {log_path}]")
            self._log_size_badge.configure(text="  —  ")
        else:
            content = log_path.read_text(encoding="utf-8", errors="replace")
            self._log_box.insert("0.0", content)
            self._log_box._textbox.see("end")
            size = log_path.stat().st_size
            self._log_size_badge.configure(text=f"  {size/1024:.1f} KB  ")
        self._log_box.configure(state="disabled")

    def _clear_log_file(self):
        log_path = self._get_log_path()
        try: log_path.write_text("", encoding="utf-8")
        except Exception: pass
        self._load_log()

    def _copy_log(self):
        self._log_box.configure(state="normal")
        content = self._log_box.get("0.0", "end")
        self._log_box.configure(state="disabled")
        self.clipboard_clear()
        self.clipboard_append(content)
