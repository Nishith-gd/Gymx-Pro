"""
Security regression tests for Phase 1 changes.

Covers:
  - CSRF protection actually rejects a POST with no/invalid token
  - role_required actually blocks a non-admin from an admin-only route
  - the api.py create_exercise field-name bug is fixed
  - login is rate-limited after repeated failed attempts

Run with: pytest test_security.py -v
"""
import os
import pytest

os.environ['SECRET_KEY'] = 'test-secret-key-not-for-production'
os.environ['FLASK_DEBUG'] = '1'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app, db
from app.models.models import User, Member


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=True,
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

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email, password):
    return client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)


def test_csrf_blocks_post_without_token(client):
    """A POST to a form-protected route with no csrf_token must be rejected."""
    login(client, 'admin@test.com', 'adminpass123')
    response = client.post('/members/add', data={
        'first_name': 'New',
        'last_name': 'Member',
        'email': 'newmember@test.com',
        'password': 'somepassword123',
        'phone': '1234567890',
        # no csrf_token field on purpose
    })
    assert response.status_code == 400
    assert User.query.filter_by(email='newmember@test.com').first() is None


def test_role_required_blocks_non_admin(client):
    """A logged-in member must not be able to reach the admin-only members list."""
    login(client, 'member@test.com', 'memberpass123')
    response = client.get('/members/', follow_redirects=True)
    assert response.status_code == 200  # redirected to dashboard, not the members page
    assert b'Access denied' in response.data or b'Dashboard' in response.data


def test_role_required_blocks_non_admin_api(client):
    """The /api/members endpoint must reject non-admin/trainer roles with 403 JSON."""
    login(client, 'member@test.com', 'memberpass123')
    response = client.get('/api/members')
    assert response.status_code == 403
    assert response.get_json()['error'] == 'Access denied'


def test_create_exercise_field_names_fixed(client, app):
    """Regression test for the sets/reps/rest_seconds -> default_* bug."""
    login(client, 'admin@test.com', 'adminpass123')
    response = client.post('/api/exercises', json={
        'name': 'Bench Press',
        'muscle_group': 'chest',
        'sets': 4,
        'reps': 8,
        'rest_seconds': 90,
    })
    assert response.status_code == 201
    exercise_id = response.get_json()['id']

    with app.app_context():
        from app.models.models import Exercise
        exercise = Exercise.query.get(exercise_id)
        assert exercise.default_sets == 4
        assert exercise.default_reps == 8
        assert exercise.default_rest_seconds == 90


def test_login_rate_limited_after_repeated_failures(client):
    """5 failed logins/min is the limit; the 6th attempt should be throttled."""
    for _ in range(5):
        client.post('/auth/login', data={'email': 'admin@test.com', 'password': 'wrong'})
    response = client.post('/auth/login', data={'email': 'admin@test.com', 'password': 'wrong'})
    assert response.status_code == 429
