#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI conversion works.
Run this after starting the server to test the endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_health_endpoint():
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_trigger_agent_endpoint():
    """Test the trigger-agent endpoint with policy."""
    test_payload = {
        "device_id": "device-001",
        "event_details": "sensor_A_threshold_exceeded",
        "policy": "When sensor A exceeds threshold, activate sensor B monitoring"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/trigger-agent",
            json=test_payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Trigger agent status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Trigger agent test failed: {e}")
        return False

def test_autonomous_agent_endpoint():
    """Test the autonomous trigger-agent endpoint (no policy)."""
    test_payload = {
        "device_id": "device-001",
        "event_details": "sensor_A_temperature_85_celsius_sustained_high_reading"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/trigger-agent",
            json=test_payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Autonomous agent status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Autonomous agent test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing FastAPI endpoints...")
    print("Make sure the server is running first with: python run.py")
    print()
    
    health_ok = test_health_endpoint()
    print()
    
    if health_ok:
        print("Testing Policy-Driven Mode:")
        agent_ok = test_trigger_agent_endpoint()
        print()
        
        print("Testing Autonomous Mode:")
        autonomous_ok = test_autonomous_agent_endpoint()
        print()
        
        if health_ok and agent_ok and autonomous_ok:
            print("✅ All tests passed! Both policy-driven and autonomous modes work!")
        else:
            print("❌ Some tests failed")
    else:
        print("❌ Health check failed, skipping agent tests")