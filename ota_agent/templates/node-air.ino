// =============================================================================
//  node-air  --  MQ-135 air-quality node (raw analog)
//  Generated from skeleton.ino.template. NON-REGENERABLE plumbing below;
//  agent regenerates ONLY the readAndActOnSensor() body between the markers.
//  Losing the OTA loop = physical USB reflash. Do not touch the plumbing.
// =============================================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <HTTPUpdate.h>

// ---- PER-NODE CONSTANTS (exactly four) ------------------------------------
static const char*   BASE_URL         = "http://192.168.1.100:5001";
static const char*   DEVICE_ID        = "node-air";
static const char*   SENSOR_TYPE      = "air_quality";
static const char*   FIRMWARE_VERSION = "v1.0";
// ---------------------------------------------------------------------------

static const char*   WIFI_SSID = "your-ssid";
static const char*   WIFI_PASS = "your-pass";
static const unsigned long LOOP_INTERVAL_MS = 10000;

// ============================ NON-REGENERABLE ==============================
void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(500);
  }
}

void reportReading(float value, const char* event) {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  String url = String(BASE_URL) + "/report/" + DEVICE_ID +
               "?sensor_type=" + SENSOR_TYPE +
               "&value=" + String(value, 2) +
               "&event=" + (event ? String(event) : String(""));
  http.begin(url);
  http.POST("");            // QUERY PARAMS, not JSON -- load-bearing contract
  http.end();
}

void checkForOTA() {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  String checkUrl = String(BASE_URL) + "/check/" + DEVICE_ID +
                    "?current_version=" + FIRMWARE_VERSION;
  http.begin(checkUrl);
  int code = http.GET();
  String body = (code == 200) ? http.getString() : String("");
  http.end();
  if (code == 200 && body.indexOf("\"update_available\": true") >= 0) {
    WiFiClient client;
    httpUpdate.update(client, String(BASE_URL) + "/download/" + DEVICE_ID);
  }
}
// ========================== END NON-REGENERABLE ============================


// ==== AGENT SENSOR BLOCK START ====
// Default logic (fleet-context comment goes here when the agent regenerates).
// MQ-135 analog on GPIO34 (input-only ADC pin). Reports the raw 12-bit value;
// flags a gas anomaly when it crosses the high threshold.
#define MQ135_PIN 34

void readAndActOnSensor() {
  float value = (float)analogRead(MQ135_PIN);   // 0..4095 raw analog
  const char* event = (value >= 1400.0f) ? "gas_anomaly" : "";
  reportReading(value, event);
}
// ==== AGENT SENSOR BLOCK END ====


// ============================ NON-REGENERABLE ==============================
void setup() {
  Serial.begin(115200);
  connectWiFi();
}

void loop() {
  connectWiFi();
  checkForOTA();
  readAndActOnSensor();
  delay(LOOP_INTERVAL_MS);
}
// ========================== END NON-REGENERABLE ============================
