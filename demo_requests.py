#!/usr/bin/env python3
"""
Comprehensive POST request demonstrations for OTA Agent testing.
Run this after starting the server to test various scenarios.
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

def make_request(payload, description):
    """Helper function to make POST requests with consistent formatting."""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"{'='*60}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/trigger-agent",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Request failed: {e}")
        return False

def demo_sensor_threshold_scenarios():
    """Test various sensor threshold scenarios."""
    
    # Temperature threshold exceeded
    make_request({
        "device_id": "device-001",
        "event_details": "sensor_A_threshold_exceeded",
        "policy": "When sensor A exceeds threshold, activate sensor B monitoring"
    }, "Temperature Sensor Threshold Exceeded")
    
    # Multiple sensor activation
    make_request({
        "device_id": "device-001", 
        "event_details": "multiple_sensors_active",
        "policy": "When multiple sensors are active, optimize power consumption by reducing sampling frequency"
    }, "Multiple Sensors Active - Power Optimization")
    
    # Critical temperature alert
    make_request({
        "device_id": "device-001",
        "event_details": "sensor_A_critical_temperature_85C",
        "policy": "When temperature exceeds 85°C, immediately activate cooling protocol and reduce CPU frequency"
    }, "Critical Temperature Alert")

def demo_environmental_scenarios():
    """Test environmental monitoring scenarios."""
    
    # Low light conditions
    make_request({
        "device_id": "device-001",
        "event_details": "sensor_D_low_light_detected",
        "policy": "When light intensity drops below 10 lux, switch to night mode and activate motion sensor"
    }, "Low Light Detection - Night Mode")
    
    # High pressure system
    make_request({
        "device_id": "device-001",
        "event_details": "sensor_C_pressure_spike_detected",
        "policy": "When pressure increases rapidly, log GPS coordinates and increase sensor sampling rate"
    }, "Pressure Spike Detection")
    
    # Motion detection
    make_request({
        "device_id": "device-001",
        "event_details": "sensor_E_motion_detected",
        "policy": "When motion is detected, activate all sensors for 30 seconds then return to normal mode"
    }, "Motion Detection - Full Sensor Activation")

def demo_power_management_scenarios():
    """Test power management scenarios."""
    
    # Low battery
    make_request({
        "device_id": "device-001",
        "event_details": "battery_level_15_percent",
        "policy": "When battery drops below 20%, disable non-essential sensors and reduce transmission frequency"
    }, "Low Battery - Power Conservation")
    
    # Sleep mode request
    make_request({
        "device_id": "device-001",
        "event_details": "scheduled_sleep_mode",
        "policy": "Enter deep sleep mode from 2AM to 6AM, wake only for critical alerts"
    }, "Scheduled Sleep Mode")
    
    # Solar charging detected
    make_request({
        "device_id": "device-001",
        "event_details": "solar_charging_active",
        "policy": "When solar charging is active, increase sensor sampling and enable all monitoring features"
    }, "Solar Charging - Enhanced Monitoring")

def demo_connectivity_scenarios():
    """Test connectivity and communication scenarios."""
    
    # WiFi connection lost
    make_request({
        "device_id": "device-001",
        "event_details": "wifi_connection_lost",
        "policy": "When WiFi is lost, store data locally and attempt reconnection every 5 minutes"
    }, "WiFi Connection Lost")
    
    # Firmware update available
    make_request({
        "device_id": "device-001",
        "event_details": "firmware_update_available_v2.1",
        "policy": "When firmware update is available, download during low activity hours and verify integrity"
    }, "Firmware Update Available")
    
    # Network congestion
    make_request({
        "device_id": "device-001",
        "event_details": "network_congestion_detected",
        "policy": "When network congestion is high, reduce data transmission frequency and compress sensor data"
    }, "Network Congestion - Data Optimization")

def demo_security_scenarios():
    """Test security-related scenarios."""
    
    # Unauthorized access attempt
    make_request({
        "device_id": "device-001",
        "event_details": "unauthorized_access_attempt",
        "policy": "When unauthorized access is detected, lock device, log incident, and alert administrator"
    }, "Security Alert - Unauthorized Access")
    
    # Tamper detection
    make_request({
        "device_id": "device-001",
        "event_details": "physical_tamper_detected",
        "policy": "When physical tampering is detected, immediately backup critical data and enter secure mode"
    }, "Physical Tamper Detection")

def demo_maintenance_scenarios():
    """Test maintenance and diagnostic scenarios."""
    
    # Sensor calibration needed
    make_request({
        "device_id": "device-001",
        "event_details": "sensor_calibration_due",
        "policy": "When sensors need calibration, run self-diagnostic routine and adjust readings based on reference values"
    }, "Sensor Calibration Required")
    
    # Memory usage high
    make_request({
        "device_id": "device-001",
        "event_details": "memory_usage_85_percent",
        "policy": "When memory usage exceeds 80%, clear old logs, compress data, and optimize memory allocation"
    }, "High Memory Usage - Cleanup")
    
    # System health check
    make_request({
        "device_id": "device-001",
        "event_details": "scheduled_health_check",
        "policy": "Perform comprehensive system health check including sensor validation, memory test, and connectivity verification"
    }, "Scheduled System Health Check")

def demo_edge_cases():
    """Test edge cases and error scenarios."""
    
    # Invalid sensor reading
    make_request({
        "device_id": "device-001",
        "event_details": "sensor_A_invalid_reading_-999",
        "policy": "When sensor returns invalid reading, attempt recalibration, if failed switch to backup sensor"
    }, "Invalid Sensor Reading")
    
    # Multiple simultaneous events
    make_request({
        "device_id": "device-001",
        "event_details": "multiple_events: temperature_high, motion_detected, low_battery",
        "policy": "When multiple critical events occur simultaneously, prioritize safety protocols and emergency data transmission"
    }, "Multiple Simultaneous Critical Events")
    
    # Unknown device ID
    make_request({
        "device_id": "device-999",
        "event_details": "unknown_device_registration",
        "policy": "When unknown device attempts registration, verify credentials and initialize with default configuration"
    }, "Unknown Device Registration")

def run_all_demos():
    """Run all demonstration scenarios."""
    print("🚀 Starting OTA Agent POST Request Demonstrations")
    print("Make sure the server is running: python run.py")
    
    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("❌ Server health check failed!")
            return
    except:
        print("❌ Cannot connect to server. Make sure it's running on port 5001")
        return
    
    print("✅ Server is running, starting demonstrations...\n")
    
    demo_sensor_threshold_scenarios()
    time.sleep(1)
    
    demo_environmental_scenarios()
    time.sleep(1)
    
    demo_power_management_scenarios()
    time.sleep(1)
    
    demo_connectivity_scenarios()
    time.sleep(1)
    
    demo_security_scenarios()
    time.sleep(1)
    
    demo_maintenance_scenarios()
    time.sleep(1)
    
    demo_edge_cases()
    
    print(f"\n{'='*60}")
    print("🎉 All demonstrations completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    run_all_demos()