# Vercel entry point
import traceback
from flask import Flask
from app import create_app

app = create_app()

# Temporary diagnostic handler: shows REAL error in Vercel logs
@app.errorhandler(500)
def handle_500(e):
    print("--- VERCEL 500 ERROR DIAGNOSTIC ---")
    print(traceback.format_exc())
    print("-----------------------------------")
    return f"<pre>{traceback.format_exc()}</pre>", 500

# For Vercel/Gunicorn to easily find the app object
application = app
