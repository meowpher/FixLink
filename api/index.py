"""
Vercel serverless entry point for FixLink.
This file is loaded once per cold start by the @vercel/python runtime.
It MUST export a WSGI-compatible 'app' object at module level.
"""
import os
import sys
import logging
import traceback

# Ensure the project root is on sys.path so 'app' is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from app import create_app
    app = create_app()
    logger.info("FixLink app created successfully.")
except Exception as e:
    logger.error("FATAL: Failed to create Flask app on Vercel cold start.")
    logger.error(traceback.format_exc())

    # Emit a minimal WSGI app that returns 500 with the error message
    # so Vercel shows something useful instead of a blank 500.
    from flask import Flask, jsonify
    _err_msg = str(e)

    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def startup_error(path):
        return (
            f"<h1>Application Startup Error</h1><pre>{_err_msg}</pre>",
            500,
        )

# Vercel/Gunicorn looks for 'app' at module level
application = app
