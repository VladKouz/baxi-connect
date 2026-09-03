from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from baxi_connect.config import Secrets, Settings
from baxi_connect.ui.theme import Theme, apply_ttk_theme


class SettingsWindow(tk.Toplevel):
    def __init__(
        self,
        master: tk.Misc,
        secrets: Secrets,
        settings: Settings,
        on_save: Callable[[Secrets, Settings], None],
    ) -> None:
        super().__init__(master)
        self.title("Настройки")
        self.configure(bg=Theme.bg)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        apply_ttk_theme(self)
        self._on_save = on_save
        self._build(secrets, settings)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build(self, secrets: Secrets, settings: Settings) -> None:
        outer = tk.Frame(self, bg=Theme.bg, padx=22, pady=20)
        outer.grid(row=0, column=0, sticky="nsew")

        tk.Label(
            outer,
            text="Настройки",
            fg=Theme.text,
            bg=Theme.bg,
            font=(Theme.pick_font_family(self), 20, "bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        tk.Label(
            outer,
            text="Подключение к Zont API и параметры интерфейса",
            fg=Theme.text_secondary,
            bg=Theme.bg,
            font=(Theme.pick_font_family(self), 12),
            anchor="w",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 18))

        accent = tk.Frame(outer, bg=Theme.accent, height=3)
        accent.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 18))

        self.boiler_id_var = tk.StringVar(value=secrets.boiler_id)
        self.token_var = tk.StringVar(value=secrets.token)
        self.client_var = tk.StringVar(value=secrets.client)
        self.refresh_var = tk.StringVar(value=str(settings.refresh_interval_minutes))
        self.font_var = tk.StringVar(value=str(settings.font_size))

        self._add_section(outer, "Подключение", 3)
        self._add_labeled_entry(outer, "Boiler ID", self.boiler_id_var, 4)
        self._add_labeled_entry(outer, "Token", self.token_var, 5, show="•")
        self._add_labeled_entry(outer, "Client", self.client_var, 6)

        ttk.Separator(outer).grid(row=7, column=0, columnspan=2, sticky="ew", pady=18)

        self._add_section(outer, "Интерфейс", 8)
        self._add_labeled_entry(outer, "Интервал, мин", self.refresh_var, 9)
        self._add_labeled_entry(outer, "Размер шрифта", self.font_var, 10)

        buttons = ttk.Frame(outer, style="TFrame")
        buttons.grid(row=11, column=0, columnspan=2, sticky="e", pady=(22, 0))
        ttk.Button(buttons, text="Отмена", style="Ghost.TButton", command=self.destroy).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(buttons, text="Сохранить", style="Accent.TButton", command=self._save).pack(side="left")

        outer.columnconfigure(1, weight=1)

    def _add_section(self, parent: tk.Frame, title: str, row: int) -> None:
        ttk.Label(parent, text=title, style="Section.TLabel").grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 10)
        )

    def _add_labeled_entry(
        self,
        parent: tk.Frame,
        label: str,
        variable: tk.StringVar,
        row: int,
        show: str | None = None,
    ) -> None:
        ttk.Label(parent, text=label, style="Muted.TLabel").grid(row=row, column=0, sticky="w", pady=6)
        entry = ttk.Entry(parent, textvariable=variable, width=34, show=show)
        entry.grid(row=row, column=1, sticky="ew", padx=(16, 0), pady=6)

    def _save(self) -> None:
        try:
            refresh_minutes = max(1, int(self.refresh_var.get().strip()))
            font_size = max(12, int(self.font_var.get().strip()))
        except ValueError:
            messagebox.showerror("Ошибка", "Интервал и размер шрифта должны быть числами")
            return

        secrets = Secrets(
            boiler_id=self.boiler_id_var.get().strip(),
            token=self.token_var.get().strip(),
            client=self.client_var.get().strip(),
        )
        settings = Settings(
            refresh_interval_minutes=refresh_minutes,
            font_size=font_size,
        )

        if not secrets.boiler_id or not secrets.token or not secrets.client:
            messagebox.showerror("Ошибка", "Заполните все поля подключения")
            return

        self._on_save(secrets, settings)
        self.destroy()
