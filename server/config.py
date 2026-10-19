# Load environment variables from the local .env file.
# Existing system environment variables take precedence.
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# .env.example lives in the repo root, so look there; server/.env also works.
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

_db_url = os.environ.get("DATABASE_URL")
if _db_url and _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _db_url
    ...

class TestConfig(Config):
    TESTING = True

    # Use an in-memory SQLite database for tests.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    # Testing does not require the development secret.
    SECRET_KEY = "test-only-secret"