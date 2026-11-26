"""Hằng số thiết bị ESP32, MQTT topic và lệnh RPC chuẩn cho ThingsBoard."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceSpec:
    """Mô tả cấu hình cố định của một thiết bị ESP32 trên ThingsBoard."""

    name: str
    label: str
    device_profile: str
    access_token: str
    telemetry_keys: tuple[str, ...]
    description: str


NODE1_SPEC = DeviceSpec(
    name="ESP32-Node1-Light-LED",
    label="ESP32 #1 - Cảm biến ánh sáng & 2 LED",
    device_profile="default",
    access_token="ESP32_NODE1_TOKEN",
    telemetry_keys=("illuminance", "led1", "led2"),
    description="Mạch ESP32 gắn cảm biến BH1750 (I2C) cùng LED1 (GPIO 18) và LED2 (GPIO 19).",
)

NODE2_SPEC = DeviceSpec(
    name="ESP32-Node2-Temp-Humid",
    label="ESP32 #2 - Cảm biến Nhiệt độ & Độ ẩm",
    device_profile="default",
    access_token="ESP32_NODE2_TOKEN",
    telemetry_keys=("temperature", "humidity"),
    description="Mạch ESP32 gắn cảm biến DHT22/DHT11 (GPIO 4).",
)

ALL_DEVICES: tuple[DeviceSpec, ...] = (NODE1_SPEC, NODE2_SPEC)

MQTT_TOPIC_TELEMETRY = "v1/devices/me/telemetry"
MQTT_TOPIC_ATTRIBUTES = "v1/devices/me/attributes"
MQTT_TOPIC_RPC_REQUEST = "v1/devices/me/rpc/request/+"
MQTT_TOPIC_RPC_RESPONSE_PREFIX = "v1/devices/me/rpc/response/"

RPC_SET_LED1 = "setLed1"
RPC_GET_LED1 = "getLed1"
RPC_SET_LED2 = "setLed2"
RPC_GET_LED2 = "getLed2"

SENSOR_LABELS_VI: dict[str, str] = {
    "temperature": "Nhiệt độ (°C)",
    "humidity": "Độ ẩm (%)",
    "illuminance": "Ánh sáng (lux)",
    "led1": "Trạng thái LED 1",
    "led2": "Trạng thái LED 2",
}
