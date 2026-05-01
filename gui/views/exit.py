"""
Tab: Exit Point
────────────────
Premium exit module with high-density security options.
Centralizes evidence wiping and the timed self-destruct protocol.
"""

import os
import sys
import shutil
import subprocess
import customtkinter as ctk
from pathlib import Path
from tkinter import messagebox

from gui.theme import (
    COLORS, FONTS, PAD,
    make_card, make_label, make_button, make_entry,
    make_section_header
)


class ExitView(ctk.CTkFrame):
    """Final exit workflow with a high-tech security aesthetic."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build_ui()

    def _build_ui(self):
        # ── Main Layout ───────────────────────────────────────────────────────
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header across top
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=PAD["lg"], pady=(PAD["lg"], 0))
        make_section_header(header_frame, "Finalización de Sesión", "🛡️")

        # ── Left Column: Standard Exit & Wipe ─────────────────────────────────
        left_col = ctk.CTkFrame(self, fg_color="transparent")
        left_col.grid(row=1, column=0, sticky="nsew", padx=(PAD["lg"], PAD["md"]), pady=PAD["lg"])

        exit_card = make_card(left_col)
        exit_card.pack(fill="both", expand=True)

        exit_inner = ctk.CTkFrame(exit_card, fg_color="transparent")
        exit_inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(exit_inner, text="🚪", font=("Segoe UI", 64)).pack(pady=(0, PAD["md"]))
        
        make_label(exit_inner, "CIERRE ESTÁNDAR", style="subtitle", color=COLORS["accent"]).pack()
        make_label(exit_inner, "Finaliza la sesión de auditoría de forma segura.", 
                   style="small", color=COLORS["text_secondary"], justify="center").pack(pady=(0, PAD["xl"]))

        # Action Buttons for Standard Exit
        make_button(
            exit_inner,
            "🗑️  BORRAR EVIDENCIAS Y SALIR",
            command=self._run_exit_procedure,
            style="danger",
            width=260,
            height=45
        ).pack(pady=PAD["xs"])

        make_button(
            exit_inner,
            "🚪  SALIR SIN BORRAR",
            command=self._perform_quit,
            style="secondary",
            width=260,
            height=45
        ).pack(pady=PAD["xs"])

        make_label(exit_inner, "⚠ Borra logs, reportes y temporales locales.", 
                   style="tiny", color=COLORS["text_muted"]).pack(pady=(PAD["sm"], 0))

        # ── Right Column: High-Consequence Destruct ───────────────────────────
        right_col = ctk.CTkFrame(self, fg_color="transparent")
        right_col.grid(row=1, column=1, sticky="nsew", padx=(PAD["md"], PAD["lg"]), pady=PAD["lg"])

        panic_card = ctk.CTkFrame(
            right_col, 
            fg_color=COLORS["bg_input"], 
            corner_radius=12, 
            border_width=2, 
            border_color=COLORS["danger_dim"]
        )
        panic_card.pack(fill="both", expand=True)

        panic_inner = ctk.CTkFrame(panic_card, fg_color="transparent")
        panic_inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(panic_inner, text="🧨", font=("Segoe UI", 64)).pack(pady=(0, PAD["md"]))
        
        make_label(panic_inner, "PROTOCOLO DE PÁNICO", style="subtitle", color=COLORS["danger"]).pack()
        make_label(panic_inner, "AUTODESTRUCCIÓN TOTAL DEL PROYECTO", 
                   style="small", color=COLORS["text_secondary"], justify="center").pack(pady=(0, PAD["xl"]))

        # Config Frame for Destruct
        cfg_frame = ctk.CTkFrame(panic_inner, fg_color=COLORS["bg_panel"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        cfg_frame.pack(fill="x", padx=PAD["md"], pady=(0, PAD["lg"]))

        cfg_row = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        cfg_row.pack(padx=PAD["md"], pady=PAD["md"])

        make_label(cfg_row, "Retraso (seg):", style="small", color=COLORS["text_secondary"]).pack(side="left", padx=(0, PAD["sm"]))
        self._sd_timer_var = ctk.StringVar(value="5")
        timer_entry = make_entry(cfg_row, placeholder="5", width=60)
        timer_entry.configure(textvariable=self._sd_timer_var)
        timer_entry.pack(side="left")

        # The Big Red Button
        make_button(
            panic_inner,
            "🔥  INICIAR AUTODESTRUCCIÓN",
            command=self._self_destruct,
            style="danger",
            width=280,
            height=55
        ).pack(pady=PAD["xs"])

        warn_box = ctk.CTkFrame(panic_inner, fg_color="transparent")
        warn_box.pack(pady=(PAD["sm"], 0))
        make_label(warn_box, "❗ ESTA ACCIÓN ELIMINARÁ TODA LA CARPETA RAÍZ,", 
                   style="tiny", color=COLORS["danger"]).pack()
        make_label(warn_box, "RASTROS DE WINDOWS Y PORTAPAPELES.", 
                   style="tiny", color=COLORS["danger"]).pack()

    # ── Logic Handlers ────────────────────────────────────────────────────────

    def _run_exit_procedure(self):
        if messagebox.askyesno(
            "Confirmar Limpieza",
            "¿Deseas eyectar el pendrive virtual y borrar todas las evidencias locales antes de salir?",
            icon='warning'
        ):
            self._perform_eject()
            self._perform_delete()
            self._perform_quit()

    def _perform_eject(self):
        try:
            mountpoint = os.getenv("MOUNTPOINT") or "E:"
            drive_letter = mountpoint.strip().replace("\\", "")[:2]
            ps_script = f'(New-Object -ComObject Shell.Application).Namespace(17).ParseName("{drive_letter}").InvokeVerb("Eject")'
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True)
        except: pass

    def _perform_delete(self):
        """Borrado profundo de evidencias y archivos temporales antes de salir."""
        targets = [
            "logs", ".audit", "build", "dist", "tmp", "temp", 
            ".pytest_cache", ".pyarmor", ".venv/target", 
            "gui/__pycache__", "gui/views/__pycache__",
            "_main_build_patched.py", "_main_backup.py", "main_patched.py"
        ]

        # 1. Limpiar objetivos explícitos
        for t in targets:
            p = Path(t)
            if p.exists():
                try:
                    if p.is_dir(): shutil.rmtree(p)
                    else: p.unlink()
                except: pass

        # 2. Barrido recursivo de archivos de rastro y caches
        for ext in ["*.spec", "*.pyc", "*.pyo", "__pycache__"]:
            for p in Path(".").rglob(ext):
                try:
                    if p.is_dir(): shutil.rmtree(p)
                    else: p.unlink()
                except: pass

    def _self_destruct(self):
        try:
            seconds = int(self._sd_timer_var.get())
        except:
            messagebox.showerror("Error", "Ingresá un tiempo válido.")
            return

        if not messagebox.askyesno("CONFIRMACIÓN CRÍTICA", f"¿CONFIRMAR AUTODESTRUCCIÓN TOTAL EN {seconds} SEGUNDOS?"):
            return

        root_dir = Path(".").resolve()
        parent_dir = root_dir.parent
        current_pid = os.getpid()

        bat_content = f"""@echo off
title PROTOCOLO DE AUTODESTRUCCIÓN - EJECUTANDO...
echo [*] Iniciando protocolo de saneamiento total...
echo [*] Esperando {seconds} segundos de gracia...
timeout /t {seconds} /nobreak >nul
echo [*] Forzando cierre de procesos del sistema...
taskkill /F /PID {current_pid} /T >nul 2>&1
echo [*] Limpiando portapapeles de Windows...
echo off | clip >nul 2>&1
echo [*] Eliminando archivos temporales de usuario...
del /q /s /f "%TEMP%\\*" >nul 2>&1
echo [*] Eliminando carpeta raiz de la suite: {root_dir}
cd /d "{parent_dir}"
rd /s /q "{root_dir}"
echo [*] Saneamiento de rastros locales...
powershell -Command "Clear-History" >nul 2>&1
echo [+] Protocolo completado con exito.
timeout /t 3 >nul
del "%~f0"
"""
        try:
            bat_path = parent_dir / "wipe_suite.bat"
            bat_path.write_text(bat_content, encoding="cp850")
            subprocess.Popen(["cmd.exe", "/c", str(bat_path)], creationflags=subprocess.CREATE_NEW_CONSOLE)
            self._perform_quit()
        except Exception as e:
            messagebox.showerror("Error", f"Falla en el protocolo: {e}")

    def _perform_quit(self):
        """Close the application cleanly."""
        try:
            # Safer way to get the root window and close it
            root = self.winfo_toplevel()
            root.destroy()
        except Exception:
            # Fallback
            sys.exit(0)
