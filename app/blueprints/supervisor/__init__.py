"""
Supervisor Blueprint - Dedicated Quality Assurance Workspace
"""
from flask import Blueprint

supervisor_bp = Blueprint('supervisor', __name__)

from . import routes
