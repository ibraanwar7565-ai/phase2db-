#!/usr/bin/env python3
from flask import jsonify
from werkzeug.exceptions import HTTPException
from flask import Flask
from flask_cors import CORS
from sqlalchemy import text
from auth import auth_bp
from budgets import budgets_bp
from transactions import transactions_bp
from errors import api_error
from dashboard import dashboard_bp
from users import users_bp
from mpesa import mpesa_bp
from config import Config
from extensions import db, migrate
import models  # noqa: F401  (registers the models so Flask-Migrate can see them)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY is not configured.")

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL is not configured.")

    CORS(
        app,
        resources={
            r"/api/*": {"origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]},
        },
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(mpesa_bp)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        # Covers 400, 404, 405, 409... with the same JSON shape.
        code = error.name.lower().replace(" ", "_")
        return api_error(error.code, code, error.description)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        db.session.rollback()
        app.logger.exception("Unhandled error")
        return api_error(500, "internal_server_error","An unexpected server error occurred.")
    
    @app.get("/api/health")
    def health():
        """Confirms the API is up and can reach the database."""
        db.session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}, 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5000, debug=True)