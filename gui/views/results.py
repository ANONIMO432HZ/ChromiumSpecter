"""
Tab: Resultados
───────────────
Displays the credential table from the last audit run.
Features:
  • Expanding Widget Pool (Zero-destruction rendering)
  • Proportional grid architecture (Flexible columns)
  • Selectable text (mouse selection enabled)
  • Global & Per-row password visibility toggle
  • Per-field quick copy buttons (User/Pass)
  • Optimized for 1000+ records
"""

import customtkinter as ctk
import json
import threading
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox
from gui.theme import COLORS, FONTS, PAD, make_card, make_label, make_entry, make_button, make_badge

class ResultsView(ctk.CTkFrame):
    """Credential results table with expanding performance pool and quick-copy actions."""

    COLS = ["Navegador", "Perfil", "URL", "Usuario", "Contraseña"]
    COL_WEIGHTS = [1, 1, 4, 2, 2]

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._all_results = []
        self._filtered_results = []
        self._show_passwords = False
        self._revealed_indices = set()
        self._row_pool = []

        self._build_ui()

    def load_results(self, results):
        """Main entry point to inject audit data."""
        self._all_results = results if results else []
        self._revealed_indices.clear()
        self._on_search()

    def _build_ui(self):
        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = make_card(self)
        toolbar.pack(fill="x", padx=PAD["lg"], pady=(PAD["lg"], PAD["sm"]))

        inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        inner.pack(fill="x", padx=PAD["md"], pady=PAD["sm"])

        search_container = ctk.CTkFrame(inner, fg_color="transparent")
        search_container.pack(side="left", fill="x", expand=True)

        make_label(search_container, "🔍", style="subtitle").pack(side="left", padx=(0, PAD["sm"]))
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())
        search = make_entry(search_container, placeholder="Filtrar resultados...", width=380)
        search.configure(textvariable=self._search_var)
        search.pack(side="left", padx=(0, PAD["lg"]))

        self._stats_badge = make_badge(search_container, "0 REGISTROS", "text_muted")
        self._stats_badge.pack(side="left")

        actions_frame = ctk.CTkFrame(inner, fg_color="transparent")
        actions_frame.pack(side="right")
        
        make_button(actions_frame, "📦 Exportar ZIP", command=self._export_audit, style="action", width=130).pack(side="left", padx=PAD["xs"])
        make_button(actions_frame, "📋 Copiar JSON", command=self._copy_json, style="secondary", width=120).pack(side="left", padx=PAD["xs"])
        make_button(actions_frame, "🗑 Limpiar", command=self._clear_results, style="danger", width=100).pack(side="left")

        # ── Table View ────────────────────────────────────────────────────────
        self._table_container = make_card(self)
        self._table_container.pack(fill="both", expand=True, padx=PAD["lg"], pady=(0, PAD["lg"]))

        # --- Header Row ---
        self._hdr_frame = ctk.CTkFrame(self._table_container, fg_color=COLORS["bg_panel"], height=45, corner_radius=0)
        self._hdr_frame.pack(fill="x")
        self._hdr_frame.pack_propagate(False)
        
        for i, (col, weight) in enumerate(zip(self.COLS, self.COL_WEIGHTS)):
            self._hdr_frame.grid_columnconfigure(i, weight=weight)
            lbl_container = ctk.CTkFrame(self._hdr_frame, fg_color="transparent")
            lbl_container.grid(row=0, column=i, sticky="nsew", padx=PAD["sm"])
            
            content = ctk.CTkFrame(lbl_container, fg_color="transparent")
            content.pack(side="left", fill="y")
            lbl = ctk.CTkLabel(content, text=col.upper(), font=FONTS["heading"], text_color=COLORS["text_secondary"], anchor="w")
            lbl.pack(side="left")
            
            if col == "Contraseña":
                self._eye_btn = ctk.CTkButton(
                    content, text="👁", width=28, height=28, fg_color="transparent",
                    hover_color=COLORS["bg_card_hover"], font=("Segoe UI", 13),
                    text_color=COLORS["text_muted"], command=self._toggle_passwords_global
                )
                self._eye_btn.pack(side="left", padx=PAD["xs"])

        # --- Scrollable Body ---
        self._scroll = ctk.CTkScrollableFrame(
            self._table_container, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=COLORS["accent_dim"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self._scroll.pack(fill="both", expand=True)

        # --- Empty State Visual ---
        # Placed in table_container to avoid clipping by scroll internal frame
        self._empty_state = ctk.CTkFrame(self._table_container, fg_color="transparent")
        self._empty_state.place(relx=0.5, rely=0.6, anchor="center")
        
        ctk.CTkLabel(self._empty_state, text="STATUS: IDLE", font=FONTS["heading"], text_color=COLORS["accent_dim"]).pack()
        make_label(self._empty_state, "Bandeja de Resultados Vacía", style="subtitle", color=COLORS["text_secondary"]).pack(pady=(PAD["xs"], PAD["sm"]))
        make_label(self._empty_state, "Inicie una auditoría para recolectar datos.", style="small", color=COLORS["text_muted"]).pack()

    def _add_row_to_pool(self):
        """Creates a new optimized row with per-field action buttons."""
        idx = len(self._row_pool)
        row_frame = ctk.CTkFrame(self._scroll, fg_color="transparent", height=38, corner_radius=0, border_width=0)
        for i, weight in enumerate(self.COL_WEIGHTS):
            row_frame.grid_columnconfigure(i, weight=weight)
        
        entries = []
        for i in range(len(self.COLS)):
            entry_container = ctk.CTkFrame(row_frame, fg_color="transparent", border_width=0)
            entry_container.grid(row=0, column=i, sticky="nsew", padx=PAD["sm"], pady=4)
            
            e = ctk.CTkEntry(
                entry_container, fg_color="transparent", border_width=0,
                text_color=COLORS["text_primary"], font=FONTS["body"],
                state="readonly", height=30
            )
            e.pack(side="left", fill="both", expand=True)
            
            copy_btn = None
            eye_btn = None
            
            if i in (3, 4):
                copy_btn = ctk.CTkButton(
                    entry_container, text="📋", width=24, height=24, fg_color="transparent",
                    hover_color=COLORS["bg_card_hover"], font=("Segoe UI", 11),
                    text_color=COLORS["text_muted"],
                    command=lambda d_idx=idx, col=i: self._copy_cell(d_idx, col)
                )
                copy_btn.pack(side="right", padx=(2, 0))
            
            if i == 4:
                eye_btn = ctk.CTkButton(
                    entry_container, text="👁", width=24, height=24, fg_color="transparent",
                    hover_color=COLORS["bg_card_hover"], font=("Segoe UI", 11),
                    text_color=COLORS["text_muted"],
                    command=lambda d_idx=idx: self._toggle_row_password(d_idx)
                )
                eye_btn.pack(side="right")
            
            entries.append({"widget": e, "eye": eye_btn, "copy": copy_btn})
        
        row_data = {"frame": row_frame, "entries": entries}
        self._row_pool.append(row_data)
        return row_data

    def _update_view(self):
        data = self._filtered_results
        count = len(data)

        if count == 0:
            self._empty_state.place(relx=0.5, rely=0.6, anchor="center")
            for row in self._row_pool: row["frame"].pack_forget()
            return
        
        self._empty_state.place_forget()

        while len(self._row_pool) < count:
            self._add_row_to_pool()

        for i in range(len(self._row_pool)):
            row_widgets = self._row_pool[i]
            if i < count:
                item = data[i]
                row_widgets["frame"].pack(fill="x", pady=0, padx=PAD["xs"])
                
                bg = COLORS["bg_card"] if i % 2 == 0 else "transparent"
                row_widgets["frame"].configure(fg_color=bg)

                if row_widgets["entries"][3]["copy"]:
                    row_widgets["entries"][3]["copy"].configure(command=lambda d_idx=i: self._copy_cell(d_idx, 3))
                if row_widgets["entries"][4]["copy"]:
                    row_widgets["entries"][4]["copy"].configure(command=lambda d_idx=i: self._copy_cell(d_idx, 4))
                if row_widgets["entries"][4]["eye"]:
                    row_widgets["entries"][4]["eye"].configure(command=lambda d_idx=i: self._toggle_row_password(d_idx))

                for idx, (val, cell) in enumerate(zip(item[:5], row_widgets["entries"])):
                    entry = cell["widget"]
                    eye   = cell["eye"]
                    copy  = cell["copy"]
                    
                    entry.configure(state="normal")
                    entry.delete(0, "end")
                    
                    display_text = str(val)
                    revealed = self._show_passwords or (i in self._revealed_indices)
                    
                    if idx == 4:
                        if not revealed:
                            display_text = "•" * min(len(display_text), 14)
                        
                        eye.configure(
                            text="🙈" if (i in self._revealed_indices) else "👁",
                            text_color=COLORS["success"] if (i in self._revealed_indices) else COLORS["text_muted"]
                        )
                        if self._show_passwords: eye.pack_forget()
                        else: eye.pack(side="right")

                    entry.insert(0, display_text)
                    if idx == 2: entry.configure(text_color=COLORS["info"]) 
                    elif idx == 4: entry.configure(text_color=COLORS["accent"] if revealed else COLORS["text_primary"]) 
                    else: entry.configure(text_color=COLORS["text_primary"])
                    entry.configure(state="readonly")
            else:
                row_widgets["frame"].pack_forget()

    def _copy_cell(self, data_idx, col_idx):
        if data_idx < len(self._filtered_results):
            text = str(self._filtered_results[data_idx][col_idx])
            root = self.winfo_toplevel()
            root.clipboard_clear()
            root.clipboard_append(text)

    def _toggle_row_password(self, data_idx):
        if data_idx in self._revealed_indices:
            self._revealed_indices.remove(data_idx)
        else:
            self._revealed_indices.add(data_idx)
        self._update_view()

    def _toggle_passwords_global(self):
        self._show_passwords = not self._show_passwords
        self._eye_btn.configure(
            text="🙈" if self._show_passwords else "👁",
            text_color=COLORS["success"] if self._show_passwords else COLORS["text_muted"]
        )
        if self._show_passwords: self._revealed_indices.clear()
        self._update_view()

    def _on_search(self):
        query = self._search_var.get().lower()
        self._filtered_results = [r for r in self._all_results if any(query in str(f).lower() for f in r)] if query else self._all_results
        self._revealed_indices.clear() 
        self._update_view()
        self._stats_badge.configure(
            text=f"{len(self._filtered_results)} REGISTROS",
            fg_color=COLORS["accent_dim"] if self._filtered_results else COLORS["bg_card"],
            text_color=COLORS["accent"] if self._filtered_results else COLORS["text_muted"]
        )

    def _copy_json(self):
        if not self._filtered_results: return
        keys = ["navegador", "perfil", "url", "usuario", "contraseña"]
        data = [dict(zip(keys, r)) for r in self._filtered_results]
        root = self.winfo_toplevel()
        root.clipboard_clear()
        root.clipboard_append(json.dumps(data, ensure_ascii=False, indent=2))

    def _clear_results(self):
        self._all_results, self._filtered_results = [], []
        try:
            self.winfo_toplevel().clipboard_clear()
        except: pass
        self._on_search()

    def _export_audit(self):
        d = Path(".audit")
        if not d.exists() or not any(d.iterdir()):
            messagebox.showwarning("Exportar", "No hay datos de auditoría para exportar.")
            return
        save_path = filedialog.asksaveasfilename(
            title="Exportar Evidencia (ZIP)",
            initialfile=f"auditoria_chromium_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            defaultextension=".zip",
            filetypes=[("Archivo ZIP", "*.zip")]
        )
        if not save_path: return
        def _do():
            try:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    zip_base = Path(tmp_dir) / "export"
                    shutil.make_archive(str(zip_base), 'zip', d)
                    shutil.move(str(zip_base) + ".zip", save_path)
                self.after(0, lambda: messagebox.showinfo("Éxito", f"Evidencia exportada:\n{save_path}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Falla al exportar: {e}"))
        threading.Thread(target=_do, daemon=True).start()
