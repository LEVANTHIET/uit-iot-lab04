"""Kiểm thử trình giả lập MQTT hai mạch ESP32 và mã nguồn firmware Arduino."""

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.constants import MQTT_TOPIC_TELEMETRY
from edge.simulator.esp32_sim import DualEsp32Simulator
from edge.simulator.rpc_handler import handle_led_rpc


ROOT_DIR = Path(__file__).resolve().parents[1]


class TestEdgeRpcHandler(unittest.TestCase):
    """Kiểm tra xử lý các lệnh RPC điều khiển 2 đèn LED."""

    def test_set_and_get_both_leds(self) -> None:
        """Xác nhận setLed1/getLed1/setLed2/getLed2 cập nhật đúng trạng thái."""
        state = {"led1": False, "led2": False}
        state, val1 = handle_led_rpc("setLed1", True, state)
        self.assertTrue(val1)
        self.assertTrue(state["led1"])

        state, val2 = handle_led_rpc("setLed2", "on", state)
        self.assertTrue(val2)
        self.assertTrue(state["led2"])

        _, read1 = handle_led_rpc("getLed1", None, state)
        _, read2 = handle_led_rpc("getLed2", None, state)
        self.assertTrue(read1)
        self.assertTrue(read2)

    def test_rejects_unknown_rpc_method(self) -> None:
        """Từ chối tên phương thức RPC lạ ngoài danh sách hỗ trợ."""
        with self.assertRaises(ValueError):
            handle_led_rpc("rebootDevice", None, {"led1": False, "led2": False})


class TestDualEsp32Simulator(unittest.TestCase):
    """Kiểm thử xuất bản dữ liệu MQTT và phản hồi RPC không cần Broker thật."""

    def test_publish_step_and_rpc_callback(self) -> None:
        """Xác nhận publish_step gửi đủ 3 thông số cùng xử lý callback RPC."""
        with patch("edge.simulator.esp32_sim.mqtt.Client") as mock_cls:
            c1 = MagicMock()
            c2 = MagicMock()
            mock_cls.side_effect = [c1, c2]
            sim = DualEsp32Simulator()

            p1, p2 = sim.publish_step(step=1)
            self.assertIn("illuminance", p1)
            self.assertIn("temperature", p2)
            self.assertIn("humidity", p2)
            c1.publish.assert_called()
            c2.publish.assert_called()

            msg = MagicMock()
            msg.topic = "v1/devices/me/rpc/request/42"
            msg.payload = json.dumps({"method": "setLed2", "params": True}).encode("utf-8")
            sim._on_node1_message(c1, None, msg)
            c1.publish.assert_any_call("v1/devices/me/rpc/response/42", "true")
            c1.publish.assert_any_call(
                MQTT_TOPIC_TELEMETRY,
                json.dumps({"led1": False, "led2": True}),
            )

    def test_firmware_sketches_match_tokens_and_topics(self) -> None:
        """Kiểm tra hai tệp .ino khớp token, chân GPIO và vòng lặp không block."""
        ino1 = (
            ROOT_DIR / "edge" / "firmware" / "esp32_node1_light_led" / "esp32_node1_light_led.ino"
        ).read_text(encoding="utf-8")
        ino2 = (
            ROOT_DIR / "edge" / "firmware" / "esp32_node2_temp_humid" / "esp32_node2_temp_humid.ino"
        ).read_text(encoding="utf-8")

        for item in ("ESP32_NODE1_TOKEN", "setLed1", "setLed2", "LED1_PIN = 18", "LED2_PIN = 19", "millis()"):
            self.assertIn(item, ino1)
        for item in ("ESP32_NODE2_TOKEN", "DHTPIN 4", "temperature", "humidity", "millis()"):
            self.assertIn(item, ino2)


if __name__ == "__main__":
    unittest.main()
