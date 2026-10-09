# Load environment variables from the local .env file.
# Existing system environment variables take precedence.
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JSON_SORT_KEYS = False


class TestConfig(Config):
    TESTING = True

    # Use an in-memory SQLite database for tests.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    # Testing does not require the development secret.
    SECRET_KEY = "test-only-secret"