"""
FixLink Flask Application Routes Package
Exposes all modular route blueprints for registration in create_app().
"""
from .main import main_bp
from .admin import admin_bp
from .auth import auth_bp
from .superadmin import superadmin_bp
from .faculty import faculty_bp
from .onboarding import onboarding_bp
from .supervisor import supervisor_bp
from .professional import professional_bp

__all__ = [
    'main_bp',
    'admin_bp',
    'auth_bp',
    'superadmin_bp',
    'faculty_bp',
    'onboarding_bp',
    'supervisor_bp',
    'professional_bp'
]
