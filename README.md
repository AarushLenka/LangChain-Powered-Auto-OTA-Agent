# OTA Agent - Autonomous IoT Firmware Management System

An autonomous system for managing IoT device firmware using AI agents.

## Recent Changes

### v1.0.1 Updates
- **Converted from Flask to FastAPI** for better performance and automatic API documentation
- **Fixed database schema consistency** - now uses detailed sensor schema matching db.json
- **Improved error handling** throughout the database operations
- **Removed code duplication** by eliminating redundant files
- **Updated configuration** to use consistent naming conventions

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Running the Server

```bash
python run.py
```

The server will start on port 5001 by default.

## API Endpoints

### Health Check
```
GET /health
```

### Trigger Agent
```
POST /trigger-agent
Content-Type: application/json

{
  "device_id": "device-001",
  "event_details": "sensor_A_threshold_exceeded", 
  "policy": "When sensor A exceeds threshold, activate sensor B monitoring"
}
```

## Testing

Run the test script to verify the API is working:
```bash
python test_api.py
```

## API Documentation

With FastAPI, automatic interactive API documentation is available at:
- Swagger UI: http://localhost:5001/docs
- ReDoc: http://localhost:5001/redoc

## Architecture

- **FastAPI** - Modern web framework with automatic validation
- **LangChain** - AI agent framework for autonomous firmware management
- **Pydantic** - Data validation and serialization
- **JSON Database** - Simple file-based device state storage