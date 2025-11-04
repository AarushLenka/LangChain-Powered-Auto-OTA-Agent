from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import traceback
from .agent import FirmwareAgent


class EventRequest(BaseModel):
    device_id: str
    event_details: str
    policy: str


class HealthResponse(BaseModel):
    status: str


class EventResponse(BaseModel):
    success: bool
    agent_output: str


def create_app(agent: FirmwareAgent) -> FastAPI:
    """Factory function to create and configure FastAPI app."""
    app = FastAPI(title="OTA Agent", description="Autonomous IoT Firmware Management System")
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(status="healthy")
    
    @app.post("/trigger-agent", response_model=EventResponse)
    async def handle_event(request: EventRequest):
        """Handle incoming device events and trigger agent."""
        print(f"\n\n--- New Event for {request.device_id} ---")
        print(f"Event: {request.event_details}")
        print(f"Policy: {request.policy}")
        print("--- Invoking Agent ---")

        input_string = FirmwareAgent.create_agent_prompt(
            request.device_id, request.event_details, request.policy
        )

        try:
            result = agent.invoke({"input": input_string})
            return EventResponse(
                success=True,
                agent_output=result.get('output', '')
            )
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
    
    return app