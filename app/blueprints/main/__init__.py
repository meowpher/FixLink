from flask import Blueprint

# The blueprint is actually defined in routes.py to avoid circular imports 
# or maintained here if we want to follow a standard pattern.
# For now, we'll just import it from routes.py.

from .routes import main_bp
