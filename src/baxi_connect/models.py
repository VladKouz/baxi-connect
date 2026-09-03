from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class HeatingMode:
    id: int
    name: str
    position: int = 0


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
    online: bool = False
    burner_on: bool = False
    heating_on: bool = False
    dhw_on: bool = False
    boiler_fail: bool = False
    connection_channel: str | None = None
    error: str | None = None
    ot_flags: list[str] = field(default_factory=list)

    @property
    def is_ok(self) -> bool:
        return self.error is None

    @property
    def status_summary(self) -> str:
        parts: list[str] = []
        if self.boiler_fail:
            parts.append("авария")
        elif not self.online:
            parts.append("офлайн")
        else:
            parts.append("онлайн")
        if self.burner_on:
            parts.append("горелка")
        if self.heating_on:
            parts.append("отопление")
        if self.dhw_on:
            parts.append("ГВС")
        if self.connection_channel:
            parts.append(self.connection_channel)
        return " · ".join(parts)
