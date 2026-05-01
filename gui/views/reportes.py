"""
Tab: Reportes
─────────────
Browse, open and manage generated audit report files:
  • File list from the .audit directory
  • Open HTML/CSV in default app
  • Delete individual files or bulk-wipe
  • Preview CSV inline
"""

import os
import subprocess
import threading
import customtkinter as ctk
from pathlib import Path
from datetime import datetime

from gui.theme import (
    COLORS, FONTS, PAD,
    make_card, make_label, make_button, make_entry,
    make_section_header, make_badge,
)


class ReportesView(ctk.CTkFrame):
    """Report file browser and manager."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._audit_dir: Path | None = None
        self._files: list[Path] = []
        self._selected: Path | None = None
        self._build_ui()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_audit_dir(self, path: Path):
        self._audit_dir = path
        self._refresh_files()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = make_card(self)
        toolbar.pack(fill="x", padx=PAD["lg"], pady=(PAD["lg"], PAD["sm"]))

        tb = ctk.CTkFrame(toolbar, fg_color="transparent")
        tb.pack(fill="x", padx=PAD["md"], pady=PAD["sm"])

        make_label(tb, "Directorio:", style="small", color=COLORS["text_secondary"]).pack(side="left", padx=(0, PAD["sm"]))
        self._dir_var = ctk.StringVar(value=".audit")
        dir_entry = make_entry(tb, placeholder=".audit", width=240)
        dir_entry.configure(textvariable=self._dir_var)
        dir_entry.pack(side="left", padx=(0, PAD["sm"]))

        make_button(tb, "📂 Explorar",   command=self._browse_dir,    style="secondary", width=120).pack(side="left", padx=(0, PAD["sm"]))
        make_button(tb, "🔄 Refrescar", command=self._refresh_files, style="secondary", width=120).pack(side="left", padx=(0, PAD["sm"]))
        make_button(tb, "🗑 Eliminar todo", command=self._wipe_all,      style="danger",    width=130).pack(side="left")

        self._count_badge = make_badge(tb, "0 archivos", "text_muted")
        self._count_badge.pack(side="right", padx=PAD["sm"])

        # ── Split: file list + preview ────────────────────────────────────────
        # ── Split: file list + preview ────────────────────────────────────────
        split = ctk.CTkFrame(self, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=PAD["lg"], pady=(0, PAD["lg"]))

        # Left Column: File List
        left_col = ctk.CTkFrame(split, fg_color="transparent")
        left_col.pack(side="left", fill="y", padx=(0, PAD["sm"]))
        left_col.configure(width=280)

        make_section_header(left_col, "Archivos Generados", "📁")
        list_card = make_card(left_col)
        list_card.pack(fill="both", expand=True)

        self._file_list = ctk.CTkScrollableFrame(
            list_card,
            fg_color=COLORS["bg_input"],
            corner_radius=6,
            scrollbar_button_color=COLORS["accent_dim"],
            scrollbar_button_hover_color=COLORS["accent"],
            width=260,
        )
        self._file_list.pack(fill="both", expand=True, padx=PAD["sm"], pady=PAD["sm"])

        # Right Column: Preview + Actions
        right_col = ctk.CTkFrame(split, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True)

        make_section_header(right_col, "Vista Previa / Acciones", "🔍")
        preview_card = make_card(right_col)
        preview_card.pack(fill="both", expand=True)

        # Action bar inside preview card
        act_row = ctk.CTkFrame(preview_card, fg_color="transparent")
        act_row.pack(fill="x", padx=PAD["sm"], pady=(PAD["sm"], 0))

        make_button(act_row, "Visualizar", command=self._open_file, style="primary", width=110).pack(side="left", padx=(0, PAD["sm"]))
        make_button(act_row, "Eliminar",   command=self._delete_selected, style="danger", width=110).pack(side="left", padx=(0, PAD["sm"]))
        
        # New buttons: Copy and Clear
        make_button(act_row, "📋 Copiar",  command=self._copy_to_clipboard, style="action", width=100).pack(side="left", padx=(0, PAD["sm"]))
        make_button(act_row, "🧹 Limpiar", command=self._clear_preview,    style="action", width=100).pack(side="left", padx=(0, PAD["sm"]))

        self._selected_badge = make_badge(act_row, "ningún archivo seleccionado", "text_muted")
        self._selected_badge.pack(side="left", padx=PAD["sm"])

        self._preview_box = ctk.CTkTextbox(
            preview_card,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            font=FONTS["mono_sm"],
            corner_radius=8,
            border_width=0,
            state="disabled",
        )
        self._preview_box.pack(fill="both", expand=True, padx=PAD["sm"], pady=PAD["sm"])

        self._refresh_files()

    # ── File operations ───────────────────────────────────────────────────────

    def _get_audit_dir(self) -> Path:
        if self._audit_dir:
            return self._audit_dir
        raw = self._dir_var.get() or ".audit"
        return Path(raw)

    def _refresh_files(self):
        d = self._get_audit_dir()
        if d.exists():
            self._files = sorted(
                [f for f in d.iterdir() if f.suffix in (".html", ".csv", ".json", ".log")],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        else:
            self._files = []

        self._count_badge.configure(text=f"  {len(self._files)} archivos  ")
        self._render_file_list()

    def _render_file_list(self):
        for w in self._file_list.winfo_children():
            w.destroy()

        if not self._files:
            ctk.CTkLabel(
                self._file_list,
                text="Sin reportes.\nEjecutá una auditoría.",
                font=FONTS["small"],
                text_color=COLORS["text_muted"],
                justify="center",
            ).pack(pady=PAD["xl"])
            return

        ICON = {".html": "🌐", ".csv": "📊", ".json": "📋", ".log": "📝"}
        EXT_COLOR = {".html": "info", ".csv": "success", ".json": "accent", ".log": "text_muted"}

        for f in self._files:
            icon  = ICON.get(f.suffix, "📄")
            color = EXT_COLOR.get(f.suffix, "accent")
            size  = f.stat().st_size
            size_str = f"{size/1024:.1f} KB" if size >= 1024 else f"{size} B"
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%m/%d %H:%M")

            row = ctk.CTkFrame(
                self._file_list,
                fg_color=COLORS["bg_card"],
                corner_radius=6,
                cursor="hand2",
            )
            row.pack(fill="x", pady=2, padx=2)
            row.bind("<Button-1>", lambda e, fp=f: self._select_file(fp))

            hdr = ctk.CTkFrame(row, fg_color="transparent")
            hdr.pack(fill="x", padx=PAD["sm"], pady=(PAD["xs"], 0))
            hdr.bind("<Button-1>", lambda e, fp=f: self._select_file(fp))

            ctk.CTkLabel(hdr, text=icon, font=FONTS["body"]).pack(side="left")
            make_badge(hdr, f.suffix.upper().lstrip("."), color).pack(side="left", padx=PAD["xs"])

            meta = ctk.CTkFrame(row, fg_color="transparent")
            meta.pack(fill="x", padx=PAD["sm"], pady=(0, PAD["xs"]))
            meta.bind("<Button-1>", lambda e, fp=f: self._select_file(fp))
            ctk.CTkLabel(meta, text=f.name[:28] + ("…" if len(f.name) > 28 else ""), font=FONTS["tiny"], text_color=COLORS["text_primary"]).pack(side="left")
            ctk.CTkLabel(meta, text=f"{size_str} · {mtime}", font=FONTS["tiny"], text_color=COLORS["text_muted"]).pack(side="right")

    def _copy_to_clipboard(self):
        """Copy current preview text to system clipboard."""
        content = self._preview_box.get("1.0", "end-1c")
        if content and content != "Error al leer el archivo.":
            self.clipboard_clear()
            self.clipboard_append(content)

    def _clear_preview(self):
        """Clear the preview area and reset selection."""
        self._preview_box.configure(state="normal")
        self._preview_box.delete("1.0", "end")
        self._preview_box.configure(state="disabled")
        self._selected = None
        self._selected_badge.configure(text="  ningún archivo seleccionado  ", fg_color=COLORS["bg_card"], text_color=COLORS["text_muted"])

    def _select_file(self, path: Path):
        self._selected = path
        self._selected_badge.configure(
            text=f"  {path.name}  ",
            fg_color=COLORS["accent_dim"],
            text_color=COLORS["accent"],
        )
        self._load_preview(path)

    def _load_preview(self, path: Path):
        self._preview_box.configure(state="normal")
        self._preview_box.delete("0.0", "end")
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            lines   = content.splitlines()
            preview = "\n".join(lines[:120])
            if len(lines) > 120:
                preview += f"\n\n… ({len(lines) - 120} líneas más)"
            self._preview_box.insert("0.0", preview)
        except Exception as e:
            self._preview_box.insert("0.0", f"[Error al leer archivo: {e}]")
        self._preview_box.configure(state="disabled")

    def _open_file(self):
        if not self._selected:
            return
        try:
            os.startfile(str(self._selected))
        except Exception as e:
            pass

    def _delete_selected(self):
        if not self._selected:
            return
        try:
            self._selected.unlink(missing_ok=True)
        except Exception:
            pass
        self._selected = None
        self._selected_badge.configure(text="  ningún archivo  ", fg_color=COLORS["bg_card"], text_color=COLORS["text_muted"])
        self._preview_box.configure(state="normal")
        self._preview_box.delete("0.0", "end")
        self._preview_box.configure(state="disabled")
        self._refresh_files()

    def _wipe_all(self):
        """Aggressively delete all files in the audit directory, including logs."""
        d = self._get_audit_dir()
        if not d.exists():
            return

        # Iterate over all files in the directory to be thorough
        for f in d.iterdir():
            if f.is_file():
                try:
                    f.unlink(missing_ok=True)
                except Exception:
                    # Log file might be locked by the auditor, we ignore it silently or show a hint
                    pass
        
        # Reset UI state
        self._files = []
        self._clear_preview()
        self._refresh_files()

    def _browse_dir(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(title="Seleccioná el directorio de reportes")
        if d:
            self._dir_var.set(d)
            self.set_audit_dir(Path(d))
