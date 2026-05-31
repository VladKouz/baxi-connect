from __future__ import annotations

import tkinter as tk
from pathlib import Path

from baxi_connect.config import PROJECT_ROOT

ICON_DIR = PROJECT_ROOT / "assets" / "icons"

METRIC_ICON_FILES = {
    "temperature_boiler": "boiler.png",
    "burner_modulation": "modulation.png",
    "pressure": "pressure.png",
    "temperature_dhw": "dhw.png",
}

MODE_ICON_FILES = {
    "ночь": "night.png",
    "комфорт": "comfort.png",
    "эконом": "economy.png",
    "выключен": "off.png",
    "лето": "summer.png",
}


class IconCache:
    def __init__(self) -> None:
        self._refs: list[tk.PhotoImage] = []

    def load(self, filename: str, max_size: int = 32) -> tk.PhotoImage | None:
        path = ICON_DIR / filename
        if not path.exists():
            return None
        icon = tk.PhotoImage(file=str(path))
        if icon.width() > max_size or icon.height() > max_size:
            factor = max(icon.width() // max_size, icon.height() // max_size, 1)
            icon = icon.subsample(factor, factor)
        self._refs.append(icon)
        return icon

    def load_mode_icon(self, mode_name: str, max_size: int = 32) -> tk.PhotoImage | None:
        filename = MODE_ICON_FILES.get(mode_name.casefold())
        if not filename:
            return None
        return self.load(filename, max_size=max_size)

    def load_metric_icon(self, metric_key: str, max_size: int = 28) -> tk.PhotoImage | None:
        filename = METRIC_ICON_FILES.get(metric_key)
        if not filename:
            return None
        return self.load(filename, max_size=max_size)

    def clear(self) -> None:
        self._refs.clear()
