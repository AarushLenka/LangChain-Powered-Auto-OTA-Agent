from flask import Flask, request, jsonify
import traceback
from .agent import FirmwareAgent


def create_app(agent: FirmwareAgent) -> Flask:
    """Factory function to create and configure Flask app."""
    app = Flask(__name__)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy"}), 200
    
    @app.route('/trigger-agent', methods=['POST'])
    def handle_event():
        """Handle incoming device events and trigger agent."""
        data = request.json
        device_id = data.get("device_id")
        event_details = data.get("event_details")
        policy = data.get("policy")

        if not all([device_id, event_details, policy]):
            return jsonify({
                "error": "Missing required fields: device_id, event_details, or policy"
            }), 400

        print(f"\n\n--- New Event for {device_id} ---")
        print(f"Event: {event_details}")
        print(f"Policy: {policy}")
        print("--- Invoking Agent ---")

        input_string = FirmwareAgent.create_agent_prompt(
            device_id, event_details, policy
        )

        try:
            result = agent.invoke({"input": input_string})
            return jsonify({
                "success": True,
                "agent_output": result.get('output')
            })
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    return app