from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(email="taha.piplodwala@mitwpu.edu.in").first()
    if user:
        print(f"User found: {user.email}")
        print(f"Role: {user.role}")
        print(f"Is Superadmin? {user.is_superadmin}")
    else:
        print("User not found in the database.")
