import os


class Config:
    """Base settings shared by every environment.

    Values are read from environment variables so no secrets live in the code.
    Member 2 will load them from a .env file (python-dotenv) on top of this.
    """

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/smartpesa_dev",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret")
    JSON_SORT_KEYS = False


class TestConfig(Config):
    """In-memory SQLite so tests run without a PostgreSQL server."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
