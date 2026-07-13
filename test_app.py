"""
GymX Pro — Comprehensive pytest test suite (Phase 5).

Covers:
  - Auth flow: register, login, logout, bad credentials
  - Permission denial for every role on every blueprint
  - Full CRUD cycle for Members and Workout Plans
  - CSRF rejection (POST without token → 400)
  - Dashboard data
  - Profile page

Run:  pytest test_app.py -v
Run a single class:  pytest test_app.py::TestAuth -v
"""

import os

# Set env vars BEFORE importing the app so create_app() sees them.
os.environ.setdefault('SECRET_KEY', 'test-secret-not-for-production')
os.environ.setdefault('FLASK_DEBUG', '1')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

import pytest
from app import create_app, db
from app.models.models import User, Member, Trainer, WorkoutPlan


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def app():
    """Module-scoped app with an in-memory SQLite DB seeded once."""
    _app = create_app()
    _app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,   # disabled so functional tests don't need tokens
        RATELIMIT_ENABLED=False,  # disable rate limiting so login tests aren't throttled
    )
    with _app.app_context():
        db.create_all()
        _seed()
        yield _app
        db.session.remove()
        db.drop_all()


def _seed():
    """Create one admin, one trainer, and one member user."""
    admin = User(email='admin@test.com', first_name='Ada', last_name='Min', role='admin')
    admin.set_password('AdminPass123')

    trainer_u = User(email='trainer@test.com', first_name='Trey', last_name='Ner', role='trainer')
    trainer_u.set_password('TrainerPass123')

    member_u = User(email='member@test.com', first_name='Mo', last_name='Ember', role='member')
    member_u.set_password('MemberPass123')

    db.session.add_all([admin, trainer_u, member_u])
    db.session.commit()

    trainer = Trainer(user_id=trainer_u.id, specialization='Strength')
    member = Member(user_id=member_u.id)
    db.session.add_all([trainer, member])
    db.session.commit()


@pytest.fixture
def client(app):
    """Fresh test client per test (no session state)."""
    return app.test_client()


def _login(client, email, password):
    return client.post(
        '/auth/login',
        data={'email': email, 'password': password},
        follow_redirects=True,
    )


@pytest.fixture
def admin_client(client):
    _login(client, 'admin@test.com', 'AdminPass123')
    yield client
    client.get('/auth/logout')


@pytest.fixture
def trainer_client(client):
    _login(client, 'trainer@test.com', 'TrainerPass123')
    yield client
    client.get('/auth/logout')


@pytest.fixture
def member_client(client):
    _login(client, 'member@test.com', 'MemberPass123')
    yield client
    client.get('/auth/logout')


# ---------------------------------------------------------------------------
# 1. Auth flow
# ---------------------------------------------------------------------------

class TestAuth:
    def test_login_page_renders(self, client):
        resp = client.get('/auth/login')
        assert resp.status_code == 200
        assert b'Sign In' in resp.data or b'Login' in resp.data

    def test_register_page_renders(self, client):
        resp = client.get('/auth/register')
        assert resp.status_code == 200

    def test_successful_registration(self, client, app):
        resp = client.post('/auth/register', data={
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@test.com',
            'password': 'Newpass123',
            'confirm_password': 'Newpass123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            assert User.query.filter_by(email='newuser@test.com').first() is not None

    def test_registration_rejects_duplicate_email(self, client):
        # First registration
        client.post('/auth/register', data={
            'first_name': 'Dup', 'last_name': 'User',
            'email': 'dup@test.com', 'password': 'Duppass123',
            'confirm_password': 'Duppass123',
        })
        # Duplicate
        resp = client.post('/auth/register', data={
            'first_name': 'Dup', 'last_name': 'User',
            'email': 'dup@test.com', 'password': 'Duppass123',
            'confirm_password': 'Duppass123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'already' in resp.data.lower() or b'registered' in resp.data.lower()

    def test_registration_rejects_weak_password(self, client, app):
        resp = client.post('/auth/register', data={
            'first_name': 'Weak', 'last_name': 'Pass',
            'email': 'weakpass@test.com',
            'password': '123',        # too short
            'confirm_password': '123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            assert User.query.filter_by(email='weakpass@test.com').first() is None

    def test_registration_rejects_password_mismatch(self, client, app):
        resp = client.post('/auth/register', data={
            'first_name': 'Miss', 'last_name': 'Match',
            'email': 'mismatch@test.com',
            'password': 'Password123',
            'confirm_password': 'Different123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            assert User.query.filter_by(email='mismatch@test.com').first() is None

    def test_successful_login_reaches_dashboard(self, client):
        resp = _login(client, 'admin@test.com', 'AdminPass123')
        assert resp.status_code == 200
        assert b'Dashboard' in resp.data
        client.get('/auth/logout')

    def test_bad_password_rejected(self, client):
        resp = _login(client, 'admin@test.com', 'WrongPassword')
        assert b'Login failed' in resp.data or b'check' in resp.data.lower()

    def test_unknown_email_rejected(self, client):
        resp = _login(client, 'nobody@nowhere.com', 'AnyPass123')
        assert b'Login failed' in resp.data or b'check' in resp.data.lower()

    def test_logout_redirects_to_login(self, client):
        _login(client, 'admin@test.com', 'AdminPass123')
        resp = client.get('/auth/logout', follow_redirects=True)
        assert resp.status_code == 200
        # After logout the session is cleared; dashboard must redirect to login
        resp2 = client.get('/dashboard/', follow_redirects=True)
        assert b'Sign In' in resp2.data or b'Login' in resp2.data or b'login' in resp2.data.lower()

    def test_unauthenticated_dashboard_redirects_to_login(self, client):
        resp = client.get('/dashboard/', follow_redirects=True)
        assert b'Sign In' in resp.data or b'Login' in resp.data or b'login' in resp.data.lower()


# ---------------------------------------------------------------------------
# 2. Permission / role-denial (one protected route per blueprint)
# ---------------------------------------------------------------------------

class TestPermissions:
    # --- Members (admin only) ---
    def test_members_list_blocked_for_member(self, member_client):
        resp = member_client.get('/members/', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Access denied' in resp.data or b'Dashboard' in resp.data

    def test_members_list_blocked_for_trainer(self, trainer_client):
        resp = trainer_client.get('/members/', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Access denied' in resp.data or b'Dashboard' in resp.data

    def test_members_list_ok_for_admin(self, admin_client):
        resp = admin_client.get('/members/')
        assert resp.status_code == 200
        assert b'Members' in resp.data

    # --- Trainers (admin only) ---
    def test_trainers_add_blocked_for_member(self, member_client):
        resp = member_client.get('/trainers/add', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Access denied' in resp.data or b'Dashboard' in resp.data

    def test_trainers_add_blocked_for_trainer(self, trainer_client):
        resp = trainer_client.get('/trainers/add', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Access denied' in resp.data or b'Dashboard' in resp.data

    # --- Exercises (add/edit blocked for member) ---
    def test_exercise_list_ok_for_member(self, member_client):
        resp = member_client.get('/exercises/')
        assert resp.status_code == 200

    def test_exercise_add_blocked_for_member(self, member_client):
        resp = member_client.get('/exercises/add', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Access denied' in resp.data or b'Dashboard' in resp.data

    def test_exercise_add_ok_for_trainer(self, trainer_client):
        resp = trainer_client.get('/exercises/add')
        assert resp.status_code == 200

    # --- Workouts (add blocked for member) ---
    def test_workout_list_ok_for_member(self, member_client):
        resp = member_client.get('/workouts/')
        assert resp.status_code == 200

    def test_workout_add_blocked_for_member(self, member_client):
        resp = member_client.get('/workouts/add', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Access denied' in resp.data or b'Dashboard' in resp.data

    # --- Memberships (plans list admin only) ---
    def test_membership_plans_blocked_for_member(self, member_client):
        resp = member_client.get('/memberships/plans', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Access denied' in resp.data or b'Dashboard' in resp.data

    # --- Reports (admin/trainer only) ---
    def test_reports_blocked_for_member(self, member_client):
        resp = member_client.get('/reports/', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Access denied' in resp.data or b'Dashboard' in resp.data

    def test_reports_ok_for_trainer(self, trainer_client):
        resp = trainer_client.get('/reports/')
        assert resp.status_code == 200

    # --- Attendance (open to all logged-in) ---
    def test_attendance_ok_for_member(self, member_client):
        resp = member_client.get('/attendance/')
        assert resp.status_code == 200

    # --- Progress (open to all logged-in) ---
    def test_progress_ok_for_member(self, member_client):
        resp = member_client.get('/progress/')
        assert resp.status_code == 200

    # --- Notifications (own items) ---
    def test_notifications_ok_for_member(self, member_client):
        resp = member_client.get('/notifications/')
        assert resp.status_code == 200

    # --- API (/api/members blocked for member) ---
    def test_api_members_blocked_for_member(self, member_client):
        resp = member_client.get('/api/members')
        assert resp.status_code == 403
        data = resp.get_json()
        assert data is not None
        assert 'error' in data


# ---------------------------------------------------------------------------
# 3. CSRF rejection (separate app instance with CSRF enabled)
# ---------------------------------------------------------------------------

class TestCSRF:
    @pytest.fixture(scope='class')
    def csrf_app(self):
        _app = create_app()
        _app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            WTF_CSRF_ENABLED=True,
            RATELIMIT_ENABLED=False,
        )
        with _app.app_context():
            db.create_all()
            u = User(email='csrf@test.com', first_name='Csrf', last_name='Admin', role='admin')
            u.set_password('CsrfAdmin123')
            db.session.add(u)
            db.session.commit()
            yield _app
            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def csrf_client(self, csrf_app):
        c = csrf_app.test_client()
        c.post('/auth/login', data={'email': 'csrf@test.com', 'password': 'CsrfAdmin123'},
               follow_redirects=True)
        return c

    def test_post_without_csrf_token_returns_400(self, csrf_client):
        resp = csrf_client.post('/members/add', data={
            'first_name': 'NoCSRF',
            'last_name': 'User',
            'email': 'nocsrf@test.com',
            'password': 'Password123',
            # csrf_token intentionally omitted
        })
        assert resp.status_code == 400

    def test_post_with_bad_csrf_token_returns_400(self, csrf_client):
        resp = csrf_client.post('/members/add', data={
            'first_name': 'BadCSRF',
            'last_name': 'User',
            'email': 'badcsrf@test.com',
            'password': 'Password123',
            'csrf_token': 'this-is-a-fake-token',
        })
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 4. Full CRUD cycle — Members
# ---------------------------------------------------------------------------

class TestMembersCRUD:
    """Create → Edit → Delete a member in a single test to avoid inter-test state."""

    def test_full_crud_cycle(self, admin_client, app):
        # -- Create --
        resp = admin_client.post('/members/add', data={
            'first_name': 'Crud',
            'last_name': 'Member',
            'email': 'crudmember@test.com',
            'password': 'CrudPass123',
            'phone': '5550001111',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Member added' in resp.data or b'success' in resp.data.lower()

        with app.app_context():
            u = User.query.filter_by(email='crudmember@test.com').first()
            assert u is not None
            m = u.member
            assert m is not None
            member_id = m.id

        # -- Edit --
        resp = admin_client.post(f'/members/{member_id}/edit', data={
            'first_name': 'CrudEdited',
            'last_name': 'Member',
            'email': 'crudmember@test.com',
            'phone': '5550002222',
        }, follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            u = User.query.filter_by(email='crudmember@test.com').first()
            assert u is not None
            assert u.first_name == 'CrudEdited'
            assert u.phone == '5550002222'

        # -- Delete --
        resp = admin_client.post(f'/members/{member_id}/delete', follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            assert User.query.filter_by(email='crudmember@test.com').first() is None

    def test_create_rejects_invalid_email(self, admin_client, app):
        resp = admin_client.post('/members/add', data={
            'first_name': 'Bad', 'last_name': 'Email',
            'email': 'not-an-email',
            'password': 'ValidPass123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            assert User.query.filter_by(email='not-an-email').first() is None

    def test_create_rejects_short_password(self, admin_client, app):
        resp = admin_client.post('/members/add', data={
            'first_name': 'Short', 'last_name': 'Pass',
            'email': 'shortpass@test.com',
            'password': '123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            assert User.query.filter_by(email='shortpass@test.com').first() is None

    def test_create_rejects_duplicate_email(self, admin_client, app):
        # First member is seeded as 'member@test.com'
        resp = admin_client.post('/members/add', data={
            'first_name': 'Dup', 'last_name': 'Email',
            'email': 'member@test.com',   # already exists
            'password': 'ValidPass123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'already' in resp.data.lower() or b'exists' in resp.data.lower()

    def test_member_blocked_cannot_add_members(self, member_client, app):
        resp = member_client.post('/members/add', data={
            'first_name': 'Forbidden', 'last_name': 'Add',
            'email': 'forbidden@test.com', 'password': 'ForbidPass123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            assert User.query.filter_by(email='forbidden@test.com').first() is None


# ---------------------------------------------------------------------------
# 5. Full CRUD cycle — Workout Plans
# ---------------------------------------------------------------------------

class TestWorkoutPlansCRUD:
    def test_full_crud_cycle(self, admin_client, app):
        # -- Create --
        resp = admin_client.post('/workouts/add', data={
            'name': 'Test Strength Plan',
            'description': 'A pytest-created plan',
            'category': 'strength',
        }, follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            plan = WorkoutPlan.query.filter_by(name='Test Strength Plan').first()
            assert plan is not None
            plan_id = plan.id

        # -- View detail --
        resp = admin_client.get(f'/workouts/{plan_id}')
        assert resp.status_code == 200
        assert b'Test Strength Plan' in resp.data

        # -- Edit --
        resp = admin_client.post(f'/workouts/{plan_id}/edit', data={
            'name': 'Edited Strength Plan',
            'description': 'Updated by pytest',
            'category': 'hypertrophy',
        }, follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            updated = WorkoutPlan.query.get(plan_id)
            assert updated is not None
            assert updated.name == 'Edited Strength Plan'
            assert updated.category == 'hypertrophy'

        # -- Delete --
        resp = admin_client.post(f'/workouts/{plan_id}/delete', follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            assert WorkoutPlan.query.get(plan_id) is None

    def test_member_cannot_create_workout_plan(self, member_client, app):
        resp = member_client.post('/workouts/add', data={
            'name': 'ForbiddenPlan', 'description': '', 'category': 'cardio',
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            assert WorkoutPlan.query.filter_by(name='ForbiddenPlan').first() is None


# ---------------------------------------------------------------------------
# 6. Dashboard
# ---------------------------------------------------------------------------

class TestDashboard:
    def test_dashboard_ok_for_admin(self, admin_client):
        resp = admin_client.get('/dashboard/')
        assert resp.status_code == 200
        assert b'Dashboard' in resp.data

    def test_dashboard_ok_for_trainer(self, trainer_client):
        resp = trainer_client.get('/dashboard/')
        assert resp.status_code == 200

    def test_dashboard_ok_for_member(self, member_client):
        resp = member_client.get('/dashboard/')
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 7. Profile page
# ---------------------------------------------------------------------------

class TestProfile:
    def test_profile_renders_for_admin(self, admin_client):
        resp = admin_client.get('/profile/')
        assert resp.status_code == 200
        assert b'Profile' in resp.data

    def test_profile_renders_for_member(self, member_client):
        resp = member_client.get('/profile/')
        assert resp.status_code == 200

    def test_profile_update_persists(self, admin_client, app):
        resp = admin_client.post('/profile/', data={
            'first_name': 'UpdatedAda',
            'last_name': 'Min',
            'email': 'admin@test.com',
            'phone': '5551234567',
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            u = User.query.filter_by(email='admin@test.com').first()
            assert u.first_name == 'UpdatedAda'
            assert u.phone == '5551234567'
