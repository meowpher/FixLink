# Vercel entry point
import traceback
from flask import Flask
from app import create_app

app = create_app()

# For Vercel/Gunicorn to easily find the app object
application = app
