from __future__ import annotations

from datetime import datetime, timezone

import requests

from baxi_connect.config import Secrets
from baxi_connect.models import BoilerReading, HeatingMode

ZONT_API_URL = "https://my.zont.online/api/devices"
ZONT_COMMAND_URL = "https://my.zont.online/api/send_z3k_command"


class ZontApiError(Exception):
    pass


def _api_headers(secrets: Secrets) -> dict[str, str]:
    return {
        "X-ZONT-Client": secrets.client,
        "X-ZONT-Token": secrets.token,
        "Content-Type": "application/json",
    }


def _post_json(url: str, secrets: Secrets, payload: dict) -> dict:
    try:
        response = requests.post(url, json=payload, headers=_api_headers(secrets), timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise ZontApiError(f"Ошибка сети: {exc}") from exc

    if not data.get("ok"):
        error = data.get("error_ui") or data.get("error") or "Неизвестная ошибка"
        raise ZontApiError(str(error))
    return data


def _find_device(devices: list[dict], boiler_id: str) -> dict:
    needle = boiler_id.strip().casefold()
    for device in devices:
        serial = str(device.get("serial") or "").strip()
        if serial.casefold() == needle:
            return device
        name = str(device.get("name") or "").strip()
        if name.casefold() == needle:
            return device
    raise ZontApiError(f"Устройство «{boiler_id}» не найдено")


def _device_id(device: dict) -> int:
    device_id = device.get("id") or device.get("device_id")
    if device_id is None:
        raise ZontApiError("Не удалось определить ID устройства")
    return int(device_id)


def _load_modes(device: dict) -> list[HeatingMode]:
    modes: list[HeatingMode] = []
    for mode in (device.get("z3k_config") or {}).get("heating_modes") or []:
        if "id" not in mode or not mode.get("name"):
            continue
        modes.append(
            HeatingMode(
                id=int(mode["id"]),
                name=str(mode["name"]),
                position=int(mode.get("position") or 0),
            )
        )
    modes.sort(key=lambda item: (item.position, item.name.casefold()))
    return modes


def _find_opentherm_entry(z3k_state: dict) -> tuple[dict | None, dict]:
    """Return (ot_block, adapter_entry)."""
    for value in z3k_state.values():
        if not isinstance(value, dict):
            continue
        ot = value.get("ot")
        if isinstance(ot, dict) and any(key in ot for key in ("bt", "rml", "wp", "dt")):
            return ot, value
    return None, {}


def _resolve_current_mode(device: dict, z3k_state: dict) -> tuple[int | None, str]:
    modes = {mode.id: mode.name for mode in _load_modes(device)}
    circuits = (device.get("z3k_config") or {}).get("heating_circuits") or []

    preferred = []
    others = []
    for circuit in circuits:
        name = str(circuit.get("name") or "").casefold()
        if "отопл" in name:
            preferred.append(circuit)
        else:
            others.append(circuit)

    for circuit in preferred + others:
        circuit_id = str(circuit.get("id"))
        state = z3k_state.get(circuit_id)
        if not isinstance(state, dict):
            continue
        mode_id = state.get("mode_id")
        if mode_id in modes:
            return int(mode_id), modes[mode_id]

    for state in z3k_state.values():
        if isinstance(state, dict):
            mode_id = state.get("mode_id")
            if mode_id in modes:
                return int(mode_id), modes[mode_id]

    return None, "—"


def fetch_boiler_reading(secrets: Secrets) -> BoilerReading:
    if not secrets.boiler_id or not secrets.token or not secrets.client:
        raise ZontApiError("Заполните настройки подключения (⚙)")

    payload = _post_json(ZONT_API_URL, secrets, {"load_io": True})
    device = _find_device(payload.get("devices") or [], secrets.boiler_id)
    io = device.get("io") or {}
    z3k_state = io.get("z3k-state") or {}
    ot, adapter = _find_opentherm_entry(z3k_state)

    if ot is None:
        raise ZontApiError("Данные OpenTherm не найдены")

    mode_id, mode_name = _resolve_current_mode(device, z3k_state)
    flags = [str(flag) for flag in (ot.get("s") or [])]
    adapter_status = adapter.get("status") or {}
    connection = io.get("connection-state") or {}

    return BoilerReading(
        device_id=_device_id(device),
        mode_id=mode_id,
        mode_name=mode_name,
        modes=_load_modes(device),
        temperature_boiler=ot.get("bt"),
        burner_modulation=ot.get("rml"),
        pressure=ot.get("wp"),
        temperature_dhw=ot.get("dt"),
        updated_at=datetime.now(timezone.utc).astimezone(),
        online=bool(device.get("online")),
        burner_on="fl" in flags,
        heating_on="ch" in flags,
        dhw_on="dhw" in flags,
        boiler_fail=bool(adapter_status.get("boiler_fail") or "f" in flags),
        connection_channel=connection.get("connection_channel"),
        ot_flags=flags,
    )


def set_heating_mode(secrets: Secrets, device_id: int, mode_id: int) -> None:
    _post_json(
        ZONT_COMMAND_URL,
        secrets,
        {
            "device_id": device_id,
            "object_id": mode_id,
            "command_name": "SelectHeatingMode",
            "command_args": None,
            "is_guaranteed": True,
        },
    )
