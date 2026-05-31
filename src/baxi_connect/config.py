from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SECRETS_PATH = PROJECT_ROOT / "secrets.json"
SETTINGS_PATH = PROJECT_ROOT / "settings.json"


@dataclass
class Secrets:
    boiler_id: str = ""
    token: str = ""
    client: str = ""


@dataclass
class Settings:
    refresh_interval_minutes: int = 10
    font_size: int = 28


def load_secrets() -> Secrets:
    if not SECRETS_PATH.exists():
        secrets = Secrets()
        save_secrets(secrets)
        return secrets

    data = json.loads(SECRETS_PATH.read_text(encoding="utf-8"))
    return Secrets(
        boiler_id=str(data.get("boiler_id", Secrets.boiler_id)),
        token=str(data.get("token", Secrets.token)),
        client=str(data.get("client", Secrets.client)),
    )


def save_secrets(secrets: Secrets) -> None:
    SECRETS_PATH.write_text(
        json.dumps(asdict(secrets), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_settings() -> Settings:
    if not SETTINGS_PATH.exists():
        settings = Settings()
        save_settings(settings)
        return settings

    data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    return Settings(
        refresh_interval_minutes=max(1, int(data.get("refresh_interval_minutes", 10))),
        font_size=max(12, int(data.get("font_size", 28))),
    )


def save_settings(settings: Settings) -> None:
    SETTINGS_PATH.write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
