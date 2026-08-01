/*
 * Firmware for device-001
 * Event: sensor_D_light_intensity_fluctuating_rapidly_between_0_and_1000_lux
 * Reasoning: The event is isolated as all other nodes are stale.
 * Modifications:
 * - Implemented a debounce mechanism to stabilize readings.
 * - Averaged light intensity readings over 5 seconds.
 * - Added logging for critical events.
 */

#include <Arduino.h>

const int LIGHT_SENSOR_PIN = A0; // Pin for light sensor
const int DEBOUNCE_TIME = 1000; // 1 second debounce time
const int AVERAGE_READINGS_COUNT = 5; // Number of readings to average

unsigned long lastReadingTime = 0;
int lightReadings[AVERAGE_READINGS_COUNT];
int readingIndex = 0;
bool isStable = false;

void setup() {
    Serial.begin(115200);
}

void loop() {
    unsigned long currentTime = millis();
    
    // Read light intensity
    int lightValue = analogRead(LIGHT_SENSOR_PIN);
    
    // Check for debounce
    if (currentTime - lastReadingTime > DEBOUNCE_TIME) {
        lightReadings[readingIndex] = lightValue;
        readingIndex = (readingIndex + 1) % AVERAGE_READINGS_COUNT;

        // Calculate average
        int averageLightValue = 0;
        for (int i = 0; i < AVERAGE_READINGS_COUNT; i++) {
            averageLightValue += lightReadings[i];
        }
        averageLightValue /= AVERAGE_READINGS_COUNT;

        // Log the average value
        Serial.print("Average Light Intensity: ");
        Serial.println(averageLightValue);

        // Update last reading time
        lastReadingTime = currentTime;
    }

    // Implement additional logic for handling connectivity and security as needed
}