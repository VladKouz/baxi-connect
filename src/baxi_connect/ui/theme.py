from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


class Theme:
    bg = "#0f1117"
    surface = "#181b24"
    card = "#1f2430"
    card_hover = "#252b3a"
    border = "#2d3548"
    text = "#f4f6fb"
    text_secondary = "#8b93a7"
    text_muted = "#5c6478"
    accent = "#ff6b3d"
    accent_soft = "#ff6b3d22"
    success = "#34d399"
    warning = "#fbbf24"
    danger = "#f87171"
    info = "#60a5fa"

    mode_colors = {
        "комфорт": "#34d399",
        "эконом": "#60a5fa",
        "ночь": "#a78bfa",
        "лето": "#fbbf24",
        "выключен": "#6b7280",
    }

    metric_colors = {
        "temperature_boiler": "#ff6b3d",
        "burner_modulation": "#fbbf24",
        "pressure": "#60a5fa",
        "temperature_dhw": "#34d399",
    }

    @classmethod
    def mode_color(cls, mode_name: str) -> str:
        return cls.mode_colors.get(mode_name.casefold(), cls.accent)

    @classmethod
    def pick_font_family(cls, root: tk.Misc) -> str:
        families = set(tkfont.families(root))
        for candidate in ("SF Pro Display", "SF Pro Text", "Helvetica Neue", "Helvetica", "Arial"):
            if candidate in families:
                return candidate
        return "TkDefaultFont"


def apply_ttk_theme(root: tk.Misc) -> None:
    family = Theme.pick_font_family(root)
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=Theme.bg, foreground=Theme.text, font=(family, 12))
    style.configure("TFrame", background=Theme.bg)
    style.configure("Card.TFrame", background=Theme.surface)
    style.configure("TLabel", background=Theme.bg, foreground=Theme.text)
    style.configure("Muted.TLabel", background=Theme.bg, foreground=Theme.text_secondary)
    style.configure("Section.TLabel", background=Theme.bg, foreground=Theme.text, font=(family, 14, "bold"))
    style.configure(
        "TEntry",
        fieldbackground=Theme.card,
        foreground=Theme.text,
        bordercolor=Theme.border,
        lightcolor=Theme.border,
        darkcolor=Theme.border,
        insertcolor=Theme.text,
        padding=8,
    )
    style.configure("TSeparator", background=Theme.border)
    style.configure(
        "Accent.TButton",
        background=Theme.accent,
        foreground="#ffffff",
        borderwidth=0,
        focuscolor=Theme.accent,
        padding=(16, 10),
        font=(family, 12, "bold"),
    )
    style.map(
        "Accent.TButton",
        background=[("active", "#ff825c"), ("pressed", "#e85a30")],
        foreground=[("disabled", "#ffffff")],
    )
    style.configure(
        "Ghost.TButton",
        background=Theme.card,
        foreground=Theme.text_secondary,
        borderwidth=0,
        focuscolor=Theme.card,
        padding=(16, 10),
        font=(family, 12),
    )
    style.map(
        "Ghost.TButton",
        background=[("active", Theme.card_hover), ("pressed", Theme.border)],
        foreground=[("active", Theme.text)],
    )


class IconButton(tk.Canvas):
    def __init__(
        self,
        master: tk.Misc,
        text: str,
        command,
        size: int = 36,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            width=size,
            height=size,
            bg=Theme.bg,
            highlightthickness=0,
            **kwargs,
        )
        self._command = command
        self._text = text
        self._size = size
        self._hover = False
        self._draw()
        self.bind("<Button-1>", lambda _e: self._command())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.configure(cursor="hand2")

    def _draw(self) -> None:
        self.delete("all")
        fill = Theme.card_hover if self._hover else Theme.card
        r = 10
        s = self._size
        self._round_rect(2, 2, s - 2, s - 2, r, fill=fill, outline=Theme.border)
        self.create_text(s / 2, s / 2, text=self._text, fill=Theme.text, font=("", 14))

    def _round_rect(self, x1, y1, x2, y2, radius, **kwargs) -> None:
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        self.create_polygon(points, smooth=True, **kwargs)

    def _on_enter(self, _event: tk.Event) -> None:
        self._hover = True
        self._draw()

    def _on_leave(self, _event: tk.Event) -> None:
        self._hover = False
        self._draw()


class MetricCard(tk.Frame):
    FOOTER_HEIGHT = 22
    BAR_HEIGHT = 10

    def __init__(
        self,
        master: tk.Misc,
        key: str,
        title: str,
        unit: str,
        value_font: tkfont.Font,
        label_font: tkfont.Font,
        icon: tk.PhotoImage | None = None,
        min_height: int = 140,
    ) -> None:
        super().__init__(
            master,
            bg=Theme.card,
            highlightbackground=Theme.border,
            highlightthickness=1,
            height=min_height,
        )
        self.grid_propagate(False)
        self.key = key
        self.unit = unit
        self.accent = Theme.metric_colors.get(key, Theme.accent)

        accent_bar = tk.Frame(self, bg=self.accent, height=3)
        accent_bar.pack(fill="x")

        body = tk.Frame(self, bg=Theme.card, padx=16, pady=14)
        body.pack(fill="both", expand=True)

        top = tk.Frame(body, bg=Theme.card)
        top.pack(fill="both", expand=True)

        self.icon_label = tk.Label(top, bg=Theme.card)
        if icon is not None:
            self.icon_label.configure(image=icon)
            self.icon_label.pack(anchor="w")

        self.value_label = tk.Label(
            top,
            text="—",
            fg=Theme.text,
            bg=Theme.card,
            font=value_font,
            anchor="w",
        )
        self.value_label.pack(anchor="w", pady=(8, 0))

        footer = tk.Frame(body, bg=Theme.card, height=self.FOOTER_HEIGHT)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self.title_label = tk.Label(
            footer,
            text=title,
            fg=Theme.text_secondary,
            bg=Theme.card,
            font=label_font,
            anchor="w",
        )
        self.title_label.pack(side="left", fill="y")

        self.unit_label = tk.Label(
            footer,
            text=unit,
            fg=Theme.text_muted,
            bg=Theme.card,
            font=label_font,
            anchor="e",
        )
        self.unit_label.pack(side="right", fill="y")

        bar_slot = tk.Frame(body, bg=Theme.card, height=self.BAR_HEIGHT)
        bar_slot.pack(fill="x", side="bottom", pady=(8, 0))
        bar_slot.pack_propagate(False)

        self.mod_bar: ttk.Progressbar | None = None
        if key == "burner_modulation":
            self.mod_bar = ttk.Progressbar(
                bar_slot,
                mode="determinate",
                maximum=100,
                style="Mod.Horizontal.TProgressbar",
            )
            self.mod_bar.pack(fill="both", expand=True)

    def set_value(self, text: str, modulation: float | None = None) -> None:
        self.value_label.configure(text=text, fg=Theme.text)
        if self.mod_bar is not None and modulation is not None:
            self.mod_bar["value"] = max(0, min(100, modulation))

    def set_placeholder(self) -> None:
        self.value_label.configure(text="—", fg=Theme.text_muted)
        if self.mod_bar is not None:
            self.mod_bar["value"] = 0


def configure_progressbar(root: tk.Misc) -> None:
    style = ttk.Style(root)
    style.configure(
        "Mod.Horizontal.TProgressbar",
        troughcolor=Theme.border,
        background=Theme.metric_colors["burner_modulation"],
        bordercolor=Theme.border,
        lightcolor=Theme.metric_colors["burner_modulation"],
        darkcolor=Theme.metric_colors["burner_modulation"],
        thickness=6,
    )
