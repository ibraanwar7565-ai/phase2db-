#!/usr/bin/env python3
from flask import jsonify
from werkzeug.exceptions import HTTPException
from flask import Flask
from flask_cors import CORS
from sqlalchemy import text

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
            r"/api/*": {"origins": ["http://localhost:5173"]},
        },
    )

    db.init_app(app)
    migrate.init_app(app, db)

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "error": {
                "status": 400,
                "code": "bad_request",
                "message": "The request is invalid."
            }
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": {
                "status": 404,
                "code": "not_found",
                "message": "The requested resource was not found."
            }
        }), 404

    @app.errorhandler(409)
    def conflict(error):
        return jsonify({
            "error": {
                "status": 409,
                "code": "conflict",
                "message": "The request conflicts with the current state."
            }
        }), 409

    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error("An internal server error occurred.")

        return jsonify({
            "error": {
                "status": 500,
                "code": "internal_server_error",
                "message": "An unexpected server error occurred."
            }
        }), 500

    @app.get("/api/health")
    def health():
        """Confirms the API is up and can reach the database."""
        db.session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}, 200

    

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
