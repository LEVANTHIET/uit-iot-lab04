"""Chuẩn hóa và kiểm tra biên giá trị cảm biến trước khi gửi ThingsBoard."""

import math
from typing import Any


SENSOR_BOUNDS: dict[str, tuple[float, float]] = {
    "temperature": (-40.0, 85.0),
    "humidity": (0.0, 100.0),
    "illuminance": (0.0, 65535.0),
}

LED_KEYS: frozenset[str] = frozenset({"led1", "led2"})


def _parse_bool_led(key: str, value: Any) -> bool:
    """Chuyển đổi giá trị điều khiển đèn LED sang kiểu bool chuẩn."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value in (0, 1):
            return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "1", "on"):
            return True
        if lowered in ("false", "0", "off"):
            return False
    raise ValueError(f"Giá trị LED không hợp lệ cho '{key}': {value!r}")


def validate_sensor_value(key: str, value: Any) -> float | bool:
    """Kiểm tra tính hợp lệ của thông số cảm biến theo giới hạn vật lý."""
    if key in LED_KEYS:
        return _parse_bool_led(key, value)
    if key not in SENSOR_BOUNDS:
        raise ValueError(f"Khóa cảm biến không được hỗ trợ: {key}")
    if value is None or isinstance(value, bool):
        raise ValueError(f"Giá trị số không hợp lệ cho '{key}': {value!r}")
    numeric = float(value)
    if math.isnan(numeric) or math.isinf(numeric):
        raise ValueError(f"Giá trị '{key}' là NaN hoặc vô cực")
    low, high = SENSOR_BOUNDS[key]
    if numeric < low or numeric > high:
        raise ValueError(f"Giá trị '{key}'={numeric} nằm ngoài khoảng [{low}, {high}]")
    return round(numeric, 2)


def build_tb_telemetry_payload(
    values: dict[str, Any],
    ts_ms: int | None = None,
) -> dict[str, Any]:
    """Đóng gói bản tin telemetry chuẩn ThingsBoard từ từ điển giá trị thô."""
    if not values:
        raise ValueError("Danh sách thông số telemetry không được rỗng")
    normalized = {k: validate_sensor_value(k, v) for k, v in values.items()}
    if ts_ms is None:
        return normalized
    if ts_ms < 0:
        raise ValueError("Mốc thời gian ts_ms phải là số nguyên không âm")
    return {"ts": int(ts_ms), "values": normalized}
