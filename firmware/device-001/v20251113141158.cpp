// Firmware Version: 2.1
// Description: Enhanced safety measures for high temperature events with alerting, power management, and improved sensor handling.
#include <Arduino.h>

// --- Pin Definitions ---
#define SENSOR_A_PIN 1 // Temperature sensor
#define SENSOR_B_PIN 2 // Humidity sensor
#define SENSOR_C_PIN 3 // Pressure sensor
#define SENSOR_D_PIN 4 // Light intensity sensor
#define SENSOR_E_PIN 5 // Motion sensor
#define SENSOR_F_PIN 6 // GPS latitude sensor

// --- Configuration ---
const int MEMORY_TEST_SIZE = 1024; // Size for memory test
const int NORMAL_SENSOR_READ_DELAY = 5000; // Delay between sensor readings in normal state
const int HIGH_TEMP_SENSOR_READ_DELAY = 1000; // Delay between sensor readings in high temperature state
const int TEMP_THRESHOLD = 80; // Temperature threshold in Celsius
const int CRITICAL_TEMP_THRESHOLD = 90; // Critical temperature threshold in Celsius
const int MOVING_AVERAGE_SIZE = 5; // Size of the moving average buffer

// --- State Variables ---
bool sensorsOperational = true; // Flag to indicate if all sensors are operational
int temperatureReadings[MOVING_AVERAGE_SIZE]; // Buffer for moving average
int readingIndex = 0; // Current index for moving average
int lastTemperatureReading = 0; // Store the last temperature reading

void setup() {
    Serial.begin(115200);
    while (!Serial); // Wait for serial connection
    Serial.println("============================");
    Serial.println("Device starting... Firmware v2.1");
    Serial.println("Mode: Enhanced Safety with Temperature Management");
    Serial.println("============================");

    // Initialize sensor pins
    pinMode(SENSOR_A_PIN, INPUT);
    pinMode(SENSOR_B_PIN, INPUT);
    pinMode(SENSOR_C_PIN, INPUT);
    pinMode(SENSOR_D_PIN, INPUT);
    pinMode(SENSOR_E_PIN, INPUT);
    pinMode(SENSOR_F_PIN, INPUT);

    // Initialize moving average buffer
    for (int i = 0; i < MOVING_AVERAGE_SIZE; i++) {
        temperatureReadings[i] = 0;
    }

    // Perform initial health checks
    performHealthCheck();
}

void loop() {
    // Perform health check at regular intervals
    performHealthCheck();
    delay((lastTemperatureReading > TEMP_THRESHOLD) ? HIGH_TEMP_SENSOR_READ_DELAY : NORMAL_SENSOR_READ_DELAY);
}

void performHealthCheck() {
    Serial.println("Performing health check...");

    // Validate sensors
    validateSensors();

    // Perform memory test
    if (!testMemory()) {
        Serial.println("ERROR: Memory test failed!");
        sensorsOperational = false;
    }

    // Check connectivity
    if (!checkConnectivity()) {
        Serial.println("ERROR: Connectivity check failed!");
        sensorsOperational = false;
    }

    if (sensorsOperational) {
        Serial.println("All systems operational.");
    } else {
        Serial.println("Some systems are not operational.");
    }
}

void validateSensors() {
    // Check temperature sensor
    lastTemperatureReading = analogRead(SENSOR_A_PIN);
    if (lastTemperatureReading < 0) {
        Serial.println("WARNING: Sensor A (Temperature) is not operational.");
        sensorsOperational = false;
    } else {
        // Update moving average
        temperatureReadings[readingIndex] = lastTemperatureReading;
        readingIndex = (readingIndex + 1) % MOVING_AVERAGE_SIZE;

        // Calculate moving average
        int averageTemperature = 0;
        for (int i = 0; i < MOVING_AVERAGE_SIZE; i++) {
            averageTemperature += temperatureReadings[i];
        }
        averageTemperature /= MOVING_AVERAGE_SIZE;

        Serial.print("Sensor A (Temperature) average value: ");
        Serial.println(averageTemperature);
        
        // Check if average temperature exceeds threshold
        if (averageTemperature > CRITICAL_TEMP_THRESHOLD) {
            Serial.println("CRITICAL ALERT: Temperature exceeds safe limits! Shutting down...");
            enterSafeMode();
        } else if (averageTemperature > TEMP_THRESHOLD) {
            Serial.println("ALERT: Temperature exceeds warning limits!");
            // Send alert to network or log
        }
    }

    // Check other sensors...
    // Add similar checks for SENSOR_B_PIN, SENSOR_C_PIN, SENSOR_D_PIN, SENSOR_E_PIN, and SENSOR_F_PIN
}

void enterSafeMode() {
    // Disable non-essential sensors to save power
    pinMode(SENSOR_B_PIN, INPUT); // Example: Disable humidity sensor
    pinMode(SENSOR_C_PIN, INPUT); // Example: Disable pressure sensor
    // Add more as needed

    // Optionally, send a shutdown signal or alert
    Serial.println("Entering safe mode to prevent damage.");
    while (true) {
        // Loop indefinitely to prevent further processing
    }
}

bool testMemory() {
    // Simple memory test by allocating and freeing memory
    char *testMemory = (char *)malloc(MEMORY_TEST_SIZE);
    if (testMemory == NULL) {
        return false; // Memory allocation failed
    }
    free(testMemory); // Free allocated memory
    return true; // Memory test passed
}

bool checkConnectivity() {
    // Placeholder for actual connectivity check logic
    // For example, ping a known server or check Wi-Fi status
    return true; // Assume connectivity is fine for this example
}