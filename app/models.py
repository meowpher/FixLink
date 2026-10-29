"""
Backward compatibility re-export shim for app.models.
All models have been modularized under app/models/.
"""
from app.models import *  # noqa: F401, F403
