# LangChain-Powered Auto-OTA Agent

## 🚀 What is this project?

This is an **Autonomous IoT Firmware Management System** that uses AI (LangChain + OpenAI) to automatically generate, modify, and deploy firmware updates for IoT devices based on real-time events and policies.

Think of it as an AI firmware engineer that:
- Monitors IoT device events (sensor readings, alerts, etc.)
- Analyzes the situation using predefined policies
- Automatically writes new Arduino C++ firmware code
- Deploys the updated firmware via Over-The-Air (OTA) updates

## 🎯 The Problem This Solves

Traditional IoT firmware management requires:
- Manual code updates for each device scenario
- Human intervention for every policy change
- Time-consuming deployment cycles
- Risk of human error in critical situations

**This system automates the entire process**, allowing IoT devices to adapt their behavior autonomously based on real-world conditions.

## 🏗️ How It Works

### Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   IoT Device    │───▶│   FastAPI Server │───▶│  LangChain AI   │
│  (sends events) │    │  (receives POST) │    │     Agent       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Device DB      │    │  Firmware Tools │
                       │   (db.json)      │    │ (read/write/OTA)│
                       └──────────────────┘    └─────────────────┘
```

### Step-by-Step Workflow

1. **Event Trigger**: IoT device sends a POST request with:
   - `device_id`: Which device is reporting
   - `event_details`: What happened (e.g., "temperature exceeded 85°C")
   - `policy`: What should be done (e.g., "activate cooling protocol")

2. **AI Agent Processing**: The LangChain agent:
   - Reads current device configuration from database
   - Analyzes existing firmware code
   - Generates new Arduino C++ code implementing the policy
   - Saves the new firmware with timestamp versioning

3. **OTA Deployment**: Simulates pushing the new firmware to the device

4. **Database Update**: Updates device state and version history

## 📁 Project Structure

```
├── ota_agent/                 # Main application package
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Application entry point & server startup
│   ├── config.py             # Configuration management
│   ├── app.py                # FastAPI application & routes
│   ├── agent.py              # LangChain AI agent implementation
│   ├── database.py           # Device state management
│   └── tools.py              # AI agent tools (read/write firmware, OTA)
├── firmware/                 # Generated firmware files
│   └── device-001/           # Device-specific firmware versions
│       ├── v1.0.cpp          # Initial firmware
│       └── v20251104*.cpp    # AI-generated versions
├── db.json                   # Device database (sensor schemas, versions)
├── run.py                    # Simple entry point
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (OpenAI API key)
├── test_api.py              # Basic API testing
├── demo_requests.py         # Comprehensive test scenarios
└── curl_examples.sh         # Quick curl-based testing
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- OpenAI API key

### Step 1: Clone and Install
```bash
git clone <repository-url>
cd LangChain-Powered-Auto-OTA-Agent
pip install -r requirements.txt
```

### Step 2: Configure Environment
Create/edit `.env` file:
```bash
OPENAI_API_KEY="your-openai-api-key-here"
```

### Step 3: Start the Server
```bash
python run.py
```

The server will start on `http://localhost:5001`

## 🧪 Testing the System

### Quick Health Check
```bash
curl http://localhost:5001/health
```

### Basic Event Test
```bash
curl -X POST http://localhost:5001/trigger-agent \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "event_details": "sensor_A_threshold_exceeded",
    "policy": "When sensor A exceeds threshold, activate sensor B monitoring"
  }'
```

### Comprehensive Testing
```bash
# Python-based comprehensive testing
python demo_requests.py

# Or quick curl examples
./curl_examples.sh
```

## 📊 Example Scenarios

### 1. Temperature Alert
**Event**: `"sensor_A_critical_temperature_85C"`
**Policy**: `"When temperature exceeds 85°C, immediately activate cooling protocol"`
**Result**: AI generates firmware that activates cooling fans and reduces CPU frequency

### 2. Low Battery
**Event**: `"battery_level_15_percent"`
**Policy**: `"When battery drops below 20%, disable non-essential sensors"`
**Result**: AI modifies firmware to turn off humidity and GPS sensors, keeping only critical temperature monitoring

### 3. Motion Detection
**Event**: `"sensor_E_motion_detected"`
**Policy**: `"When motion is detected, activate all sensors for 30 seconds"`
**Result**: AI creates firmware that temporarily enables all sensors with a timer

## 🔧 Key Components Explained

### 1. FirmwareAgent (`agent.py`)
- **Purpose**: The AI brain that processes events and generates firmware
- **Technology**: LangChain + OpenAI GPT-4
- **Process**: Receives events → Analyzes current state → Generates new C++ code → Triggers deployment

### 2. DeviceDatabase (`database.py`)
- **Purpose**: Manages device configurations and firmware versions
- **Storage**: JSON file with sensor schemas, current firmware paths, version history
- **Functions**: Read device state, update firmware paths, initialize new devices

### 3. Tools (`tools.py`)
- **Purpose**: Provides AI agent with capabilities to interact with the system
- **Available Tools**:
  - `read_current_firmware`: Get existing code
  - `write_new_firmware`: Save new code with versioning
  - `get_device_state_tool`: Read device configuration
  - `trigger_ota_flash`: Simulate firmware deployment

### 4. FastAPI Server (`app.py`)
- **Purpose**: HTTP API for receiving device events
- **Endpoints**:
  - `GET /health`: System health check
  - `POST /trigger-agent`: Process device events

## 🎛️ Device Configuration

Each device has a sensor schema in `db.json`:
```json
{
  "device-001": {
    "current_firmware_path": "firmware/device-001/v20251104221103.cpp",
    "sensor_schema": {
      "A": {"type": "temperature", "pin": 1, "unit": "celsius"},
      "B": {"type": "humidity", "pin": 2, "unit": "percentage"},
      "C": {"type": "pressure", "pin": 3, "unit": "pascal"},
      "D": {"type": "light_intensity", "pin": 4, "unit": "lux"},
      "E": {"type": "motion", "pin": 5, "unit": "boolean"},
      "F": {"type": "gps_latitude", "pin": 6, "unit": "degrees"}
    },
    "version_history": ["firmware/device-001/v1.0.cpp", "..."]
  }
}
```

## 🚀 Real-World Applications

- **Smart Agriculture**: Automatically adjust irrigation based on soil moisture
- **Industrial Monitoring**: Modify sensor behavior based on equipment conditions
- **Smart Buildings**: Adapt HVAC and lighting based on occupancy patterns
- **Environmental Monitoring**: Change sampling rates based on weather conditions
- **Security Systems**: Update detection algorithms based on threat levels

## 🔮 Future Enhancements

- **Multi-device orchestration**: Coordinate firmware updates across device fleets
- **Machine learning integration**: Learn from device behavior patterns
- **Real OTA deployment**: Integration with actual IoT platforms
- **Rollback capabilities**: Automatic firmware rollback on failures
- **Advanced testing**: Firmware simulation and validation before deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ using LangChain, FastAPI, and OpenAI**