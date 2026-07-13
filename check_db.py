from app import create_app, db
from app.models.models import User, Member

app = create_app()

with app.app_context():
    users = User.query.all()
    print("=== All Users ===")
    for u in users:
        print(f"ID: {u.id}, Email: {u.email}, Role: {u.role}, Name: {u.first_name} {u.last_name}")
        # Test password
        if u.email == 'admin@gymx.com':
            print(f"Password check for 'admin123': {u.check_password('admin123')}")
    
    members = Member.query.all()
    print("\n=== All Members ===")
    for m in members:
        print(f"ID: {m.id}, User ID: {m.user_id}")
