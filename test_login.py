from app import create_app
import traceback
import os

os.environ['DATABASE_URL'] = 'sqlite:///test.db'
app = create_app('testing')
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

client = app.test_client()

try:
    print("Sending POST request to /login")
    response = client.post('/login', data={'email': 'taha.piplodwala@mitwpu.edu.in', 'password': 'password123'})
    print(f"Status Code: {response.status_code}")
except Exception as e:
    print("Caught exception:")
    traceback.print_exc()
