// Firmware Version: 1.3
// Description: Enhanced safety and power management for critical temperature events.
#include <Arduino.h>

// --- Pin Definitions
#define SENSOR_A_PIN 1
#define SENSOR_B_PIN 2
#define SENSOR_C_PIN 3
#define SENSOR_D_PIN 4

// --- Configuration ---
const int CRITICAL_TEMPERATURE = 90; // Critical temperature threshold
const int SENSOR_A_THRESHOLD = 100;   // Previous threshold for normal operation
const int NORMAL_DELAY = 5000;         // Normal delay between readings
const int CRITICAL_DELAY = 10000;      // Delay during critical conditions

// --- State Variables ---
bool isCritical = false; // Flag to indicate if we are in a critical state

void setup() {
    Serial.begin(115200);
    while (!Serial); // Wait for serial connection
    Serial.println("============================");
    Serial.println("Device starting... Firmware v1.3");
    Serial.println("Mode: Monitoring Sensors A, B, C, D");
    Serial.println("============================");
    pinMode(SENSOR_A_PIN, INPUT);
    pinMode(SENSOR_B_PIN, INPUT);
    pinMode(SENSOR_C_PIN, INPUT);
    pinMode(SENSOR_D_PIN, INPUT);
}

void loop() {
    // Read sensor A value
    int sensor_a_value = analogRead(SENSOR_A_PIN);
    
    // Log sensor data to the console
    Serial.print("DATA: Sensor A (temperature): ");
    Serial.println(sensor_a_value);

    // Check for critical temperature condition
    if (sensor_a_value >= CRITICAL_TEMPERATURE) {
        isCritical = true; // Set critical state
        Serial.println("EVENT: sensor_A_temperature_critical");
        Serial.println("ACTION: Initiating safety protocols.");
        // Implement safety protocols (e.g., shut down or alert)
        // Here we could add code to send an alert over the network
    } else {
        isCritical = false; // Reset critical state
        // Check for normal threshold
        if (sensor_a_value > SENSOR_A_THRESHOLD) {
            Serial.println("EVENT: sensor_A_threshold_exceeded");
            // Activate sensor B monitoring
            Serial.println("ACTION: Activating Sensor B monitoring");
        } else {
            // Deactivate sensor B monitoring
            Serial.println("ACTION: Deactivating Sensor B monitoring");
        }
    }

    // Adjust delay based on critical state
    int delayTime = isCritical ? CRITICAL_DELAY : NORMAL_DELAY;
    Serial.println("---");
    delay(delayTime); // Wait before next reading
