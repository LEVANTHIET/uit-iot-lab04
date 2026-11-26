"""Kiểm thử cấu hình Dashboard JSON, Custom Widget và luồng ThingsBoard API."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cloud.export_cli import export_logs_to_file
from cloud.provision import provision_all
from cloud.tb_client import ThingsBoardClient
from dashboard.builder import (
    build_custom_widget_payload,
    build_dashboard_payload,
    export_static_artifacts,
    resolve_widget_fqns,
)


class _FakeResponse:
    """Giả lập HTTP response phục vụ kiểm thử không cần server thật."""

    def __init__(self, status_code: int, payload: object) -> None:
        self.status_code = status_code
        self._payload = payload
        self.content = b"{}" if payload is not None else b""

    def json(self) -> object:
        """Trả về dữ liệu JSON giả lập."""
        return self._payload

    def raise_for_status(self) -> None:
        """Ném lỗi nếu mã HTTP từ 400 trở lên."""
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class TestDashboardBuilder(unittest.TestCase):
    """Kiểm tra tính toàn vẹn JSON của Dashboard và Custom Widget ThingsBoard."""

    def test_dashboard_contains_all_lab04_sections(self) -> None:
        """Xác nhận Dashboard đủ 2 ESP32, 3 cảm biến, 2 LED RPC và Logs 5 cột."""
        dash = build_dashboard_payload("uuid-1", "uuid-2")
        serialized = json.dumps(dash, ensure_ascii=False)
        for token in ("uuid-1", "uuid-2", "temperature", "humidity", "illuminance", "setLed1", "setLed2"):
            self.assertIn(token, serialized)

    def test_custom_widget_contains_five_columns_and_export(self) -> None:
        """Xác nhận Custom Widget có đủ 5 cột tiếng Việt và nút xuất CSV/Excel."""
        widget = build_custom_widget_payload()
        html = widget["descriptor"]["templateHtml"]
        js = widget["descriptor"]["controllerScript"]
        for col in ("ID thiết bị", "Tên thiết bị", "Tên giá trị", "Giá trị cảm biến", "Thời gian nhận dữ liệu"):
            self.assertIn(col, html)
            self.assertIn(col, js)
        self.assertIn("Xuất CSV", html)
        self.assertIn("Xuất Excel", html)

    def test_resolve_widget_fqns_adapts_live_catalog(self) -> None:
        """Xác nhận hàm đối chiếu FQN nhận diện đúng tên widget từ server."""
        catalog = [
            {"fqn": "system.cards.value_card"},
            {"fqn": "system.charts.timeseries_line_chart"},
        ]
        resolved = resolve_widget_fqns(catalog)
        self.assertEqual(resolved["value_card"], "system.cards.value_card")
        self.assertEqual(resolved["line_chart"], "system.charts.timeseries_line_chart")


class TestCloudProvisionAndExport(unittest.TestCase):
    """Kiểm thử client ThingsBoard API, auto-provision và xuất tệp CLI."""

    def test_provision_all_and_export_with_mock_session(self) -> None:
        """Mô phỏng trọn vẹn luồng đăng nhập, tạo thiết bị, nạp Dashboard và xuất CSV."""
        session = MagicMock()
        session.get.side_effect = [
            _FakeResponse(404, None),
            _FakeResponse(404, None),
            _FakeResponse(404, None),
            _FakeResponse(200, {"id": {"id": "id-node1"}, "name": "ESP32-Node1-Light-LED"}),
            _FakeResponse(200, {"id": {"id": "id-node2"}, "name": "ESP32-Node2-Temp-Humid"}),
        ]
        session.request.side_effect = [
            _FakeResponse(200, {"token": "jwt-123"}),
            _FakeResponse(200, {"id": {"id": "id-node1"}}),
            _FakeResponse(200, {"credentialsId": "OLD_1"}),
            _FakeResponse(200, {"credentialsId": "ESP32_NODE1_TOKEN"}),
            _FakeResponse(200, {"id": {"id": "id-node2"}}),
            _FakeResponse(200, {"credentialsId": "ESP32_NODE2_TOKEN"}),
            _FakeResponse(200, []),
            _FakeResponse(200, {"id": {"id": "bundle-1"}}),
            _FakeResponse(200, {"id": {"id": "wtype-1"}}),
            _FakeResponse(200, {"data": []}),
            _FakeResponse(200, {"data": []}),
            _FakeResponse(200, {"id": {"id": "dash-1"}}),
            _FakeResponse(200, {"illuminance": [{"ts": 1700000000000, "value": "250"}]}),
            _FakeResponse(200, {"temperature": [{"ts": 1700000001000, "value": "27.5"}]}),
        ]
        client = ThingsBoardClient(base_url="http://localhost:8080", session=session)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            n1, n2, dash_id = provision_all(client, "tenant@thingsboard.org", "tenant", save_dir=tmp_dir)
            self.assertEqual((n1, n2, dash_id), ("id-node1", "id-node2", "dash-1"))
            self.assertTrue((tmp_dir / "thingsboard_dashboard.json").is_file())

            csv_out = tmp_dir / "out.csv"
            count = export_logs_to_file(client, csv_out, fmt="csv")
            self.assertEqual(count, 2)
            self.assertIn("ESP32-Node1-Light-LED", csv_out.read_text(encoding="utf-8-sig"))

            b_path, d_path = export_static_artifacts(output_dir=tmp_dir)
            self.assertTrue(b_path.is_file())
            self.assertTrue(d_path.is_file())


if __name__ == "__main__":
    unittest.main()
