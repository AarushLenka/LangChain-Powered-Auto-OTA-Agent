#!/bin/bash
# Autonomous Curl examples - No policies required!
# The AI agent makes intelligent decisions based on events alone.

BASE_URL="http://localhost:5001"

echo "🤖 Autonomous OTA Agent API - Curl Examples"
echo "The AI decides what to do based on events alone!"
echo "=============================================="

# Health check
echo -e "\n1. Health Check:"
curl -X GET "$BASE_URL/health" \
  -H "Content-Type: application/json" | jq '.'

# Temperature emergency - AI decides response
echo -e "\n2. Temperature Emergency (AI Autonomous Decision):"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "sensor_A_temperature_critical_89_celsius_immediate_action_required"
  }' | jq '.'

# Battery crisis - AI power management
echo -e "\n3. Battery Crisis (AI Power Management):"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "battery_voltage_critically_low_3.1V_device_shutdown_imminent"
  }' | jq '.'

# Sensor malfunction - AI diagnostic response
echo -e "\n4. Sensor Malfunction (AI Diagnostic):"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "sensor_B_humidity_returning_impossible_values_150_percent_malfunction_detected"
  }' | jq '.'

# Network failure - AI connectivity strategy
echo -e "\n5. Network Failure (AI Connectivity Strategy):"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "wifi_connection_lost_cellular_backup_unavailable_isolated_operation_mode"
  }' | jq '.'

# Motion security alert - AI security response
echo -e "\n6. Security Alert (AI Security Protocol):"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "motion_sensor_triggered_3AM_unauthorized_access_suspected"
  }' | jq '.'

# Environmental adaptation - AI weather response
echo -e "\n7. Storm Detection (AI Weather Adaptation):"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "barometric_pressure_dropping_rapidly_wind_speed_increasing_severe_weather_approaching"
  }' | jq '.'

# Performance degradation - AI optimization
echo -e "\n8. Performance Issues (AI System Optimization):"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "system_lag_detected_sensor_sampling_delayed_memory_fragmentation_suspected"
  }' | jq '.'

# Multi-sensor coordination - AI orchestration
echo -e "\n9. Multi-Sensor Coordination (AI Orchestration):"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "all_sensors_active_simultaneously_data_overload_processing_bottleneck_detected"
  }' | jq '.'

# Predictive maintenance - AI proactive response
echo -e "\n10. Predictive Maintenance (AI Proactive Response):"
curl -X POST "$BASE_URL/trigger-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "sensor_drift_patterns_indicate_calibration_needed_within_48_hours_preventive_action"
  }' | jq '.'

echo -e "\n✅ All autonomous curl examples completed!"
echo "🤖 The AI made intelligent decisions without any policies!"