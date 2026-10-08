#!/usr/bin/env python3

from flask import Flask
from sqlalchemy import text

from config import Config
from extensions import db, migrate
import models  # noqa: F401  (registers the models so Flask-Migrate can see them)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.get("/api/health")
    def health():
        """Confirms the API is up and can reach the database."""
        db.session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}, 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
