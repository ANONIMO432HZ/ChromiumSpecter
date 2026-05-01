"""
Design system & theme tokens for the Chromium Auditor Dashboard.
All views import from here — no ad-hoc colors or fonts allowed.
"""

import customtkinter as ctk

# ─── Appearance ─────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ─── Color Palette ──────────────────────────────────────────────────────────
COLORS = {
    # Backgrounds
    "bg_root":       "#0d0f17",
    "bg_sidebar":    "#12141f",
    "bg_panel":      "#181b28",
    "bg_card":       "#1e2235",
    "bg_card_hover": "#232740",
    "bg_input":      "#141620",

    # Accent / Brand
    "accent":        "#4f8ef7",
    "accent_hover":  "#6aa3ff",
    "accent_dim":    "#1e3a6e",
    "accent_glow":   "#2563eb",

    # Status
    "success":       "#22c55e",
    "success_dim":   "#14532d",
    "warning":       "#f59e0b",
    "warning_dim":   "#78350f",
    "danger":        "#ef4444",
    "danger_dim":    "#7f1d1d",
    "info":          "#06b6d4",
    "info_dim":      "#0e4f5c",

    # Text
    "text_primary":  "#e8eaf6",
    "text_secondary":"#8892b0",
    "text_muted":    "#4a5568",
    "text_accent":   "#4f8ef7",

    # Borders
    "border":        "#252840",
    "border_focus":  "#4f8ef7",
}

# ─── Typography ─────────────────────────────────────────────────────────────
FONTS = {
    "title":     ("Segoe UI", 22, "bold"),
    "subtitle":  ("Segoe UI", 14, "bold"),
    "heading":   ("Segoe UI", 13, "bold"),
    "body":      ("Segoe UI", 12),
    "small":     ("Segoe UI", 11),
    "tiny":      ("Segoe UI", 10),
    "mono":      ("Consolas", 12),
    "mono_sm":   ("Consolas", 10),
    "badge":     ("Segoe UI", 10, "bold"),
    "nav":       ("Segoe UI", 13),
    "nav_active":("Segoe UI", 13, "bold"),
    "stat":      ("Segoe UI", 28, "bold"),
    "stat_label":("Segoe UI", 11),
    "code":      ("Consolas", 11),
}

# ─── Spacing ─────────────────────────────────────────────────────────────────
PAD = {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32}

# ─── Reusable Widget Factories ───────────────────────────────────────────────

def make_card(parent, **kwargs) -> ctk.CTkFrame:
    """Standard card container."""
    return ctk.CTkFrame(
        parent,
        fg_color=COLORS["bg_card"],
        corner_radius=10,
        border_width=1,
        border_color=COLORS["border"],
        **kwargs,
    )


def make_label(parent, text, style="body", color=None, **kwargs) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent,
        text=text,
        font=FONTS[style],
        text_color=color or COLORS["text_primary"],
        **kwargs,
    )


def make_button(parent, text, command=None, style="primary", width=140, **kwargs) -> ctk.CTkButton:
    palette = {
        # Style: (fg_color, hover_color, text_color, border_width, border_color)
        "primary":   (COLORS["accent"],       COLORS["accent_hover"],  COLORS["text_primary"],   0, None),
        "secondary": (COLORS["success_dim"],  COLORS["success"],       COLORS["text_primary"],   0, None),
        "danger":    (COLORS["danger_dim"],   COLORS["danger"],        COLORS["text_primary"],   0, None),
        "success":   (COLORS["success_dim"],  COLORS["success"],       COLORS["text_primary"],   0, None),
        "warning":   (COLORS["warning_dim"],  COLORS["warning"],       COLORS["bg_root"],        0, None),
        "busy":      (COLORS["accent_dim"],   COLORS["accent_dim"],    COLORS["text_secondary"], 0, None),
        # Aliases para mantener compatibilidad pero forzando el look sólido
        "action":    (COLORS["accent_dim"],    COLORS["accent"],        COLORS["text_primary"],   0, None),
        "ghost":     (COLORS["success_dim"],   COLORS["success"],       COLORS["text_primary"],   0, None), # Alias sólido
    }
    fg, hover, txt, bw, bc = palette.get(style, palette["primary"])
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=fg,
        hover_color=hover,
        text_color=txt,
        text_color_disabled=txt, # Prevent the "opaque" look
        border_width=bw,
        border_color=bc,
        font=FONTS["body"],
        corner_radius=8,
        width=width,
        **kwargs,
    )


def make_entry(parent, placeholder="", show=None, width=200, **kwargs) -> ctk.CTkEntry:
    e_kwargs = dict(
        placeholder_text=placeholder,
        fg_color=COLORS["bg_input"],
        border_color=COLORS["border"],
        border_width=1,
        text_color=COLORS["text_primary"],
        placeholder_text_color=COLORS["text_muted"],
        font=FONTS["body"],
        corner_radius=8,
        width=width,
    )
    if show is not None:
        e_kwargs["show"] = show
    e_kwargs.update(kwargs)
    return ctk.CTkEntry(parent, **e_kwargs)


def make_section_header(parent, text: str, icon: str = ""):
    """Returns a labelled divider row."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=PAD["md"], pady=(PAD["md"], PAD["sm"]))
    lbl = ctk.CTkLabel(
        row,
        text=f"{icon}  {text}" if icon else text,
        font=FONTS["heading"],
        text_color=COLORS["text_accent"],
    )
    lbl.pack(side="left")
    line = ctk.CTkFrame(row, fg_color=COLORS["border"], height=1)
    line.pack(side="left", fill="x", expand=True, padx=(PAD["sm"], 0), pady=PAD["xs"])
    return row


def make_badge(parent, text: str, color_key: str = "accent") -> ctk.CTkLabel:
    bg = COLORS.get(f"{color_key}_dim", COLORS["accent_dim"])
    fg = COLORS.get(color_key, COLORS["accent"])
    return ctk.CTkLabel(
        parent,
        text=text.upper(),
        font=FONTS["badge"],
        text_color=fg,
        fg_color=bg,
        corner_radius=12,
        height=24,
        padx=12,
    )


def make_stat_card(parent, label: str, value: str, icon: str, color_key="accent") -> ctk.CTkFrame:
    card = make_card(parent)
    card.configure(width=160)
    icon_lbl = ctk.CTkLabel(card, text=icon, font=("Segoe UI Emoji", 26), text_color=COLORS.get(color_key, COLORS["accent"]))
    icon_lbl.pack(pady=(PAD["lg"], PAD["xs"]))
    ctk.CTkLabel(card, text=value, font=FONTS["stat"], text_color=COLORS.get(color_key, COLORS["accent"])).pack()
    ctk.CTkLabel(card, text=label, font=FONTS["stat_label"], text_color=COLORS["text_secondary"]).pack(pady=(PAD["xs"], PAD["lg"]))
    return card


# ── Utility Button Helpers ───────────────────────────────────────────
# Contract: add_xxx_button(parent, ..., **kwargs) → CTkButton
# All buttons use style="secondary" and width=36 by default.
# Override via **kwargs. Call .pack()/.grid() on the returned widget.

def add_clear_button(parent, entry, **kwargs):
    """🗑  Clears a CTkEntry and its linked StringVar."""
    def clear():
        entry.delete(0, "end")
        try:
            if hasattr(entry, "_textvariable") and entry._textvariable:
                entry._textvariable.set("")
        except Exception:
            pass
    text = kwargs.pop("text", "🗑")
    kwargs.setdefault("style", "secondary")
    kwargs.setdefault("width", 36)
    return make_button(parent, text, command=clear, **kwargs)


def add_reveal_button(parent, entry, **kwargs):
    """👁  Toggles password visibility on a CTkEntry (show='*' ↔ '')."""
    def toggle():
        entry.configure(show="" if entry.cget("show") == "*" else "*")
    text = kwargs.pop("text", "👁")
    kwargs.setdefault("style", "secondary")
    kwargs.setdefault("width", 36)
    return make_button(parent, text, command=toggle, **kwargs)


def add_folder_button(parent, callback, **kwargs):
    """📂  Opens a native folder-picker dialog and calls callback(path)."""
    from tkinter import filedialog

    def pick():
        path = filedialog.askdirectory(title="Seleccionar carpeta")
        if path:
            callback(path)
    text = kwargs.pop("text", "📂")
    kwargs.setdefault("style", "secondary")
    kwargs.setdefault("width", 40)
    return make_button(parent, text, command=pick, **kwargs)


def add_file_button(parent, callback, filetypes=None, **kwargs):
    """📄  Opens a native file-picker dialog and calls callback(path)."""
    from tkinter import filedialog

    def pick():
        path = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=filetypes or [("Todos los archivos", "*.*")],
        )
        if path:
            callback(path)
    text = kwargs.pop("text", "📄")
    kwargs.setdefault("style", "secondary")
    kwargs.setdefault("width", 40)
    return make_button(parent, text, command=pick, **kwargs)


def add_copy_button(parent, get_text, **kwargs):
    """📋  Copies get_text() result to the clipboard."""
    import customtkinter as _ctk

    def copy():
        text = get_text() if callable(get_text) else str(get_text)
        root = parent.winfo_toplevel()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
    text = kwargs.pop("text", "📋")
    kwargs.setdefault("style", "secondary")
    kwargs.setdefault("width", 36)
    return make_button(parent, text, command=copy, **kwargs)


def add_refresh_button(parent, callback, **kwargs):
    """🔄  Calls callback() — use for reload / reset actions."""
    text = kwargs.pop("text", "🔄")
    kwargs.setdefault("style", "secondary")
    kwargs.setdefault("width", 36)
    return make_button(parent, text, command=callback, **kwargs)


def add_open_button(parent, get_path, **kwargs):
    """📤  Opens a file or folder in the OS native explorer."""
    import subprocess as _sp
    import sys as _sys

    def open_path():
        path = get_path() if callable(get_path) else str(get_path)
        if _sys.platform == "win32":
            _sp.Popen(["explorer", path])
        elif _sys.platform == "darwin":
            _sp.Popen(["open", path])
        else:
            _sp.Popen(["xdg-open", path])
    text = kwargs.pop("text", "📤")
    kwargs.setdefault("style", "secondary")
    kwargs.setdefault("width", 36)
    return make_button(parent, text, command=open_path, **kwargs)


def add_info_button(parent, message, title="Ayuda", **kwargs):
    """ℹ️  Shows a simple messagebox with the provided help text."""
    from tkinter import messagebox

    def show():
        messagebox.showinfo(title, message)
    text = kwargs.pop("text", "ℹ️")
    kwargs.setdefault("style", "secondary")
    kwargs.setdefault("width", 36)
    return make_button(parent, text, command=show, **kwargs)
