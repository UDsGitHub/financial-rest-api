import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY")
    ALPHA_VANTAGE_BASE_URL: str = os.getenv("ALPHA_VANTAGE_BASE_URL")

config = Config()