"""
Tab: Exit Point
────────────────
Clean exit module with: "Eject Pendrive + Borrar Evidencias + Salir".
No credential storage — just UX for the final step.
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
    make_card, make_label, make_button,
    make_section_header,
)


class ExitView(ctk.CTkFrame):
    """Final exit workflow card with eject + delete + quit sequence."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build_ui()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        make_section_header(self, "Punto de Salida", "🚪")

        # Main card
        card = make_card(self)
        card.pack(fill="x", padx=PAD["lg"], pady=PAD["md"])
        card.configure(height=420)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=PAD["xl"], pady=PAD["xl"])

        # Icon centered above text
        icon_label = ctk.CTkLabel(inner, text="🚨", font=("Segoe UI", 48))
        icon_label.pack(pady=(0, PAD["lg"]))

        # Title
        make_label(
            inner,
            "ELIMINAR EVIDENCIAS Y SALIR",
            style="subtitle",
            color=COLORS["danger"],
        ).pack(pady=(0, PAD["md"]))

        # Description
        msg = "Esta acción borrará todos los archivos temporales y logs, eyectará el pendrive virtual y cerrará la aplicación."
        make_label(inner, msg, style="body", color=COLORS["text_secondary"], wraplength=520, justify="center").pack(pady=(0, PAD["lg"]))

        # Action buttons row - Centered
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(pady=(0, PAD["md"]))

        make_button(
            btn_row,
            "🗑️ BORRAR Y SALIR",
            command=self._run_exit_procedure,
            style="danger",
            width=180,
            height=48,
        ).pack(side="left", padx=PAD["xs"])

        make_button(
            btn_row,
            "🚪 SALIR",
            command=self._perform_quit,
            style="secondary",
            width=140,
            height=48,
        ).pack(side="left", padx=PAD["xs"])

        # Legal / disclaimer
        legal = ctk.CTkFrame(inner, fg_color="transparent")
        legal.pack(pady=(PAD["lg"], 0))
        make_label(legal, "⚠️ ADVERTENCIA: Esta operación es irreversible.", style="small", color=COLORS["warning"]).pack()

    # ── Workflow ──────────────────────────────────────────────────────────────

    def _cancel_exit(self):
        """Go back to the first tab (Auditoria)."""
        try:
            # Assuming the sidebar uses a specific method to switch
            self.master.master._on_nav_click("Auditoria")
        except:
            pass

    def _run_exit_procedure(self):
        if messagebox.askyesno(
            "Confirmar salida",
            "¿Estás seguro de que deseas:\n\n"
            "1. Eyectar el pendrive virtual?\n"
            "2. Borrar todas las evidencias (logs, auditorías)?\n"
            "3. Salir de la aplicación?",
            icon='warning'
        ):
            self._perform_eject()
            self._perform_delete()
            self._perform_quit()

    def _perform_eject(self):
        """Native Windows ejection using COM objects."""
        try:
            mountpoint = os.getenv("MOUNTPOINT") or "E:"
            drive_letter = mountpoint.strip().replace("\\", "")[:2] # Ensure "E:" format
            
            ps_script = f'(New-Object -ComObject Shell.Application).Namespace(17).ParseName("{drive_letter}").InvokeVerb("Eject")'
            cmd = ["powershell", "-NoProfile", "-Command", ps_script]
            
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"[+] Drive {drive_letter} ejected.")
        except Exception as e:
            print(f"[-] Warning: failed to eject drive: {e}")

    def _perform_delete(self):
        """Delete all traces (logs, temp source, audit results)."""
        targets = [
            Path("logs"),
            Path(".audit"),
            Path("_main_build_patched.py"),
            Path("_main_backup.py"),
            Path("main_patched.py")
        ]

        for target in targets:
            try:
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink(missing_ok=True)
                print(f"[+] Cleaned: {target}")
            except Exception as e:
                print(f"[-] Error cleaning {target}: {e}")

    def _perform_quit(self):
        """Close the application cleanly."""
        print("[!] Exiting suite. Goodbye.")
        self.master.destroy()
        sys.exit(0)
