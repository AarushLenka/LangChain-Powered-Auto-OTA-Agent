import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DB_FILE = "db.json"
    FIRMWARE_DIR = "firmware"
    FLASK_PORT = 5001
    FLASK_DEBUG = True
    LLM_MODEL = "gpt-4o-mini"
    LLM_TEMPERATURE = 0.2
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set")