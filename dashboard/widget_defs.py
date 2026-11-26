"""Các hàm tạo định nghĩa từng Widget chuẩn cấu trúc JSON của ThingsBoard 3.8."""

from typing import Any


def make_data_key(
    name: str,
    label: str,
    key_type: str = "timeseries",
    units: str = "",
    color: str = "#2196f3",
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Tạo đối tượng dataKey cho datasource của widget ThingsBoard."""
    return {
        "name": name,
        "type": key_type,
        "label": label,
        "color": color,
        "units": units,
        "decimals": 2,
        "settings": settings or {},
    }


def make_entities_table_widget(widget_id: str, alias_id: str, fqn: str) -> dict[str, Any]:
    """Tạo widget bảng hiển thị trạng thái kết nối các thiết bị ESP32."""
    time_fmt = "return value ? new Date(Number(value)).toLocaleString('vi-VN') : '-';"
    return {
        "id": widget_id,
        "typeFullFqn": fqn,
        "type": "latest",
        "sizeX": 24,
        "sizeY": 5,
        "row": 0,
        "col": 0,
        "config": {
            "title": "Trạng Thái Kết Nối Thiết Bị (ESP32)",
            "showTitle": True,
            "useDashboardTimewindow": False,
            "datasources": [
                {
                    "type": "entity",
                    "entityAliasId": alias_id,
                    "dataKeys": [
                        make_data_key("name", "Tên thiết bị", key_type="entityField"),
                        make_data_key("type", "Loại", key_type="entityField"),
                        make_data_key("active", "Đang kết nối", key_type="attribute"),
                        make_data_key(
                            "lastActivityTime",
                            "Hoạt động cuối",
                            key_type="attribute",
                            settings={"useCellContentFunction": True, "cellContentFunction": time_fmt},
                        ),
                    ],
                }
            ],
            "settings": {
                "entitiesTitle": "Trạng Thái Kết Nối Thiết Bị (ESP32)",
                "displayEntityName": False,
                "displayEntityType": False,
                "enableSearch": True,
                "displayPagination": False,
                "enableStickyHeader": True,
            },
        },
    }


def _value_card_settings(color: str, icon: str) -> dict[str, Any]:
    """Tạo bộ thuộc tính hiển thị chuẩn cho Value Card trên ThingsBoard 3.8."""
    return {
        "layout": "square",
        "showLabel": True,
        "labelPosition": "top",
        "labelFont": {"family": "Roboto", "size": 15, "sizeUnit": "px", "weight": "500"},
        "labelColor": {"type": "constant", "color": "rgba(0, 0, 0, 0.75)"},
        "showIcon": True,
        "icon": icon,
        "iconSize": 34,
        "iconSizeUnit": "px",
        "iconColor": {"type": "constant", "color": color},
        "valueFont": {"family": "Roboto", "size": 36, "sizeUnit": "px", "weight": "600"},
        "valueColor": {"type": "constant", "color": "#111827"},
        "showDate": True,
        "dateFormat": {"lastUpdateAgo": True, "custom": False},
        "dateFont": {"family": "Roboto", "size": 12, "sizeUnit": "px", "weight": "400"},
        "dateColor": {"type": "constant", "color": "rgba(0, 0, 0, 0.45)"},
        "background": {
            "type": "color",
            "color": "#ffffff",
            "overlay": {
                "enabled": False,
                "color": "rgba(255,255,255,0.72)",
                "blur": 3,
            },
        },
    }


def make_value_card_widget(
    widget_id: str,
    alias_id: str,
    title: str,
    key: str,
    units: str,
    color: str,
    fqn: str,
    icon: str = "sensors",
) -> dict[str, Any]:
    """Tạo widget thẻ hiển thị giá trị cảm biến tức thời."""
    return {
        "id": widget_id,
        "typeFullFqn": fqn,
        "type": "latest",
        "sizeX": 4,
        "sizeY": 3,
        "row": 0,
        "col": 0,
        "config": {
            "title": title,
            "showTitle": False,
            "useDashboardTimewindow": True,
            "units": units,
            "decimals": 2,
            "datasources": [
                {
                    "type": "entity",
                    "entityAliasId": alias_id,
                    "dataKeys": [make_data_key(key, title, units=units, color=color)],
                }
            ],
            "settings": _value_card_settings(color, icon),
        },
    }


def make_led_switch_widget(
    widget_id: str,
    alias_id: str,
    title: str,
    led_num: int,
    fqn: str,
) -> dict[str, Any]:
    """Tạo widget công tắc điều khiển đèn LED thời gian thực qua MQTT RPC."""
    return {
        "id": widget_id,
        "typeFullFqn": fqn,
        "type": "rpc",
        "sizeX": 6,
        "sizeY": 3,
        "row": 0,
        "col": 0,
        "config": {
            "title": title,
            "showTitle": True,
            "targetDeviceAliasIds": [alias_id],
            "targetDeviceAliases": [],
            "datasources": [],
            "settings": {
                "title": title,
                "initialValue": False,
                "retrieveValueMethod": "rpc",
                "getValueMethod": f"getLed{led_num}",
                "setValueMethod": f"setLed{led_num}",
                "requestTimeout": 5000,
                "showOnOffLabels": True,
            },
        },
    }


def make_line_chart_widget(
    widget_id: str,
    alias_id: str,
    title: str,
    key: str,
    label: str,
    units: str,
    color: str,
    fqn: str,
) -> dict[str, Any]:
    """Tạo widget biểu đồ đường thời gian thực cho một thông số cảm biến."""
    line_settings = {"showLines": True, "fillLines": True, "showPoints": True}
    return {
        "id": widget_id,
        "typeFullFqn": fqn,
        "type": "timeseries",
        "sizeX": 8,
        "sizeY": 5,
        "row": 0,
        "col": 0,
        "config": {
            "title": title,
            "showTitle": True,
            "useDashboardTimewindow": True,
            "units": units,
            "decimals": 2,
            "datasources": [
                {
                    "type": "entity",
                    "entityAliasId": alias_id,
                    "dataKeys": [
                        make_data_key(key, label, units=units, color=color, settings=line_settings)
                    ],
                }
            ],
            "settings": {"showLegend": True, "stack": False},
        },
    }


def make_logs_custom_widget(
    widget_id: str,
    node1_alias: str,
    node2_alias: str,
    fqn: str,
) -> dict[str, Any]:
    """Tạo widget nhật ký 5 trường kèm bộ lọc cùng nút xuất CSV/Excel."""
    return {
        "id": widget_id,
        "typeFullFqn": fqn,
        "type": "timeseries",
        "sizeX": 24,
        "sizeY": 7,
        "row": 0,
        "col": 0,
        "config": {
            "title": "Nhật Ký Hệ Thống IoT - Lọc & Xuất CSV/Excel",
            "showTitle": False,
            "useDashboardTimewindow": True,
            "datasources": [
                {
                    "type": "entity",
                    "entityAliasId": node1_alias,
                    "dataKeys": [
                        make_data_key("illuminance", "illuminance", units="lx"),
                        make_data_key("led1", "led1"),
                        make_data_key("led2", "led2"),
                    ],
                },
                {
                    "type": "entity",
                    "entityAliasId": node2_alias,
                    "dataKeys": [
                        make_data_key("temperature", "temperature", units="°C"),
                        make_data_key("humidity", "humidity", units="%"),
                    ],
                },
            ],
            "settings": {},
        },
    }
