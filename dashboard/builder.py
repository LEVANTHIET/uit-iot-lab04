"""Đóng gói Custom Widget Bundle và cấu hình Dashboard chuẩn ThingsBoard CE."""

import json
from pathlib import Path
from typing import Any

from common.constants import NODE1_SPEC, NODE2_SPEC
from dashboard.widget_defs import (
    make_entities_table_widget,
    make_led_switch_widget,
    make_line_chart_widget,
    make_logs_custom_widget,
    make_value_card_widget,
)


WIDGETS_DIR = Path(__file__).resolve().parent / "widgets"
BUNDLE_ALIAS = "uit_lab04"
CUSTOM_WIDGET_ALIAS = "uit_lab04_system_logs_export"
DASHBOARD_TITLE = "UIT Lab 04 - Giám Sát & Điều Khiển Hệ Thống IoT (2x ESP32)"

DEFAULT_WIDGET_FQNS: dict[str, str] = {
    "entities_table": "system.entity_widgets.entities_table",
    "value_card": "system.cards.simple_card",
    "switch_control": "system.control_widgets.switch_control",
    "line_chart": "system.charts.basic_timeseries",
    "logs_custom": f"{BUNDLE_ALIAS}.{CUSTOM_WIDGET_ALIAS}",
}


def _read_widget_asset(filename: str) -> str:
    """Đọc tệp HTML/CSS/JS của Custom Widget từ thư mục widgets."""
    return (WIDGETS_DIR / filename).read_text(encoding="utf-8")


def build_widget_bundle_payload(bundle_alias: str = BUNDLE_ALIAS) -> dict[str, Any]:
    """Tạo cấu hình Widgets Bundle chứa Custom Widget của Lab 04."""
    return {
        "alias": bundle_alias,
        "title": "UIT Lab 04 Custom Widgets",
        "description": "Bộ widget tùy biến bảng nhật ký 5 trường kèm lọc và xuất CSV/Excel.",
    }


def build_custom_widget_payload(bundle_alias: str = BUNDLE_ALIAS) -> dict[str, Any]:
    """Tạo payload đăng ký Custom Widget Type lên API /api/widgetType của ThingsBoard."""
    descriptor = {
        "type": "timeseries",
        "sizeX": 12,
        "sizeY": 7,
        "resources": [],
        "templateHtml": _read_widget_asset("logs_export_widget.html"),
        "templateCss": _read_widget_asset("logs_export_widget.css"),
        "controllerScript": _read_widget_asset("logs_export_widget.js"),
        "settingsSchema": "{}",
        "dataKeySettingsSchema": "{}",
        "defaultConfig": json.dumps(
            {
                "datasources": [],
                "timewindow": {"realtime": {"timewindowMs": 900000}},
                "showTitle": False,
                "title": "Nhật ký hệ thống",
            },
            ensure_ascii=False,
        ),
    }
    return {
        "fqn": f"{bundle_alias}.{CUSTOM_WIDGET_ALIAS}",
        "name": "UIT Lab 04 System Logs & CSV/Excel Export",
        "deprecated": False,
        "descriptor": descriptor,
    }


def _find_matching_fqn(infos: list[dict[str, Any]], candidates: tuple[str, ...]) -> str | None:
    """Tìm FQN widget khớp nhất từ danh sách widgetTypesInfos của ThingsBoard."""
    fqns = [str(item.get("fqn", "")) for item in infos if item.get("fqn")]
    for candidate in candidates:
        for fqn in fqns:
            if fqn == candidate or fqn.endswith(f".{candidate}"):
                return fqn
    return None


def resolve_widget_fqns(widget_infos: list[dict[str, Any]]) -> dict[str, str]:
    """Ánh xạ các widget gốc đang có sẵn trên phiên bản ThingsBoard thực tế."""
    resolved = dict(DEFAULT_WIDGET_FQNS)
    candidates_map: dict[str, tuple[str, ...]] = {
        "entities_table": ("system.entity_widgets.entities_table", "entities_table"),
        "value_card": ("system.cards.simple_card", "system.cards.value_card", "value_card", "simple_card"),
        "switch_control": ("system.control_widgets.switch_control", "switch_control", "rpc_button"),
        "line_chart": ("system.charts.basic_timeseries", "system.charts.timeseries_line_chart", "basic_timeseries"),
    }
    for key, candidates in candidates_map.items():
        match = _find_matching_fqn(widget_infos, candidates)
        if match:
            resolved[key] = match
    return resolved


def _build_entity_aliases(node1_id: str, node2_id: str) -> dict[str, Any]:
    """Tạo cấu trúc entityAliases trỏ tới hai mạch ESP32 trên ThingsBoard."""
    return {
        "alias_all_devices": {
            "id": "alias_all_devices",
            "alias": "Tất cả ESP32 Lab 04",
            "filter": {
                "type": "entityList",
                "entityType": "DEVICE",
                "entityList": [node1_id, node2_id],
                "resolveMultiple": True,
            },
        },
        "alias_node1": {
            "id": "alias_node1",
            "alias": NODE1_SPEC.name,
            "filter": {"type": "singleEntity", "singleEntity": {"entityType": "DEVICE", "id": node1_id}},
        },
        "alias_node2": {
            "id": "alias_node2",
            "alias": NODE2_SPEC.name,
            "filter": {"type": "singleEntity", "singleEntity": {"entityType": "DEVICE", "id": node2_id}},
        },
    }


def _build_layout_positions() -> dict[str, dict[str, int]]:
    """Định vị lưới 24 cột cho toàn bộ widget trên Dashboard."""
    return {
        "w_devices": {"col": 0, "row": 0, "sizeX": 24, "sizeY": 4},
        "w_temp_card": {"col": 0, "row": 4, "sizeX": 4, "sizeY": 3},
        "w_humid_card": {"col": 4, "row": 4, "sizeX": 4, "sizeY": 3},
        "w_lux_card": {"col": 8, "row": 4, "sizeX": 4, "sizeY": 3},
        "w_led1_rpc": {"col": 12, "row": 4, "sizeX": 6, "sizeY": 3},
        "w_led2_rpc": {"col": 18, "row": 4, "sizeX": 6, "sizeY": 3},
        "w_chart_temp": {"col": 0, "row": 7, "sizeX": 8, "sizeY": 5},
        "w_chart_humid": {"col": 8, "row": 7, "sizeX": 8, "sizeY": 5},
        "w_chart_lux": {"col": 16, "row": 7, "sizeX": 8, "sizeY": 5},
        "w_logs_table": {"col": 0, "row": 12, "sizeX": 24, "sizeY": 7},
    }


def build_dashboard_payload(
    node1_id: str,
    node2_id: str,
    widget_fqns: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Tạo JSON Dashboard hoàn chỉnh đáp ứng đủ 7 yêu cầu Lab 04 trong ThingsBoard."""
    fqns = widget_fqns or DEFAULT_WIDGET_FQNS
    widgets = {
        "w_devices": make_entities_table_widget("w_devices", "alias_all_devices", fqns["entities_table"]),
        "w_temp_card": make_value_card_widget("w_temp_card", "alias_node2", "Nhiệt độ", "temperature", "°C", "#ef4444", fqns["value_card"]),
        "w_humid_card": make_value_card_widget("w_humid_card", "alias_node2", "Độ ẩm", "humidity", "%", "#3b82f6", fqns["value_card"]),
        "w_lux_card": make_value_card_widget("w_lux_card", "alias_node1", "Ánh sáng", "illuminance", "lx", "#f59e0b", fqns["value_card"]),
        "w_led1_rpc": make_led_switch_widget("w_led1_rpc", "alias_node1", "Điều khiển LED 1 (GPIO 18)", 1, fqns["switch_control"]),
        "w_led2_rpc": make_led_switch_widget("w_led2_rpc", "alias_node1", "Điều khiển LED 2 (GPIO 19)", 2, fqns["switch_control"]),
        "w_chart_temp": make_line_chart_widget("w_chart_temp", "alias_node2", "Biểu đồ Nhiệt độ", "temperature", "Nhiệt độ", "°C", "#ef4444", fqns["line_chart"]),
        "w_chart_humid": make_line_chart_widget("w_chart_humid", "alias_node2", "Biểu đồ Độ ẩm", "humidity", "Độ ẩm", "%", "#3b82f6", fqns["line_chart"]),
        "w_chart_lux": make_line_chart_widget("w_chart_lux", "alias_node1", "Biểu đồ Ánh sáng", "illuminance", "Ánh sáng", "lx", "#f59e0b", fqns["line_chart"]),
        "w_logs_table": make_logs_custom_widget("w_logs_table", "alias_node1", "alias_node2", fqns["logs_custom"]),
    }
    return {
        "title": DASHBOARD_TITLE,
        "configuration": {
            "description": "Dashboard ThingsBoard CE thực hành IoT UIT Lab 04 (2x ESP32).",
            "widgets": widgets,
            "entityAliases": _build_entity_aliases(node1_id, node2_id),
            "timewindow": {
                "displayValue": "",
                "selectedTab": 0,
                "realtime": {"realtimeType": 0, "interval": 1000, "timewindowMs": 900000},
            },
            "states": {
                "default": {
                    "name": "Màn hình chính",
                    "root": True,
                    "layouts": {
                        "main": {
                            "widgets": _build_layout_positions(),
                            "gridSettings": {"columns": 24, "margin": 10},
                        }
                    },
                }
            },
        },
    }


def export_static_artifacts(output_dir: Path | None = None) -> tuple[Path, Path]:
    """Xuất tệp JSON tĩnh cho Widget Bundle và Dashboard phục vụ lưu trữ Git."""
    target_dir = output_dir or Path(__file__).resolve().parent
    bundle_data = {
        "widgetsBundle": build_widget_bundle_payload(),
        "widgetTypes": [build_custom_widget_payload()],
    }
    dash_data = build_dashboard_payload(
        node1_id="11111111-1111-1111-1111-111111111111",
        node2_id="22222222-2222-2222-2222-222222222222",
    )
    bundle_path = target_dir / "thingsboard_widget_bundle.json"
    dash_path = target_dir / "thingsboard_dashboard.json"
    bundle_path.write_text(json.dumps(bundle_data, indent=2, ensure_ascii=False), encoding="utf-8")
    dash_path.write_text(json.dumps(dash_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return bundle_path, dash_path


if __name__ == "__main__":
    export_static_artifacts()
