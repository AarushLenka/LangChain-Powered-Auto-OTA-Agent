# 🤖 Autonomous IoT Firmware Agent

An AI-powered system that autonomously generates, modifies, and deploys firmware updates for IoT devices based on real-time events. Built with LangChain, OpenAI GPT-4, and FastAPI.

## 🎯 What Does This Do?

Imagine an IoT device that can **rewrite its own firmware** in response to changing conditions - without human intervention. This system makes that possible.

When your IoT device experiences an event (temperature spike, low battery, sensor failure, security threat), it sends a simple message to this agent. The AI analyzes the situation, generates optimized Arduino C++ firmware code, and deploys it via OTA (Over-The-Air) update.

**No policies required. No manual coding. Just autonomous intelligence.**

## ✨ Key Features

- 🧠 **Fully Autonomous**: AI makes intelligent decisions without explicit policies
- 🔧 **Real Firmware Generation**: Creates actual compilable Arduino C++ code
- 📡 **OTA Deployment**: Simulates Over-The-Air firmware updates
- 🎯 **100+ Training Scenarios**: Comprehensive test suite across 10 categories
- 📊 **Version Control**: Tracks all firmware changes with timestamps
- 🔒 **Multi-Domain Intelligence**: Handles temperature, power, sensors, network, security, and more
- ⚡ **Fast Response**: Generates and deploys firmware in seconds

## 🏗️ Architecture

```
┌─────────────────┐
│   IoT Device    │  Sends event: "temperature_critical_90C"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Server │  Receives POST request
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LangChain AI   │  Analyzes event autonomously
│   Agent (GPT-4) │  Makes intelligent decisions
└────────┬────────┘
         │
         ├──────────────────────────────────┐
         ▼                                  ▼
┌─────────────────┐              ┌─────────────────┐
│  Firmware Tools │              │   Device DB     │
│  - Read code    │              │   - Sensors     │
│  - Write code   │              │   - Versions    │
│  - Deploy OTA   │              │   - History     │
└─────────────────┘              └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Generated      │  v20251106234228.cpp
│  Firmware       │  (timestamped versions)
└─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd LangChain-Powered-Auto-OTA-Agent

# Install dependencies
pip install -r requirements.txt

# Configure your OpenAI API key
echo 'OPENAI_API_KEY="your-key-here"' > .env

# Start the server
python run.py
```

Server will start on `http://localhost:5001`

### Your First Autonomous Request

```bash
# Simple event - AI decides what to do
curl -X POST http://localhost:5001/trigger-agent \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "sensor_A_temperature_critical_90_celsius"
  }'
```

The AI will:
1. Read current device configuration
2. Analyze the temperature event
3. Generate optimized firmware with cooling protocols
4. Save new firmware with timestamp
5. Simulate OTA deployment

Check `firmware/device-001/` for the newly generated firmware file!

## 📁 Project Structure

```
├── ota_agent/                      # Core application
│   ├── __init__.py                # Package initialization
│   ├── main.py                    # Server startup & initialization
│   ├── app.py                     # FastAPI routes
│   ├── agent.py                   # LangChain AI agent
│   ├── config.py                  # Configuration management
│   ├── database.py                # Device state management
│   └── tools.py                   # AI tools (read/write/deploy)
│
├── firmware/                      # Generated firmware files
│   └── device-001/
│       ├── v1.0.cpp              # Initial firmware
│       └── v20251106*.cpp        # AI-generated versions
│
├── training_results/              # Training execution results
│
├── db.json                        # Device database
├── training_data.json             # 100 training scenarios
│
├── run.py                         # Server entry point
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables
│
├── test_api.py                    # Basic API tests
├── autonomous_demo.py             # Comprehensive autonomous demos
├── autonomous_curl_examples.sh    # Quick curl tests
├── demo_requests.py               # Policy-driven demos (legacy)
├── curl_examples.sh               # Policy-driven curl (legacy)
└── run_training_scenarios.py      # Training data executor
```

## 🧪 Testing & Demonstrations

### Quick Health Check
```bash
curl http://localhost:5001/health
```

### Basic Testing
```bash
# Test both autonomous and policy-driven modes
python test_api.py
```

### Autonomous Demonstrations
```bash
# Python-based comprehensive demos (18 scenarios)
python autonomous_demo.py

# Quick curl examples (10 scenarios)
./autonomous_curl_examples.sh
```

### Training Suite
```bash
# Run 10 sample scenarios
python run_training_scenarios.py sample

# Run specific category (e.g., security_events)
python run_training_scenarios.py category security_events

# Run all 100 training scenarios (~30-40 minutes)
python run_training_scenarios.py all
```

## 🎓 Training Data

The system includes **100 realistic IoT scenarios** across 10 categories:

| Category | Scenarios | Examples |
|----------|-----------|----------|
| 🌡️ Temperature Management | 10 | Overheating, thermal shock, freezing conditions |
| 🔋 Power Management | 10 | Low battery, solar charging, power optimization |
| 📡 Sensor Diagnostics | 10 | Sensor failures, calibration, drift detection |
| 🌐 Network Connectivity | 10 | WiFi loss, latency, packet loss, isolation |
| 🔒 Security Events | 10 | Unauthorized access, tampering, attacks |
| 🌍 Environmental Adaptation | 10 | Weather changes, day/night, seasonal shifts |
| ⚡ Performance Optimization | 10 | CPU overload, memory pressure, bottlenecks |
| 🔧 Predictive Maintenance | 10 | Component wear, degradation, preventive actions |
| 🎛️ Multi-Sensor Coordination | 10 | Sensor fusion, conflicts, synchronization |
| 🚨 Emergency Protocols | 10 | Fire, water damage, earthquakes, hazards |

Each scenario tests the AI's ability to make intelligent autonomous decisions.

## 💡 How the AI Makes Decisions

The agent uses GPT-4 with deep knowledge of:
- **Arduino/C++ Programming**: Generates compilable embedded code
- **IoT Best Practices**: Industry-standard sensor management
- **Power Optimization**: Battery life and energy efficiency
- **Safety Protocols**: Prevents damage and ensures reliability
- **Security Principles**: Protects against threats and tampering

### Decision-Making Process

1. **Analyze Event**: Understand what happened and why it matters
2. **Read Context**: Get device configuration and current firmware
3. **Evaluate Options**: Consider safety, power, performance, security
4. **Generate Solution**: Write optimized firmware addressing the issue
5. **Deploy Update**: Save and trigger OTA deployment

### Example: Temperature Crisis

**Event**: `"sensor_A_temperature_critical_90_celsius"`

**AI's Autonomous Decisions**:
- Set critical temperature threshold to 90°C
- Implement safety state management
- Add dynamic delay (longer during critical states for power saving)
- Enhanced logging for critical events
- Graceful degradation while maintaining operation

**Generated Firmware**: Complete Arduino C++ code with detailed comments explaining each decision.

## 🔧 API Reference

### Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy"
}
```

### Trigger Agent (Autonomous Mode)
```http
POST /trigger-agent
Content-Type: application/json

{
  "device_id": "device-001",
  "event_details": "battery_voltage_low_3.2V_power_conservation_needed"
}
```

**Response**:
```json
{
  "success": true,
  "agent_output": "The new firmware has been successfully written and deployed..."
}
```

### Trigger Agent (Policy Mode - Backward Compatible)
```http
POST /trigger-agent
Content-Type: application/json

{
  "device_id": "device-001",
  "event_details": "sensor_A_threshold_exceeded",
  "policy": "When sensor A exceeds threshold, activate sensor B monitoring"
}
```

## 📊 Device Configuration

Each device has a sensor schema in `db.json`:

```json
{
  "device-001": {
    "current_firmware_path": "firmware/device-001/v20251106234228.cpp",
    "sensor_schema": {
      "A": {"type": "temperature", "pin": 1, "unit": "celsius"},
      "B": {"type": "humidity", "pin": 2, "unit": "percentage"},
      "C": {"type": "pressure", "pin": 3, "unit": "pascal"},
      "D": {"type": "light_intensity", "pin": 4, "unit": "lux"},
      "E": {"type": "motion", "pin": 5, "unit": "boolean"},
      "F": {"type": "gps_latitude", "pin": 6, "unit": "degrees"}
    },
    "version_history": [
      "firmware/device-001/v1.0.cpp",
      "firmware/device-001/v20251106234228.cpp"
    ]
  }
}
```

## 🎯 Real-World Use Cases

### Smart Agriculture
**Event**: `"soil_moisture_critically_low_irrigation_needed"`
**AI Action**: Activates irrigation sensors, adjusts watering schedules, monitors moisture levels

### Industrial Monitoring
**Event**: `"vibration_sensor_detecting_abnormal_patterns_equipment_failure_risk"`
**AI Action**: Increases monitoring frequency, implements predictive maintenance, alerts operators

### Smart Buildings
**Event**: `"occupancy_detected_after_hours_security_protocol_needed"`
**AI Action**: Activates security sensors, enables motion tracking, logs events

### Environmental Monitoring
**Event**: `"air_quality_degraded_pollution_levels_high"`
**AI Action**: Increases sampling rate, activates additional sensors, triggers alerts

### Energy Management
**Event**: `"grid_power_unstable_switching_to_battery_backup"`
**AI Action**: Optimizes power consumption, prioritizes critical sensors, manages battery life

## 🔮 Advanced Features

### Firmware Versioning
Every firmware update is timestamped and tracked:
- Format: `v{YYYYMMDDHHMMSS}.cpp`
- Example: `v20251106234228.cpp`
- Full version history maintained in database

### Multi-Device Support
Easily extend to multiple devices:
```json
{
  "device-001": { ... },
  "device-002": { ... },
  "device-003": { ... }
}
```

### Training Results Analysis
```bash
# Results saved to training_results/
{
  "summary": {
    "total_scenarios": 100,
    "successful": 98,
    "failed": 2,
    "average_time": 8.5
  }
}
```

## 🛠️ Configuration

### Environment Variables (`.env`)
```bash
OPENAI_API_KEY="your-openai-api-key"
```

### Config Options (`ota_agent/config.py`)
```python
SERVER_PORT = 5001          # API server port
LLM_MODEL = "gpt-4o-mini"   # OpenAI model
LLM_TEMPERATURE = 0.2       # AI creativity (0-1)
DB_FILE = "db.json"         # Database file
FIRMWARE_DIR = "firmware"   # Firmware storage
```

## 📈 Performance

- **Response Time**: 5-15 seconds per firmware generation
- **Firmware Size**: 2-5KB per file
- **Concurrent Requests**: Supports multiple simultaneous events
- **Scalability**: Can manage hundreds of devices

## 🔒 Security Considerations

- API authentication not implemented (add for production)
- Firmware validation recommended before deployment
- Secure storage of OpenAI API keys
- Network security for OTA updates
- Device authentication for production use

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Development Roadmap

- [ ] Real OTA deployment integration (ESP32, Arduino)
- [ ] Multi-device fleet management
- [ ] Web dashboard for monitoring
- [ ] Firmware simulation and testing
- [ ] Machine learning for pattern recognition
- [ ] Automatic rollback on failures
- [ ] A/B testing for firmware updates
- [ ] Integration with IoT platforms (AWS IoT, Azure IoT)

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port 5001 is available
lsof -i :5001

# Verify OpenAI API key
cat .env
```

### No firmware generated
- Check server logs for errors
- Verify OpenAI API key is valid
- Ensure device exists in `db.json`
- Check network connectivity

### Agent timeout
- Increase timeout in `run_training_scenarios.py`
- Check OpenAI API rate limits
- Verify prompt complexity

## 📚 Learn More

- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
- [Arduino Programming Guide](https://www.arduino.cc/reference/en/)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://www.langchain.com/) for AI orchestration
- Powered by [OpenAI GPT-4](https://openai.com/) for intelligent decision-making
- [FastAPI](https://fastapi.tiangolo.com/) for high-performance API
- Inspired by autonomous systems and IoT innovation

---

**Built with ❤️ for the future of autonomous IoT**

*Making IoT devices truly intelligent, one firmware update at a time.*
