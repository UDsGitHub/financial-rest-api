import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY")
    ALPHA_VANTAGE_BASE_URL: str = os.getenv("ALPHA_VANTAGE_BASE_URL")
    REDIS_URL: str = os.getenv("REDIS_URL")
    REDIS_PORT: str = os.getenv("REDIS_PORT")
    REDIS_USERNAME: str = os.getenv("REDIS_USERNAME")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD")

config = Config()