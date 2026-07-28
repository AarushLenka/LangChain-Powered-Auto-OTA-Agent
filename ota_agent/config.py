import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DB_FILE = "db.json"
    FIRMWARE_DIR = "firmware"            # generated .cpp source
    FIRMWARE_STORE_DIR = "firmware_store"  # compiled .bin served for OTA
    MANIFEST_FILE = "manifest.json"     # device_id -> latest version + bin path
    FLEET_STATE_FILE = "fleet_state.json"  # device_id -> latest sensor reading
    # A node's reading older than this (seconds) is flagged stale in fleet context,
    # so the agent doesn't treat a lagging node as evidence of a live correlation.
    FLEET_STALENESS_SECONDS = 60
    SERVER_PORT = 5001
    DEBUG = True
    LLM_MODEL = "gpt-4o-mini"
    LLM_TEMPERATURE = 0.2
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set")