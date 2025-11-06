// Firmware Version: 1.2
// Description: Deactivate sensor B monitoring when sensor A goes below threshold.
#include <Arduino.h>

// --- Pin Definitions
// Based on sensor_schema
#define SENSOR_A_PIN 1
#define SENSOR_B_PIN 2
#define SENSOR_C_PIN 3
#define SENSOR_D_PIN 4

// --- Configuration ---
const int SENSOR_A_THRESHOLD = 100;

void setup() {
    // Initialize Serial communication
    Serial.begin(115200);
    while (!Serial); // Wait for serial connection
    Serial.println("============================");
    Serial.println("Device starting... Firmware v1.2");
    Serial.println("Mode: Monitoring Sensors A, B, C, D");
    Serial.println("============================");
    // Initialize sensor pins
    pinMode(SENSOR_A_PIN, INPUT);
    pinMode(SENSOR_B_PIN, INPUT);
    pinMode(SENSOR_C_PIN, INPUT);
    pinMode(SENSOR_D_PIN, INPUT);
}

void loop() {
  // Read active sensors
    int sensor_a_value = analogRead(SENSOR_A_PIN);
    int sensor_b_value = analogRead(SENSOR_B_PIN);
    int sensor_c_value = analogRead(SENSOR_C_PIN);
    int sensor_d_value = analogRead(SENSOR_D_PIN);

  // Log sensor data to the console
    Serial.print("DATA: Sensor A (temperature): ");
    Serial.println(sensor_a_value);
    Serial.print("DATA: Sensor B (humidity): ");
    Serial.println(sensor_b_value);
    Serial.print("DATA: Sensor C (pressure): ");
    Serial.println(sensor_c_value);
    Serial.print("DATA: Sensor D (light_intensity): ");
    Serial.println(sensor_d_value);

  // Check for the trigger condition
    if (sensor_a_value > SENSOR_A_THRESHOLD) {
        // In a real device, this would be sent over WiFi/LTE to our Flask server
        Serial.println("EVENT: sensor_A_threshold_exceeded");
        // Activate sensor B monitoring
        Serial.println("ACTION: Activating Sensor B monitoring");
    } else {
        // Deactivate sensor B monitoring
        Serial.println("ACTION: Deactivating Sensor B monitoring");
    }

    Serial.println("---");
    delay(5000); // Wait for 5 seconds before next reading
}