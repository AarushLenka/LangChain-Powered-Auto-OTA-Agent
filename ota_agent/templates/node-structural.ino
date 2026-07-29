// =============================================================================
//  node-structural  --  HC-SR04 ultrasonic distance node
//  Generated from skeleton.ino.template. NON-REGENERABLE plumbing below;
//  agent regenerates ONLY the readAndActOnSensor() body between the markers.
//  Losing the OTA loop = physical USB reflash. Do not touch the plumbing.
// =============================================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <HTTPUpdate.h>
#include "secrets.h"             // WiFi SSID, password, OTA server IP (NOT in git)

// ---- PER-NODE CONSTANTS (exactly four) ------------------------------------
static const char*   BASE_URL         = OTA_BASE_URL;
static const char*   DEVICE_ID        = "node-structural";
static const char*   SENSOR_TYPE      = "distance";
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
// HC-SR04 trig + echo share GPIO5 per db.json (single-pin wiring): pulse out,
// then read the echo back on the same line. Reports distance in cm; flags a
// proximity event when an object is closer than the threshold.
#define TRIG_ECHO_PIN 5
static const float SOUND_CM_PER_US = 0.0343f;   // speed of sound / 2, cm per us
                                                // ponytail: tune per rig if readings drift

void readAndActOnSensor() {
  // 10us trigger pulse
  pinMode(TRIG_ECHO_PIN, OUTPUT);
  digitalWrite(TRIG_ECHO_PIN, LOW);  delayMicroseconds(2);
  digitalWrite(TRIG_ECHO_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_ECHO_PIN, LOW);
  // listen for echo on the same pin
  pinMode(TRIG_ECHO_PIN, INPUT);
  unsigned long us = pulseIn(TRIG_ECHO_PIN, HIGH, 30000UL);  // 30ms timeout (~5m)
  if (us == 0) return;                                        // no echo -> skip
  float value = (us * SOUND_CM_PER_US) / 2.0f;                // round-trip -> cm
  const char* event = (value < 20.0f) ? "proximity_alert" : "";
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
