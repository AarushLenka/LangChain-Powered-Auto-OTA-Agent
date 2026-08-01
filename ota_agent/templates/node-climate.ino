// =============================================================================
//  node-climate  --  DHT22 temperature/humidity node
//  Generated from skeleton.ino.template. NON-REGENERABLE plumbing below;
//  agent regenerates ONLY the readAndActOnSensor() body between the markers.
//  Losing the OTA loop = physical USB reflash. Do not touch the plumbing.
// =============================================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <HTTPUpdate.h>
#include <DHT.h>                 // DHT sensor library + Adafruit Unified Sensor
#include "secrets.h"             // WiFi SSID, password, OTA server IP (NOT in git)

// ---- PER-NODE CONSTANTS (exactly four) ------------------------------------
static const char*   BASE_URL         = OTA_BASE_URL;
static const char*   DEVICE_ID        = "node-climate";
static const char*   SENSOR_TYPE      = "temperature";
static const char*   FIRMWARE_VERSION = "v1.0";
// ---------------------------------------------------------------------------

static const unsigned long LOOP_INTERVAL_MS = 10000;

// ============================ NON-REGENERABLE ==============================
void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
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
  // Whitespace-tolerant: the server emits compact JSON ("key":true) while a
  // pretty-printer would emit ("key": true). Match either.
  bool updateAvailable = code == 200 &&
      (body.indexOf("\"update_available\":true") >= 0 ||
       body.indexOf("\"update_available\": true") >= 0);
  if (updateAvailable) {
    WiFiClient client;
    httpUpdate.update(client, String(BASE_URL) + "/download/" + DEVICE_ID);
  }
}
// ========================== END NON-REGENERABLE ============================


// ==== AGENT SENSOR BLOCK START ====
// Default logic (fleet-context comment goes here when the agent regenerates).
// DHT22 data pin 4. Reports temperature in celsius; flags a critical event
// when it crosses the high threshold.
#define DHT_PIN  4
#define DHT_TYPE DHT22
static DHT dht(DHT_PIN, DHT_TYPE);
static bool dht_started = false;

void readAndActOnSensor() {
  if (!dht_started) { dht.begin(); dht_started = true; }
  float value = dht.readTemperature();          // celsius
  if (isnan(value)) return;                      // skip bad reads
  const char* event = (value >= 40.0f) ? "temperature_critical" : "";
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
