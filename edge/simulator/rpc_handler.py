"""Bộ xử lý lệnh RPC điều khiển 2 đèn LED theo thời gian thực."""

from typing import Any

from common.constants import RPC_GET_LED1, RPC_GET_LED2, RPC_SET_LED1, RPC_SET_LED2


def _coerce_bool(params: Any) -> bool:
    """Chuẩn hóa tham số RPC sang kiểu boolean bật/tắt."""
    if isinstance(params, bool):
        return params
    if isinstance(params, (int, float)):
        return bool(params)
    if isinstance(params, str):
        return params.strip().lower() in ("true", "1", "on")
    if isinstance(params, dict):
        if "state" in params:
            return _coerce_bool(params["state"])
        if "enabled" in params:
            return _coerce_bool(params["enabled"])
    return False


def handle_led_rpc(
    method: str,
    params: Any,
    led_state: dict[str, bool],
) -> tuple[dict[str, bool], bool]:
    """Xử lý RPC setLed1/getLed1/setLed2/getLed2 rồi trả về trạng thái mới."""
    updated = dict(led_state)
    if method == RPC_SET_LED1:
        updated["led1"] = _coerce_bool(params)
        return updated, updated["led1"]
    if method == RPC_GET_LED1:
        return updated, updated.get("led1", False)
    if method == RPC_SET_LED2:
        updated["led2"] = _coerce_bool(params)
        return updated, updated["led2"]
    if method == RPC_GET_LED2:
        return updated, updated.get("led2", False)
    if method == "setValue":
        updated["led1"] = _coerce_bool(params)
        return updated, updated["led1"]
    if method == "getValue":
        return updated, updated.get("led1", False)
    raise ValueError(f"Phương thức RPC không được hỗ trợ: {method}")
