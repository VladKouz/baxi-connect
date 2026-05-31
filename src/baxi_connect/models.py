from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HeatingMode:
    id: int
    name: str


@dataclass
class BoilerReading:
    device_id: int
    mode_id: int | None
    mode_name: str
    modes: list[HeatingMode]
    temperature_boiler: float | None
    burner_modulation: float | None
    pressure: float | None
    temperature_dhw: float | None
    updated_at: datetime
    error: str | None = None

    @property
    def is_ok(self) -> bool:
        return self.error is None
