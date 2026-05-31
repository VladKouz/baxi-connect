from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

from baxi_connect.models import BoilerReading, HeatingMode
from baxi_connect.ui.icons import IconCache
from baxi_connect.ui.mode_selector import ModeSelector
from baxi_connect.ui.theme import IconButton, MetricCard, Theme, configure_progressbar

APP_TITLE = "Baxi Connect (Custom edition)"
DEFAULT_WIDTH = 540
DEFAULT_HEIGHT = 760
METRIC_MIN_HEIGHT = 150


class DisplayWindow(tk.Toplevel):
    def __init__(
        self,
        master: tk.Misc,
        font_size: int,
        on_open_settings: Callable[[], None],
        on_refresh: Callable[[], None],
        on_mode_change: Callable[[HeatingMode], None],
    ) -> None:
        super().__init__(master)
        self.title(APP_TITLE)
        self.configure(bg=Theme.bg)
        self.attributes("-topmost", True)
        self.resizable(True, True)
        self.minsize(460, 680)

        self._on_open_settings = on_open_settings
        self._on_refresh = on_refresh
        self._on_mode_change = on_mode_change
        self._drag_x = 0
        self._drag_y = 0
        self._font_size = font_size
        self._family = Theme.pick_font_family(self)
        self._metric_icons = IconCache()

        configure_progressbar(self)
        self._build_fonts()
        self._build()
        self._bind_drag()
        self.after(0, self._apply_initial_geometry)

    def _apply_initial_geometry(self) -> None:
        self.update_idletasks()
        width = max(DEFAULT_WIDTH, self.winfo_reqwidth())
        height = max(DEFAULT_HEIGHT, self.winfo_reqheight())
        self.geometry(f"{width}x{height}+80+60")

    def _build_fonts(self) -> None:
        label_size = max(12, self._font_size - 10)
        self._brand_font = tkfont.Font(family=self._family, size=12, weight="bold")
        self._edition_font = tkfont.Font(family=self._family, size=10)
        self._subtitle_font = tkfont.Font(family=self._family, size=13)
        self._value_font = tkfont.Font(family=self._family, size=self._font_size, weight="bold")
        self._label_font = tkfont.Font(family=self._family, size=label_size)
        self._meta_font = tkfont.Font(family=self._family, size=label_size)

    def _build(self) -> None:
        shell = tk.Frame(self, bg=Theme.bg, padx=16, pady=14)
        shell.pack(fill="both", expand=True)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(3, weight=1)

        accent = tk.Frame(shell, bg=Theme.accent, height=4)
        accent.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        header = tk.Frame(shell, bg=Theme.bg)
        header.grid(row=1, column=0, sticky="ew")

        brand_wrap = tk.Frame(header, bg=Theme.bg)
        brand_wrap.pack(side="left", fill="x", expand=True)

        title_row = tk.Frame(brand_wrap, bg=Theme.bg)
        title_row.pack(anchor="w")

        tk.Label(
            title_row,
            text="Baxi Connect",
            fg=Theme.accent,
            bg=Theme.bg,
            font=self._brand_font,
            anchor="w",
        ).pack(side="left")

        tk.Label(
            title_row,
            text="(Custom edition)",
            fg=Theme.text_muted,
            bg=Theme.bg,
            font=self._edition_font,
            anchor="w",
        ).pack(side="left", padx=(8, 0), pady=(2, 0))

        self.subtitle_label = tk.Label(
            brand_wrap,
            text="Мониторинг котла",
            fg=Theme.text_secondary,
            bg=Theme.bg,
            font=self._subtitle_font,
            anchor="w",
        )
        self.subtitle_label.pack(anchor="w", pady=(6, 0))

        actions = tk.Frame(header, bg=Theme.bg)
        actions.pack(side="right")
        IconButton(actions, "↻", self._on_refresh).pack(side="left", padx=(0, 8))
        IconButton(actions, "⚙", self._on_open_settings).pack(side="left")

        self.mode_selector = ModeSelector(shell, on_mode_change=self._on_mode_change)
        self.mode_selector.grid(row=2, column=0, sticky="new", pady=(12, 0))

        grid = tk.Frame(shell, bg=Theme.bg)
        grid.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        grid.grid_columnconfigure(0, weight=1, uniform="metric_col")
        grid.grid_columnconfigure(1, weight=1, uniform="metric_col")
        grid.grid_rowconfigure(0, weight=1, uniform="metric_row")
        grid.grid_rowconfigure(1, weight=1, uniform="metric_row")

        self.cards: dict[str, MetricCard] = {}
        metrics = [
            ("temperature_boiler", "Теплоноситель", "°C", 0, 0),
            ("burner_modulation", "Модуляция", "%", 0, 1),
            ("pressure", "Давление", "бар", 1, 0),
            ("temperature_dhw", "ГВС", "°C", 1, 1),
        ]

        for key, title, unit, row, col in metrics:
            card = MetricCard(
                grid,
                key=key,
                title=title,
                unit=unit,
                value_font=self._value_font,
                label_font=self._label_font,
                icon=self._metric_icons.load_metric_icon(key, max_size=32),
                min_height=METRIC_MIN_HEIGHT,
            )
            card.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
            self.cards[key] = card

        footer = tk.Frame(shell, bg=Theme.bg)
        footer.grid(row=4, column=0, sticky="ew", pady=(10, 0))

        self.status_dot = tk.Label(footer, text="●", fg=Theme.text_muted, bg=Theme.bg, font=self._meta_font)
        self.status_dot.pack(side="left")

        self.status_label = tk.Label(
            footer,
            text="Запрос данных…",
            fg=Theme.text_muted,
            bg=Theme.bg,
            font=self._meta_font,
            anchor="w",
        )
        self.status_label.pack(side="left", padx=(6, 0))

    def set_font_size(self, font_size: int) -> None:
        self._font_size = font_size
        self._build_fonts()
        self.subtitle_label.configure(font=self._subtitle_font)
        self.status_label.configure(font=self._meta_font)
        for card in self.cards.values():
            card.value_label.configure(font=self._value_font)
            card.title_label.configure(font=self._label_font)
            card.unit_label.configure(font=self._label_font)

    def set_mode_busy(self, busy: bool) -> None:
        self.mode_selector.set_busy(busy)

    def _bind_drag(self) -> None:
        draggable = [self.subtitle_label, self.status_label, *self.cards.values()]
        for widget in draggable:
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._do_drag)
            for child in widget.winfo_children():
                child.bind("<ButtonPress-1>", self._start_drag)
                child.bind("<B1-Motion>", self._do_drag)

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _do_drag(self, event: tk.Event) -> None:
        self.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    @staticmethod
    def _format_number(value: float | None, decimals: int) -> str:
        if value is None:
            return "—"
        return f"{value:.{decimals}f}"

    def show_loading(self) -> None:
        self.subtitle_label.configure(text="Обновление данных…", fg=Theme.text_secondary)
        self.mode_selector.set_loading()
        for card in self.cards.values():
            card.set_placeholder()
        self.status_dot.configure(fg=Theme.warning)
        self.status_label.configure(text="Запрос данных…", fg=Theme.text_muted)

    def show_error(self, message: str) -> None:
        self.subtitle_label.configure(text="Нет связи с котлом", fg=Theme.danger)
        self.mode_selector.set_busy(False)
        self.status_dot.configure(fg=Theme.danger)
        self.status_label.configure(text=message, fg=Theme.danger)

    def show_reading(self, reading: BoilerReading) -> None:
        color = Theme.mode_color(reading.mode_name)
        self.subtitle_label.configure(text=f"Сейчас: {reading.mode_name}", fg=color)
        self.mode_selector.set_modes(reading.modes, reading.mode_id)
        self.mode_selector.set_busy(False)

        self.cards["temperature_boiler"].set_value(
            self._format_number(reading.temperature_boiler, 1)
        )
        modulation = reading.burner_modulation
        self.cards["burner_modulation"].set_value(
            self._format_number(modulation, 0),
            modulation=modulation,
        )
        self.cards["pressure"].set_value(self._format_number(reading.pressure, 2))
        self.cards["temperature_dhw"].set_value(self._format_number(reading.temperature_dhw, 1))

        updated = reading.updated_at.strftime("%d.%m.%Y %H:%M")
        self.status_dot.configure(fg=Theme.success)
        self.status_label.configure(text=f"Обновлено {updated}", fg=Theme.text_secondary)
