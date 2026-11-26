/*
 * UIT IoT Lab 04 - ESP32 Node 2: Cảm biến Nhiệt độ & Độ ẩm DHT22/DHT11
 * Thư viện cần cài trong Arduino IDE Library Manager:
 *   - PubSubClient (Nick O'Leary)
 *   - ArduinoJson (Benoit Blanchon, v6 hoặc v7)
 *   - DHT sensor library (Adafruit) + Adafruit Unified Sensor
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* TB_SERVER_IP  = "192.168.1.100";
const int   TB_PORT       = 1883;
const char* TB_TOKEN      = "ESP32_NODE2_TOKEN";

#define DHTPIN 4
#define DHTTYPE DHT22  // Đổi thành DHT11 nếu bạn dùng cảm biến DHT11

const unsigned long PUBLISH_INTERVAL_MS = 2000;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
DHT dht(DHTPIN, DHTTYPE);

unsigned long lastPublishMs = 0;

void ensureConnections() {
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
    }
  }
  while (!mqttClient.connected()) {
    if (mqttClient.connect("ESP32-Node2-Temp-Humid", TB_TOKEN, nullptr)) {
      mqttClient.publish("v1/devices/me/attributes", "{\"firmware\":\"1.0.0\"}");
    } else {
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  mqttClient.setServer(TB_SERVER_IP, TB_PORT);
  ensureConnections();
}

void loop() {
  if (!mqttClient.connected()) {
    ensureConnections();
  }
  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastPublishMs >= PUBLISH_INTERVAL_MS) {
    lastPublishMs = now;
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    if (!isnan(humidity) && !isnan(temperature)) {
      StaticJsonDocument<128> doc;
      doc["temperature"] = temperature;
      doc["humidity"] = humidity;
      char buffer[128];
      serializeJson(doc, buffer);
      mqttClient.publish("v1/devices/me/telemetry", buffer);
    }
  }
}
