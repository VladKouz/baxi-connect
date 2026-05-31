from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

from baxi_connect.models import HeatingMode
from baxi_connect.ui.icons import IconCache
from baxi_connect.ui.theme import Theme


class ModeChip(tk.Frame):
    HEIGHT = 112

    def __init__(
        self,
        master: tk.Misc,
        mode: HeatingMode,
        icon: tk.PhotoImage | None,
        label_font: tkfont.Font,
        command: Callable[[HeatingMode], None],
    ) -> None:
        self._idle_bg = Theme.surface
        super().__init__(
            master,
            bg=self._idle_bg,
            height=self.HEIGHT,
            highlightthickness=2,
            highlightbackground=Theme.border,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self.mode = mode
        self._icon = icon
        self._label_font = label_font
        self._command = command
        self._active = False
        self._hover = False
        self._busy = False
        self._color = Theme.mode_color(mode.name)

        self.accent_bar = tk.Frame(self, bg=self._color, height=3)
        self.accent_bar.pack(fill="x")

        self.inner = tk.Frame(self, bg=self._idle_bg)
        self.inner.pack(fill="both", expand=True, padx=6, pady=8)
        self.inner.grid_columnconfigure(0, weight=1)

        self.icon_label = tk.Label(self.inner, bg=self._idle_bg)
        if icon is not None:
            self.icon_label.configure(image=icon)
        self.icon_label.grid(row=0, column=0, pady=(0, 4))

        self.name_label = tk.Label(
            self.inner,
            text=mode.name,
            fg=Theme.text_secondary,
            bg=self._idle_bg,
            font=label_font,
            wraplength=64,
            justify="center",
        )
        self.name_label.grid(row=1, column=0, sticky="ew")

        self.dot = tk.Label(self.inner, text="", bg=self._idle_bg, font=("", 8))
        self.dot.grid(row=2, column=0, pady=(4, 0))

        for widget in (self, self.inner, self.icon_label, self.name_label, self.dot):
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.configure(cursor="hand2")

        self.update_style()

    def set_active(self, active: bool) -> None:
        self._active = active
        self.update_style()

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        cursor = "watch" if busy else "hand2"
        for widget in (self, self.inner, self.icon_label, self.name_label, self.dot):
            widget.configure(cursor=cursor)
        self.update_style()

    def set_wraplength(self, width: int) -> None:
        self.name_label.configure(wraplength=max(52, width - 12))

    def _on_click(self, _event: tk.Event) -> None:
        if self._busy or self._active:
            return
        self._command(self.mode)

    def _on_enter(self, _event: tk.Event) -> None:
        if not self._active and not self._busy:
            self._hover = True
            self.update_style()

    def _on_leave(self, _event: tk.Event) -> None:
        self._hover = False
        self.update_style()

    def _blend(self, color_a: str, color_b: str, ratio: float) -> str:
        def hex_to_rgb(value: str) -> tuple[int, int, int]:
            value = value.lstrip("#")
            return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)

        ar, ag, ab = hex_to_rgb(color_a)
        br, bg, bb = hex_to_rgb(color_b)
        r = int(ar * (1 - ratio) + br * ratio)
        g = int(ag * (1 - ratio) + bg * ratio)
        b = int(ab * (1 - ratio) + bb * ratio)
        return f"#{r:02x}{g:02x}{b:02x}"

    def update_style(self) -> None:
        if self._active:
            bg = self._blend(self._color, Theme.card, 0.78)
            border = self._color
            text = Theme.text
            dot = "●"
            dot_fg = self._color
        elif self._hover and not self._busy:
            bg = Theme.card_hover
            border = Theme.border
            text = Theme.text
            dot = ""
            dot_fg = Theme.text_muted
        else:
            bg = self._idle_bg
            border = Theme.border
            text = Theme.text_secondary
            dot = ""
            dot_fg = Theme.text_muted

        self._idle_bg = bg
        self.configure(bg=bg, highlightbackground=border)
        self.inner.configure(bg=bg)
        self.icon_label.configure(bg=bg)
        self.name_label.configure(fg=text, bg=bg)
        self.dot.configure(text=dot, fg=dot_fg, bg=bg)


class ModeSelector(tk.Frame):
    CHIP_GAP = 6
    ROW_HEIGHT = ModeChip.HEIGHT

    def __init__(
        self,
        master: tk.Misc,
        on_mode_change: Callable[[HeatingMode], None],
    ) -> None:
        super().__init__(master, bg=Theme.card, highlightbackground=Theme.border, highlightthickness=1)
        self._on_mode_change = on_mode_change
        self._family = Theme.pick_font_family(self)
        self._label_font = tkfont.Font(family=self._family, size=12)
        self._title_font = tkfont.Font(family=self._family, size=12, weight="bold")
        self._hint_font = tkfont.Font(family=self._family, size=11)
        self._chips: list[ModeChip] = []
        self._icons = IconCache()
        self._layout_job: str | None = None
        self._build_shell()

    def _build_shell(self) -> None:
        accent = tk.Frame(self, bg=Theme.accent, height=3)
        accent.pack(fill="x")

        body = tk.Frame(self, bg=Theme.card, padx=12, pady=10)
        body.pack(fill="x")

        header = tk.Frame(body, bg=Theme.card)
        header.pack(fill="x", pady=(0, 8))

        tk.Label(
            header,
            text="Режим отопления",
            fg=Theme.text,
            bg=Theme.card,
            font=self._title_font,
            anchor="w",
        ).pack(side="left")

        self.hint_label = tk.Label(
            header,
            text="нажмите для смены",
            fg=Theme.text_muted,
            bg=Theme.card,
            font=self._hint_font,
            anchor="e",
        )
        self.hint_label.pack(side="right")

        self.chips_host = tk.Frame(body, bg=Theme.card, height=self.ROW_HEIGHT)
        self.chips_host.pack(fill="x")
        self.chips_host.pack_propagate(False)

        self.chips_frame = tk.Frame(self.chips_host, bg=Theme.card)
        self.chips_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.chips_frame.bind("<Configure>", self._schedule_layout)

    def _schedule_layout(self, _event: tk.Event | None = None) -> None:
        if self._layout_job is not None:
            self.after_cancel(self._layout_job)
        self._layout_job = self.after(30, self._relayout_chips)

    def _relayout_chips(self) -> None:
        self._layout_job = None
        if not self._chips:
            return

        count = len(self._chips)
        width = max(self.chips_frame.winfo_width(), count * 64)
        chip_width = max(64, (width - self.CHIP_GAP * (count - 1)) // count)

        for col in range(count):
            self.chips_frame.grid_columnconfigure(col, weight=1, uniform="mode_chip")
        self.chips_frame.grid_rowconfigure(0, weight=1)

        for index, chip in enumerate(self._chips):
            padx = (0, self.CHIP_GAP) if index < count - 1 else (0, 0)
            chip.grid(row=0, column=index, sticky="nsew", padx=padx)
            chip.set_wraplength(chip_width)

    def set_modes(self, modes: list[HeatingMode], active_mode_id: int | None) -> None:
        for chip in self._chips:
            chip.grid_forget()
            chip.destroy()
        self._chips.clear()
        self._icons.clear()

        for mode in modes:
            chip = ModeChip(
                self.chips_frame,
                mode=mode,
                icon=self._icons.load_mode_icon(mode.name, max_size=30),
                label_font=self._label_font,
                command=self._on_mode_change,
            )
            chip.set_active(mode.id == active_mode_id)
            self._chips.append(chip)

        self._schedule_layout()

    def set_active_mode(self, mode_id: int | None) -> None:
        for chip in self._chips:
            chip.set_active(chip.mode.id == mode_id)

    def set_busy(self, busy: bool) -> None:
        self.hint_label.configure(text="смена режима…" if busy else "нажмите для смены")
        for chip in self._chips:
            chip.set_busy(busy)

    def set_loading(self) -> None:
        for chip in self._chips:
            chip.set_busy(True)
        self.hint_label.configure(text="загрузка…")
