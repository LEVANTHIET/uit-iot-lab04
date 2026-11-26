"""Trình giả lập 2 mạch ESP32 giao tiếp MQTT thời gian thực với ThingsBoard."""

import argparse
import json
import random
import time
from typing import Any

import paho.mqtt.client as mqtt

from common.constants import (
    MQTT_TOPIC_ATTRIBUTES,
    MQTT_TOPIC_RPC_REQUEST,
    MQTT_TOPIC_RPC_RESPONSE_PREFIX,
    MQTT_TOPIC_TELEMETRY,
    NODE1_SPEC,
    NODE2_SPEC,
)
from core.telemetry import build_tb_telemetry_payload
from edge.simulator.rpc_handler import handle_led_rpc


class DualEsp32Simulator:
    """Mô phỏng đồng thời ESP32 #1 (BH1750 + 2 LED) kèm ESP32 #2 (DHT22)."""

    def __init__(self, host: str = "localhost", port: int = 1883, interval: float = 2.0) -> None:
        """Khởi tạo hai kết nối MQTT độc lập cho hai mạch ESP32."""
        self.host = host
        self.port = port
        self.interval = interval
        self.led_state: dict[str, bool] = {"led1": False, "led2": False}
        self.client1 = self._create_client("sim-esp32-node1", NODE1_SPEC.access_token)
        self.client2 = self._create_client("sim-esp32-node2", NODE2_SPEC.access_token)
        self.client1.on_connect = self._on_node1_connect
        self.client1.on_message = self._on_node1_message

    def _create_client(self, client_id: str, token: str) -> mqtt.Client:
        """Tạo MQTT Client paho v2 sử dụng Access Token làm username."""
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
        client.username_pw_set(token)
        return client

    def _on_node1_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        """Đăng ký lắng nghe lệnh RPC khi ESP32 #1 kết nối Broker."""
        client.subscribe(MQTT_TOPIC_RPC_REQUEST)
        client.publish(MQTT_TOPIC_ATTRIBUTES, json.dumps({"firmware": "1.0.0", **self.led_state}))

    def _on_node1_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        """Nhận lệnh RPC bật/tắt 2 LED, phản hồi ngay đồng thời cập nhật telemetry."""
        req_id = msg.topic.rsplit("/", 1)[-1]
        data = json.loads(msg.payload.decode("utf-8"))
        method = str(data.get("method", ""))
        params = data.get("params")
        try:
            self.led_state, reply_val = handle_led_rpc(method, params, self.led_state)
        except ValueError:
            return
        client.publish(f"{MQTT_TOPIC_RPC_RESPONSE_PREFIX}{req_id}", json.dumps(reply_val))
        client.publish(MQTT_TOPIC_ATTRIBUTES, json.dumps(self.led_state))
        payload = build_tb_telemetry_payload(self.led_state)
        client.publish(MQTT_TOPIC_TELEMETRY, json.dumps(payload))

    def publish_step(self, step: int = 0) -> tuple[dict[str, Any], dict[str, Any]]:
        """Phát một chu kỳ dữ liệu cảm biến cho cả hai mạch ESP32."""
        rng = random.Random(step + int(time.time()))
        lux = round(350.0 + rng.uniform(-35.0, 45.0), 2)
        temp = round(28.5 + rng.uniform(-1.5, 1.8), 2)
        humid = round(65.0 + rng.uniform(-4.0, 4.0), 2)

        p1 = build_tb_telemetry_payload({"illuminance": lux, **self.led_state})
        p2 = build_tb_telemetry_payload({"temperature": temp, "humidity": humid})
        self.client1.publish(MQTT_TOPIC_TELEMETRY, json.dumps(p1))
        self.client2.publish(MQTT_TOPIC_TELEMETRY, json.dumps(p2))
        return p1, p2

    def run(self, duration: float | None = None) -> None:
        """Kết nối Broker rồi phát dữ liệu liên tục đến hết thời gian hoặc Ctrl+C."""
        self.client1.connect(self.host, self.port, keepalive=60)
        self.client2.connect(self.host, self.port, keepalive=60)
        self.client1.loop_start()
        self.client2.loop_start()
        deadline = (time.monotonic() + duration) if duration is not None else None
        step = 0
        try:
            while deadline is None or time.monotonic() < deadline:
                self.publish_step(step)
                step += 1
                time.sleep(self.interval)
        except KeyboardInterrupt:
            pass
        finally:
            self.client1.loop_stop()
            self.client2.loop_stop()
            self.client1.disconnect()
            self.client2.disconnect()


def main() -> None:
    """Điểm vào dòng lệnh chạy giả lập 2 mạch ESP32."""
    parser = argparse.ArgumentParser(description="Giả lập 2 mạch ESP32 qua MQTT")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--duration", type=float, default=None)
    args = parser.parse_args()

    sim = DualEsp32Simulator(host=args.host, port=args.port, interval=args.interval)
    sim.run(duration=args.duration)


if __name__ == "__main__":
    main()
