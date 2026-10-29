"""
Vercel serverless entry point for FixLink.
Provides a resilient WSGI callable that:
1. Returns an instant 200 OK for /api/ping (diagnostic endpoint).
2. Lazy-loads the Flask application on first request to minimize cold-start latency.
3. Catches and renders full startup or runtime tracebacks directly in the browser.
"""
import os
import sys
import time
import logging
import traceback

# Ensure the project root is on sys.path so 'app' is importable
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_flask_app = None
_startup_error = None


def get_application():
    global _flask_app, _startup_error
    if _flask_app is not None:
        return _flask_app
    if _startup_error is not None:
        raise _startup_error

    try:
        t0 = time.time()
        logger.info("Initializing FixLink Flask application...")
        from app import create_app
        _flask_app = create_app()
        logger.info("FixLink app initialized successfully in %.3fs.", time.time() - t0)
        return _flask_app
    except Exception as exc:
        _startup_error = exc
        logger.error("FATAL: create_app() failed on Vercel cold start:\n%s", traceback.format_exc())
        raise


def app(environ, start_response):
    """WSGI callable dispatched by Vercel runtime."""
    path = environ.get('PATH_INFO', '')

    # Diagnostic ping endpoint: always succeeds without touching DB or Flask
    if path == '/api/ping':
        status = '200 OK'
        headers = [
            ('Content-Type', 'application/json'),
            ('Cache-Control', 'no-cache, no-store, must-revalidate'),
        ]
        start_response(status, headers)
        return [b'{"status":"ok","service":"fixlink","timestamp":' + str(int(time.time())).encode() + b'}']

    try:
        flask_instance = get_application()
        return flask_instance(environ, start_response)
    except Exception:
        err_trace = traceback.format_exc()
        status = '500 Internal Server Error'
        headers = [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'no-cache, no-store, must-revalidate'),
        ]
        start_response(status, headers)
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>FixLink Application Error</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 40px 20px; }}
        .card {{ max-width: 900px; margin: 0 auto; background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
        h1 {{ color: #f43f5e; font-size: 22px; margin-top: 0; }}
        p {{ color: #94a3b8; font-size: 14px; }}
        pre {{ background: #020617; color: #38bdf8; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 13px; line-height: 1.5; border: 1px solid #1e293b; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>FixLink Startup / Runtime Exception</h1>
        <p>An exception occurred during application execution on Vercel:</p>
        <pre>{err_trace}</pre>
    </div>
</body>
</html>"""
        return [html.encode('utf-8')]


# Export all standard WSGI targets for Vercel / Gunicorn
application = app
handler = app
