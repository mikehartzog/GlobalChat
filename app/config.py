from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")

    class Config:
        env_file = ".env"

settings = Settings()

# Add this temporary debug print
print(f"API Key starts with: {settings.OPENAI_API_KEY[:5]}..." if settings.OPENAI_API_KEY else "No API key found")