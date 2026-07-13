from app import create_app, db
from app.models.models import User, Member

app = create_app()

with app.app_context():
    # Check if admin already exists
    admin = User.query.filter_by(email='admin@gymx.com').first()
    if not admin:
        admin = User(
            first_name='Admin',
            last_name='User',
            email='admin@gymx.com',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully!')
        print('Email: admin@gymx.com')
        print('Password: admin123')
    else:
        print('Admin user already exists!')
