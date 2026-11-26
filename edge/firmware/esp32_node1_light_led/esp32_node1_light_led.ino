/*
 * UIT IoT Lab 04 - ESP32 Node 1: Cảm biến ánh sáng BH1750 + 2 Đèn LED (MQTT RPC)
 * Thư viện cần cài trong Arduino IDE Library Manager:
 *   - PubSubClient (Nick O'Leary)
 *   - ArduinoJson (Benoit Blanchon, v6 hoặc v7)
 *   - BH1750 (Christopher Laws)
 */

#include <WiFi.h>
#include <Wire.h>
#include <BH1750.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* TB_SERVER_IP  = "192.168.1.100";
const int   TB_PORT       = 1883;
const char* TB_TOKEN      = "ESP32_NODE1_TOKEN";

const int LED1_PIN = 18;
const int LED2_PIN = 19;
const unsigned long PUBLISH_INTERVAL_MS = 2000;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
BH1750 lightMeter;

bool led1State = false;
bool led2State = false;
unsigned long lastPublishMs = 0;

void publishStates() {
  StaticJsonDocument<128> doc;
  doc["led1"] = led1State;
  doc["led2"] = led2State;
  char buffer[128];
  serializeJson(doc, buffer);
  mqttClient.publish("v1/devices/me/attributes", buffer);
  mqttClient.publish("v1/devices/me/telemetry", buffer);
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, payload, length)) {
    return;
  }

  String topicStr(topic);
  int slashIdx = topicStr.lastIndexOf('/');
  String reqId = topicStr.substring(slashIdx + 1);
  String method = doc["method"] | "";

  bool replyVal = false;
  if (method == "setLed1") {
    led1State = doc["params"].as<bool>();
    digitalWrite(LED1_PIN, led1State ? HIGH : LOW);
    replyVal = led1State;
  } else if (method == "getLed1") {
    replyVal = led1State;
  } else if (method == "setLed2") {
    led2State = doc["params"].as<bool>();
    digitalWrite(LED2_PIN, led2State ? HIGH : LOW);
    replyVal = led2State;
  } else if (method == "getLed2") {
    replyVal = led2State;
  } else {
    return;
  }

  String respTopic = "v1/devices/me/rpc/response/" + reqId;
  mqttClient.publish(respTopic.c_str(), replyVal ? "true" : "false");
  publishStates();
}

void ensureConnections() {
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
    }
  }
  while (!mqttClient.connected()) {
    if (mqttClient.connect("ESP32-Node1-Light-LED", TB_TOKEN, nullptr)) {
      mqttClient.subscribe("v1/devices/me/rpc/request/+");
      publishStates();
    } else {
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  digitalWrite(LED1_PIN, LOW);
  digitalWrite(LED2_PIN, LOW);

  Wire.begin(21, 22);
  lightMeter.begin();

  mqttClient.setServer(TB_SERVER_IP, TB_PORT);
  mqttClient.setCallback(onMqttMessage);
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
    float lux = lightMeter.readLightLevel();
    if (lux >= 0.0f) {
      StaticJsonDocument<128> doc;
      doc["illuminance"] = lux;
      doc["led1"] = led1State;
      doc["led2"] = led2State;
      char buffer[128];
      serializeJson(doc, buffer);
      mqttClient.publish("v1/devices/me/telemetry", buffer);
    }
  }
}
