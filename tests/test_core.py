"""Kiểm thử đơn vị và kiểm thử thuộc tính cho tầng common và core."""

import csv
import io
import math
from pathlib import Path
import sys
import unittest

from hypothesis import given
from hypothesis import strategies as st
from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.constants import ALL_DEVICES, MQTT_TOPIC_TELEMETRY
from core.logs_exporter import (
    LOG_HEADERS_VI,
    export_logs_to_csv_bytes,
    export_logs_to_xlsx_bytes,
    filter_log_records,
    flatten_tb_timeseries,
)
from core.telemetry import build_tb_telemetry_payload, validate_sensor_value


class TestTelemetryValidation(unittest.TestCase):
    """Kiểm thử chuẩn hóa thông số cảm biến và trạng thái đèn LED."""

    @given(st.floats(min_value=-40.0, max_value=85.0, allow_nan=False, allow_infinity=False))
    def test_valid_temperature_property(self, temp: float) -> None:
        """Nhiệt độ hợp lệ luôn giữ trong khoảng [-40, 85] sau khi làm tròn."""
        result = validate_sensor_value("temperature", temp)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, -40.0)
        self.assertLessEqual(result, 85.0)

    @given(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    def test_valid_humidity_property(self, humid: float) -> None:
        """Độ ẩm hợp lệ luôn nằm trong khoảng [0, 100]."""
        result = validate_sensor_value("humidity", humid)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 100.0)

    @given(st.floats(min_value=0.0, max_value=65535.0, allow_nan=False, allow_infinity=False))
    def test_valid_illuminance_property(self, lux: float) -> None:
        """Cường độ ánh sáng hợp lệ luôn nằm trong [0, 65535]."""
        result = validate_sensor_value("illuminance", lux)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 65535.0)

    def test_rejects_nan_inf_and_out_of_range(self) -> None:
        """Từ chối NaN, vô cực, giá trị rỗng hoặc vượt ngưỡng vật lý."""
        for bad in (float("nan"), float("inf"), None, True, -50.0, 120.0):
            with self.assertRaises(ValueError):
                validate_sensor_value("temperature", bad)
        self.assertTrue(math.isclose(validate_sensor_value("humidity", 55.126), 55.13))

    def test_led_and_payload_builder(self) -> None:
        """Kiểm tra đóng gói payload telemetry kèm trạng thái 2 đèn LED."""
        payload = build_tb_telemetry_payload(
            {"illuminance": 320.5, "led1": 1, "led2": "false"},
            ts_ms=1700000000000,
        )
        self.assertEqual(payload["ts"], 1700000000000)
        self.assertTrue(payload["values"]["led1"])
        self.assertFalse(payload["values"]["led2"])
        self.assertEqual(len(ALL_DEVICES), 2)
        self.assertEqual(MQTT_TOPIC_TELEMETRY, "v1/devices/me/telemetry")


class TestLogsAndExport(unittest.TestCase):
    """Kiểm thử chuyển đổi nhật ký 5 trường, bộ lọc và xuất CSV/XLSX."""

    def setUp(self) -> None:
        """Tạo tập dữ liệu mẫu từ cả hai thiết bị ESP32."""
        node1_ts = {
            "illuminance": [{"ts": 1700000002000, "value": "412.5"}],
            "led1": [[1700000003000, "true"]],
        }
        node2_ts = {
            "temperature": [{"ts": 1700000001000, "value": "29.4"}],
            "humidity": [{"ts": 1700000004000, "value": "68.2"}],
        }
        self.records = flatten_tb_timeseries("dev-1", "ESP32-Node1-Light-LED", node1_ts)
        self.records.extend(flatten_tb_timeseries("dev-2", "ESP32-Node2-Temp-Humid", node2_ts))

    def test_flatten_and_filter_records(self) -> None:
        """Kiểm tra đủ 5 trường và lọc chính xác theo thiết bị, khóa, thời gian."""
        self.assertEqual(len(self.records), 4)
        for rec in self.records:
            self.assertEqual(len(rec.as_row()), 5)
        only_temp = filter_log_records(self.records, sensor_key="temperature")
        self.assertEqual(len(only_temp), 1)
        self.assertEqual(only_temp[0].device_id, "dev-2")
        only_node1 = filter_log_records(
            self.records,
            device_query="node1",
            start_ts_ms=1700000002500,
        )
        self.assertEqual(len(only_node1), 1)
        self.assertEqual(only_node1[0].sensor_key, "led1")

    def test_csv_and_xlsx_export_roundtrip(self) -> None:
        """Kiểm tra xuất CSV UTF-8 BOM và Excel .xlsx đọc lại khớp dữ liệu."""
        csv_bytes = export_logs_to_csv_bytes(self.records)
        decoded = csv_bytes.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(decoded)))
        self.assertEqual(tuple(rows[0]), LOG_HEADERS_VI)
        self.assertEqual(len(rows), 5)

        xlsx_bytes = export_logs_to_xlsx_bytes(self.records)
        wb = load_workbook(io.BytesIO(xlsx_bytes))
        sheet = wb.active
        headers = [cell.value for cell in sheet[1]]
        self.assertEqual(tuple(headers), LOG_HEADERS_VI)
        self.assertEqual(sheet.max_row, 5)


if __name__ == "__main__":
    unittest.main()
