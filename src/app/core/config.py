import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local", override=True)

class Config:
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY")
    ALPHA_VANTAGE_BASE_URL: str = os.getenv(
        "ALPHA_VANTAGE_BASE_URL", "https://www.alphavantage.co/query"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_USERNAME: str | None = os.getenv("REDIS_USERNAME") or None
    REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD") or None
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "86400"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "4"))

config = Config()