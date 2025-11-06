#!/bin/bash
# Curl examples for OTA Agent API testing
# Make sure the server is running first: python run.py

BASE_URL="http://localhost:5001"

echo "🚀 OTA Agent API - Curl Examples"
echo "================================="

# Health check
echo -e "\n1. Health Check:"
curl -X GET "$BASE_URL/health" \
  -H "Content-Type: application/json" | jq '.'

# Basic sensor threshold
echo -e "\n2. Temperature Threshold Exceeded:"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "sensor_A_threshold_exceeded",
    "policy": "When sensor A exceeds threshold, activate sensor B monitoring"
  }' | jq '.'

# Environmental monitoring
echo -e "\n3. Low Light Detection:"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "sensor_D_low_light_detected",
    "policy": "When light intensity drops below 10 lux, switch to night mode and activate motion sensor"
  }' | jq '.'

# Power management
echo -e "\n4. Low Battery Alert:"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "battery_level_15_percent",
    "policy": "When battery drops below 20%, disable non-essential sensors and reduce transmission frequency"
  }' | jq '.'

# Motion detection
echo -e "\n5. Motion Detected:"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "sensor_E_motion_detected",
    "policy": "When motion is detected, activate all sensors for 30 seconds then return to normal mode"
  }' | jq '.'

# Critical temperature
echo -e "\n6. Critical Temperature:"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "sensor_A_critical_temperature_85C",
    "policy": "When temperature exceeds 85°C, immediately activate cooling protocol and reduce CPU frequency"
  }' | jq '.'

# Firmware update
echo -e "\n7. Firmware Update Available:"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "firmware_update_available_v2.1",
    "policy": "When firmware update is available, download during low activity hours and verify integrity"
  }' | jq '.'

# Security alert
echo -e "\n8. Security Alert:"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "unauthorized_access_attempt",
    "policy": "When unauthorized access is detected, lock device, log incident, and alert administrator"
  }' | jq '.'

# Multiple events
echo -e "\n9. Multiple Critical Events:"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "multiple_events: temperature_high, motion_detected, low_battery",
    "policy": "When multiple critical events occur simultaneously, prioritize safety protocols and emergency data transmission"
  }' | jq '.'

# System maintenance
echo -e "\n10. System Health Check:"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "scheduled_health_check",
    "policy": "Perform comprehensive system health check including sensor validation, memory test, and connectivity verification"
  }' | jq '.'

echo -e "\n✅ All curl examples completed!"