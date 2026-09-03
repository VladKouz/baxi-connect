from __future__ import annotations

import threading
import time
import tkinter as tk

from baxi_connect.config import Secrets, Settings, load_secrets, load_settings, save_secrets, save_settings
from baxi_connect.models import HeatingMode
from baxi_connect.ui.display_window import DisplayWindow
from baxi_connect.ui.settings_window import SettingsWindow
from baxi_connect.ui.theme import apply_ttk_theme
from baxi_connect.zont_api import ZontApiError, fetch_boiler_reading, set_heating_mode


class BaxiConnectApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        apply_ttk_theme(self.root)

        self.secrets = load_secrets()
        self.settings = load_settings()
        self._refresh_job: str | None = None
        self._countdown_job: str | None = None
        self._fetch_in_progress = False
        self._mode_change_in_progress = False
        self._device_id: int | None = None
        self._next_refresh_at: float | None = None
        self._has_reading = False

        self.display = DisplayWindow(
            self.root,
            font_size=self.settings.font_size,
            on_open_settings=self.open_settings,
            on_refresh=self.refresh_now,
            on_mode_change=self.change_mode,
            on_close=self.quit,
        )

        if not (self.secrets.boiler_id and self.secrets.token and self.secrets.client):
            self.root.after(200, self.open_settings)
        else:
            self.refresh_now()

    def quit(self) -> None:
        if self._refresh_job is not None:
            self.root.after_cancel(self._refresh_job)
            self._refresh_job = None
        if self._countdown_job is not None:
            self.root.after_cancel(self._countdown_job)
            self._countdown_job = None
        try:
            self.display.destroy()
        except tk.TclError:
            pass
        self.root.quit()
        self.root.destroy()

    def open_settings(self) -> None:
        SettingsWindow(
            self.display,
            secrets=self.secrets,
            settings=self.settings,
            on_save=self._apply_settings,
        )

    def _apply_settings(self, secrets: Secrets, settings: Settings) -> None:
        self.secrets = secrets
        self.settings = settings
        save_secrets(secrets)
        save_settings(settings)
        self.display.set_font_size(settings.font_size)
        self._schedule_refresh()
        self.refresh_now()

    def change_mode(self, mode: HeatingMode) -> None:
        if self._mode_change_in_progress or self._fetch_in_progress:
            return
        if self._device_id is None:
            self.display.show_error("ID устройства ещё не загружен")
            return

        self._mode_change_in_progress = True
        self.display.set_mode_busy(True)
        secrets = Secrets(
            boiler_id=self.secrets.boiler_id,
            token=self.secrets.token,
            client=self.secrets.client,
        )
        device_id = self._device_id

        def worker() -> None:
            try:
                set_heating_mode(secrets, device_id, mode.id)
                self.root.after(0, self._after_mode_change_success)
            except ZontApiError as exc:
                message = str(exc)
                self.root.after(0, lambda: self._after_mode_change_error(message))

        threading.Thread(target=worker, daemon=True).start()

    def _after_mode_change_success(self) -> None:
        self._mode_change_in_progress = False
        self.refresh_now()

    def _after_mode_change_error(self, message: str) -> None:
        self._mode_change_in_progress = False
        self.display.set_mode_busy(False)
        self.display.show_error(message)

    def refresh_now(self) -> None:
        if self._fetch_in_progress:
            return

        self._fetch_in_progress = True
        self.display.show_loading(silent=self._has_reading)
        secrets = Secrets(
            boiler_id=self.secrets.boiler_id,
            token=self.secrets.token,
            client=self.secrets.client,
        )

        def worker() -> None:
            try:
                reading = fetch_boiler_reading(secrets)
                self.root.after(0, lambda: self._on_reading_success(reading))
            except ZontApiError as exc:
                message = str(exc)
                self.root.after(0, lambda: self._on_reading_error(message))
            except Exception as exc:  # noqa: BLE001 — show any unexpected error in UI
                message = f"Неожиданная ошибка: {exc}"
                self.root.after(0, lambda: self._on_reading_error(message))

        threading.Thread(target=worker, daemon=True).start()

    def _on_reading_success(self, reading) -> None:
        self._fetch_in_progress = False
        self._mode_change_in_progress = False
        self._device_id = reading.device_id
        self._has_reading = True
        self.display.show_reading(reading)
        self._schedule_refresh()

    def _on_reading_error(self, message: str) -> None:
        self._fetch_in_progress = False
        self._mode_change_in_progress = False
        self.display.show_error(message)
        self._schedule_refresh()

    def _schedule_refresh(self) -> None:
        if self._refresh_job is not None:
            self.root.after_cancel(self._refresh_job)

        interval_ms = self.settings.refresh_interval_minutes * 60 * 1000
        self._next_refresh_at = time.monotonic() + (interval_ms / 1000)
        self._refresh_job = self.root.after(interval_ms, self.refresh_now)
        self._tick_countdown()

    def _tick_countdown(self) -> None:
        if self._countdown_job is not None:
            self.root.after_cancel(self._countdown_job)
            self._countdown_job = None

        if self._next_refresh_at is None:
            self.display.set_next_refresh(None)
            return

        remaining = int(round(self._next_refresh_at - time.monotonic()))
        self.display.set_next_refresh(remaining)
        self._countdown_job = self.root.after(1000, self._tick_countdown)

    def run(self) -> None:
        self.root.mainloop()


def run_app() -> None:
    BaxiConnectApp().run()
