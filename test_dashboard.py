"""
Regression tests for Phase 2 — dashboard must reflect real DB data,
not the old hardcoded stats/activity table.

Run with: pytest test_dashboard.py -v
"""
import os
import pytest
from datetime import datetime, date, timedelta

os.environ.setdefault('SECRET_KEY', 'test-secret-key-not-for-production')
os.environ.setdefault('FLASK_DEBUG', '1')

from app import create_app, db
from app.models.models import (
    User, Member, MembershipPlan, Membership, Payment, Attendance, WorkoutLog
)


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
    )

    with app.app_context():
        db.create_all()

        admin = User(email='admin@test.com', first_name='Ada', last_name='Min', role='admin')
        admin.set_password('adminpass123')
        db.session.add(admin)

        member_user = User(email='member@test.com', first_name='Mo', last_name='Ember', role='member')
        member_user.set_password('memberpass123')
        db.session.add(member_user)
        db.session.commit()

        member = Member(user_id=member_user.id)
        db.session.add(member)
        db.session.commit()

        plan = MembershipPlan(name='Gold', duration_months=1, price=50.0, is_active=True)
        db.session.add(plan)
        db.session.commit()

        membership = Membership(
            member_id=member.id,
            plan_id=plan.id,
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() + timedelta(days=3),  # expiring within 7 days
            status='active',
        )
        db.session.add(membership)
        db.session.commit()

        payment = Payment(
            membership_id=membership.id,
            amount=50.0,
            status='completed',
            payment_date=datetime.utcnow(),
        )
        db.session.add(payment)

        attendance = Attendance(member_id=member.id, check_in=datetime.utcnow())
        db.session.add(attendance)

        workout_log = WorkoutLog(member_id=member.id, date=date.today(), created_at=datetime.utcnow())
        db.session.add(workout_log)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email, password):
    return client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)


def test_admin_dashboard_shows_real_stats(client):
    login(client, 'admin@test.com', 'adminpass123')
    response = client.get('/dashboard/')
    assert response.status_code == 200
    body = response.data.decode()

    # Old hardcoded values must be gone
    assert 'John Doe' not in body
    assert '128' not in body
    assert '$12,500' not in body

    # Real seeded data must appear
    assert '1' in body  # active_members count == 1
    assert '$50.00' in body  # monthly revenue from the completed payment
    assert 'Mo' in body  # member name in activity feed


def test_member_dashboard_shows_personal_stats(client):
    login(client, 'member@test.com', 'memberpass123')
    response = client.get('/dashboard/')
    assert response.status_code == 200
    body = response.data.decode()

    assert 'Checked In' in body
    assert 'days left' in body


def test_dashboard_empty_state_when_no_activity(client, app):
    with app.app_context():
        Attendance.query.delete()
        WorkoutLog.query.delete()
        Membership.query.delete()
        db.session.commit()

    login(client, 'admin@test.com', 'adminpass123')
    response = client.get('/dashboard/')
    assert response.status_code == 200
    assert b'No recent activity yet' in response.data
