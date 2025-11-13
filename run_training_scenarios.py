#!/usr/bin/env python3
"""
Training data executor for OTA Agent.
Runs all scenarios from training_data.json to test and train the autonomous agent.
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

BASE_URL = "http://localhost:5001"
TRAINING_DATA_FILE = "training_data.json"
RESULTS_DIR = "training_results"

def load_training_data():
    """Load training scenarios from JSON file."""
    with open(TRAINING_DATA_FILE, 'r') as f:
        return json.load(f)

def run_scenario(scenario, delay=2):
    """Execute a single training scenario."""
    payload = {
        "device_id": scenario["device_id"],
        "event_details": scenario["event_details"]
    }
    
    print(f"\n{'='*80}")
    print(f"Scenario {scenario['id']}: {scenario['category']}")
    print(f"{'='*80}")
    print(f"Event: {scenario['event_details']}")
    print(f"Severity: {scenario['severity']}")
    print(f"Context: {scenario['context']}")
    print(f"Expected Actions: {', '.join(scenario['expected_actions'])}")
    print(f"\nSending to agent...")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/trigger-agent",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minute timeout for complex scenarios
        )
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Success (took {elapsed_time:.2f}s)")
            print(f"Agent Response: {result.get('agent_output', 'No output')[:300]}...")
            
            return {
                "scenario_id": scenario["id"],
                "status": "success",
                "elapsed_time": elapsed_time,
                "agent_output": result.get('agent_output', ''),
                "timestamp": datetime.now().isoformat()
            }
        else:
            print(f"\n❌ Failed with status {response.status_code}")
            print(f"Error: {response.text}")
            
            return {
                "scenario_id": scenario["id"],
                "status": "failed",
                "error": response.text,
                "timestamp": datetime.now().isoformat()
            }
    except requests.exceptions.Timeout:
        print(f"\n⏱️ Timeout after 120 seconds")
        return {
            "scenario_id": scenario["id"],
            "status": "timeout",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        return {
            "scenario_id": scenario["id"],
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    finally:
        time.sleep(delay)

def save_results(results, metadata):
    """Save training results to file."""
    Path(RESULTS_DIR).mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"{RESULTS_DIR}/training_results_{timestamp}.json"
    
    output = {
        "metadata": metadata,
        "execution_time": datetime.now().isoformat(),
        "results": results,
        "summary": {
            "total_scenarios": len(results),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "timeout": sum(1 for r in results if r["status"] == "timeout"),
            "errors": sum(1 for r in results if r["status"] == "error"),
            "average_time": sum(r.get("elapsed_time", 0) for r in results) / len(results) if results else 0
        }
    }
    
    with open(results_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📊 Results saved to: {results_file}")
    return output

def print_summary(summary):
    """Print execution summary."""
    print(f"\n{'='*80}")
    print("TRAINING EXECUTION SUMMARY")
    print(f"{'='*80}")
    print(f"Total Scenarios: {summary['total_scenarios']}")
    print(f"✅ Successful: {summary['successful']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"⏱️ Timeout: {summary['timeout']}")
    print(f"🔥 Errors: {summary['errors']}")
    print(f"⏰ Average Time: {summary['average_time']:.2f}s")
    print(f"{'='*80}")

def run_all_scenarios(start_from=1, limit=None, categories=None, delay=2):
    """Run all training scenarios with optional filtering."""
    print("🤖 OTA Agent Training Data Executor")
    print("="*80)
    
    # Check server health
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Server health check failed!")
            return
    except:
        print("❌ Cannot connect to server. Make sure it's running: python run.py")
        return
    
    print("✅ Server is running\n")
    
    # Load training data
    training_data = load_training_data()
    scenarios = training_data["training_scenarios"]
    metadata = training_data["metadata"]
    
    # Filter scenarios
    if categories:
        scenarios = [s for s in scenarios if s["category"] in categories]
        print(f"Filtering by categories: {', '.join(categories)}")
    
    if start_from > 1:
        scenarios = [s for s in scenarios if s["id"] >= start_from]
        print(f"Starting from scenario {start_from}")
    
    if limit:
        scenarios = scenarios[:limit]
        print(f"Limiting to {limit} scenarios")
    
    print(f"\nExecuting {len(scenarios)} scenarios...")
    print(f"Delay between scenarios: {delay}s\n")
    
    # Execute scenarios
    results = []
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[{i}/{len(scenarios)}]")
        result = run_scenario(scenario, delay=delay)
        results.append(result)
    
    # Save and display results
    output = save_results(results, metadata)
    print_summary(output["summary"])
    
    return output

def run_by_category(category, delay=2):
    """Run all scenarios in a specific category."""
    print(f"🎯 Running scenarios for category: {category}")
    return run_all_scenarios(categories=[category], delay=delay)

def run_sample(count=10, delay=2):
    """Run a sample of scenarios for quick testing."""
    print(f"🎲 Running {count} sample scenarios")
    return run_all_scenarios(limit=count, delay=delay)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "sample":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            run_sample(count=count)
        
        elif command == "category":
            if len(sys.argv) < 3:
                print("Usage: python run_training_scenarios.py category <category_name>")
                print("Available categories:")
                data = load_training_data()
                for cat in data["metadata"]["categories"]:
                    print(f"  - {cat}")
            else:
                category = sys.argv[2]
                run_by_category(category)
        
        elif command == "range":
            start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
            run_all_scenarios(start_from=start, limit=limit)
        
        elif command == "all":
            run_all_scenarios()
        
        else:
            print("Unknown command. Available commands:")
            print("  sample [count]           - Run sample scenarios (default: 10)")
            print("  category <name>          - Run all scenarios in a category")
            print("  range <start> [limit]    - Run scenarios from start with optional limit")
            print("  all                      - Run all 100 scenarios")
    else:
        # Default: run sample
        run_sample(count=10)
