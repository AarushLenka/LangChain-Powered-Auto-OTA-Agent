#!/usr/bin/env python3
"""
Autonomous OTA Agent demonstrations - no policies required!
The AI agent makes intelligent decisions based on events alone.
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

def make_autonomous_request(payload, description):
    """Helper function to make autonomous POST requests."""
    print(f"\n{'='*70}")
    print(f"AUTONOMOUS TEST: {description}")
    print(f"{'='*70}")
    print(f"Event: {payload['event_details']}")
    print("AI Decision: Let the agent decide autonomously...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/trigger-agent",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"\nStatus Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Agent Response: {result.get('agent_output', 'No output')[:200]}...")
        else:
            print(f"Error Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Request failed: {e}")
        return False

def demo_autonomous_sensor_scenarios():
    """Test autonomous sensor management decisions."""
    
    # Temperature spike - let AI decide what to do
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "sensor_A_reading_87_celsius_sustained_for_5_minutes"
    }, "High Temperature Sustained - AI Autonomous Response")
    
    # Multiple sensor anomalies
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "sensors_A_C_D_showing_inconsistent_readings_possible_calibration_issue"
    }, "Sensor Calibration Issue - AI Diagnostic Decision")
    
    # Rapid sensor fluctuations
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "sensor_D_light_intensity_fluctuating_rapidly_between_0_and_1000_lux"
    }, "Sensor Instability - AI Stabilization Strategy")

def demo_autonomous_power_scenarios():
    """Test autonomous power management decisions."""
    
    # Battery degradation
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "battery_voltage_dropped_from_4.2V_to_3.4V_in_2_hours"
    }, "Rapid Battery Drain - AI Power Optimization")
    
    # Solar charging opportunity
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "solar_panel_generating_optimal_power_sunny_conditions_detected"
    }, "Optimal Solar Conditions - AI Resource Utilization")
    
    # Power fluctuations
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "power_supply_unstable_voltage_varying_between_3.0V_and_4.5V"
    }, "Unstable Power Supply - AI Stability Management")

def demo_autonomous_environmental_scenarios():
    """Test autonomous environmental adaptation."""
    
    # Weather change detection
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "pressure_dropping_rapidly_temperature_falling_storm_approaching"
    }, "Storm Approaching - AI Weather Response")
    
    # Day/night transition
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "light_sensor_indicates_sunset_transition_to_night_mode_needed"
    }, "Day-Night Transition - AI Mode Switching")
    
    # Seasonal adaptation
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "average_temperature_dropped_10_degrees_winter_mode_optimization_needed"
    }, "Seasonal Change - AI Long-term Adaptation")

def demo_autonomous_connectivity_scenarios():
    """Test autonomous network management decisions."""
    
    # Network congestion
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "wifi_network_congested_packet_loss_30_percent_slow_response_times"
    }, "Network Congestion - AI Communication Strategy")
    
    # Connection quality degradation
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "signal_strength_weak_connection_intermittent_data_transmission_failing"
    }, "Poor Signal Quality - AI Connectivity Optimization")
    
    # Multiple network options
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "multiple_wifi_networks_available_need_to_select_optimal_connection"
    }, "Network Selection - AI Connection Optimization")

def demo_autonomous_security_scenarios():
    """Test autonomous security response decisions."""
    
    # Unusual access patterns
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "unusual_data_access_patterns_detected_potential_security_concern"
    }, "Security Anomaly - AI Threat Response")
    
    # Physical tampering
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "accelerometer_detects_device_moved_unexpectedly_possible_tampering"
    }, "Physical Tampering - AI Security Protocol")
    
    # Data integrity issues
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "sensor_data_checksum_failures_data_corruption_detected"
    }, "Data Corruption - AI Integrity Management")

def demo_autonomous_maintenance_scenarios():
    """Test autonomous maintenance and optimization decisions."""
    
    # Performance degradation
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "system_response_time_increased_50_percent_performance_degradation"
    }, "Performance Issues - AI System Optimization")
    
    # Memory management
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "memory_usage_approaching_90_percent_potential_system_instability"
    }, "Memory Pressure - AI Resource Management")
    
    # Predictive maintenance
    make_autonomous_request({
        "device_id": "device-001",
        "event_details": "sensor_readings_trending_toward_failure_patterns_preventive_action_needed"
    }, "Predictive Maintenance - AI Proactive Response")

def run_autonomous_demos():
    """Run all autonomous demonstration scenarios."""
    print("🤖 Starting Autonomous OTA Agent Demonstrations")
    print("The AI will make intelligent decisions without explicit policies!")
    print("=" * 70)
    
    # Check server health
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("❌ Server health check failed!")
            return
    except:
        print("❌ Cannot connect to server. Make sure it's running: python run.py")
        return
    
    print("✅ Server is running, starting autonomous demonstrations...\n")
    
    demo_autonomous_sensor_scenarios()
    time.sleep(2)
    
    demo_autonomous_power_scenarios()
    time.sleep(2)
    
    demo_autonomous_environmental_scenarios()
    time.sleep(2)
    
    demo_autonomous_connectivity_scenarios()
    time.sleep(2)
    
    demo_autonomous_security_scenarios()
    time.sleep(2)
    
    demo_autonomous_maintenance_scenarios()
    
    print(f"\n{'='*70}")
    print("🎉 Autonomous demonstrations completed!")
    print("Check the firmware/ directory to see all the AI-generated solutions!")
    print(f"{'='*70}")

if __name__ == "__main__":
    run_autonomous_demos()