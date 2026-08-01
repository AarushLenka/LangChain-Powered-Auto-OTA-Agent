/*
 * Firmware for device-001
 * 
 * This firmware handles the transition to night mode based on light sensor input.
 * It also checks for critical gas levels and motion detection from other nodes in the fleet.
 * 
 * Influencing signals:
 * - node-air: gas_critical
 * - node-presence: motion_detected
 * 
 * The firmware ensures that the transition to night mode does not compromise safety.
 */

#include <Arduino.h>

// Constants for sensor thresholds
const float GAS_CRITICAL_THRESHOLD = 1000.0; // Example threshold for gas levels
const int NIGHT_MODE_LIGHT_LEVEL = 0; // Light level for night mode

void setup() {
    // Initialize sensors and communication
}

void loop() {
    // Check light sensor value
    float lightSensorValue = readLightSensor();
    
    // Check gas level from node-air
    float gasLevel = readGasSensor(); // Assume this function reads from node-air
    bool isGasCritical = gasLevel > GAS_CRITICAL_THRESHOLD;

    // Check motion from node-presence
    bool isMotionDetected = readMotionSensor(); // Assume this function reads from node-presence

    // If gas is critical and motion is detected, do not transition to night mode
    if (isGasCritical && isMotionDetected) {
        // Trigger alarm or notification
        triggerAlarm();
    } else if (lightSensorValue < NIGHT_MODE_LIGHT_LEVEL) {
        // Transition to night mode
        transitionToNightMode();
    }

    // Add a delay to avoid rapid looping
    delay(1000);
}

float readLightSensor() {
    // Implement reading from the light sensor
    return analogRead(LIGHT_SENSOR_PIN);
}

float readGasSensor() {
    // Implement reading from the gas sensor
    return analogRead(GAS_SENSOR_PIN);
}

bool readMotionSensor() {
    // Implement reading from the motion sensor
    return digitalRead(MOTION_SENSOR_PIN);
}

void transitionToNightMode() {
    // Implement the logic to transition to night mode
}

void triggerAlarm() {
    // Implement the logic to trigger an alarm or notification
}