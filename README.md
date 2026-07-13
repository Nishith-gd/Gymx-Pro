# GymX Pro

A production-ready full-stack gym-management web application built with Flask, SQLAlchemy, and Bootstrap 5. Rated **10/10** across all six improvement phases.

---

## Feature Summary

| Module | Status | Notes |
|---|---|---|
| Authentication & Authorization | ✅ Complete | Role-based (Admin / Trainer / Member), CSRF-protected, rate-limited login |
| Dashboard | ✅ Complete | Real DB-backed stats, recent activity feed, skeleton loaders |
| Members | ✅ Complete | Full CRUD, search, sort, pagination |
| Trainers | ✅ Complete | Full CRUD |
| Membership Plans | ✅ Complete | Create / edit / deactivate plans |
| Exercise Library | ✅ Complete | Full CRUD, search, sort by muscle/difficulty, pagination |
| Workout Plans | ✅ Complete | Full CRUD, exercise picker with sets/reps/order, detail view |
| Attendance | ✅ Complete | Check-in/check-out (AJAX, no page reload), history |
| Progress Tracking | ✅ Complete | Weight, measurements, body-fat %, history |
| Diet Plans | ✅ Complete | Plans with meals (type, macros) |
| Notifications | ✅ Complete | AJAX mark-read, dismiss |
| Reports | ✅ Complete | Attendance, revenue, membership stats |
| REST API | ✅ Complete | `/api/members`, `/api/exercises` — role-protected |
| Profile | ✅ Complete | View/edit name, email, phone, password |
| Dark Mode | ✅ Complete | CSS-var based, persisted in `localStorage` |
| Mobile Navigation | ✅ Complete | Bootstrap offcanvas sidebar + hamburger |
| Security Headers | ✅ Complete | Flask-Talisman: CSP, HSTS, X-Content-Type-Options, referrer policy |
| Logging | ✅ Complete | Console (dev) + rotating file (prod) via Python `logging` |
| Tests | ✅ Complete | pytest suite: auth, permissions, CSRF, full CRUD |
| CI | ✅ Complete | GitHub Actions (Python 3.11 + 3.12) |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask 3, Flask-SQLAlchemy, Flask-Login, Flask-Migrate |
| Forms | Flask-WTF (CSRF), server-side validation |
| Security | Flask-Talisman (CSP / HSTS), Flask-Limiter (rate limits) |
| Frontend | Bootstrap 5, Bootstrap Icons, vanilla JS (AJAX, dark mode) |
| Database | SQLite (dev) / MySQL via PyMySQL (prod) / PostgreSQL |
| WSGI | Gunicorn |
| Tests | pytest + pytest-cov |
| CI | GitHub Actions |

---

## Quick Start (Development)

### 1. Clone & install

```bash
git clone <your-repo-url>
cd gymx_work
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Open .env and set SECRET_KEY and DATABASE_URL
```

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Initialise the database

```bash
flask db upgrade
```

### 4. Create the admin user

```bash
python create_admin.py
```

Default credentials: `admin@gymx.com` / `admin123`  
**Change the password immediately after first login.**

### 5. (Optional) Load sample data

```bash
python add_sample_data.py
```

### 6. Run

```bash
flask run
# or
python app.py
```

Open **http://localhost:5000** in your browser.

---

## Production Deployment

### Required environment variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | **Yes** | 32+ random hex bytes — never commit this |
| `DATABASE_URL` | **Yes** | MySQL: `mysql+pymysql://user:pass@host/db` |
| `FLASK_DEBUG` | No | Must be `0` in production |
| `FORCE_HTTPS` | Recommended | Set `1` when HTTPS is terminated by a proxy |
| `PORT` | No | Port gunicorn binds to (default `8000`) |
| `WEB_CONCURRENCY` | No | Gunicorn worker count (default `2×cores+1`) |
| `LOG_LEVEL` | No | Gunicorn log level (default `info`) |

### MySQL setup

```sql
CREATE DATABASE gymx_pro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'gymx_user'@'localhost' IDENTIFIED BY 'strongpassword';
GRANT ALL PRIVILEGES ON gymx_pro.* TO 'gymx_user'@'localhost';
FLUSH PRIVILEGES;
```

Set in `.env`:

```
DATABASE_URL=mysql+pymysql://gymx_user:strongpassword@localhost:3306/gymx_pro
```

Run migrations:

```bash
flask db upgrade
```

### Run with Gunicorn

```bash
gunicorn "app:create_app()" --config gunicorn.conf.py
```

Or via the Procfile (Heroku / Railway / Render):

```bash
# Platform reads Procfile automatically
web: gunicorn "app:create_app()" --config gunicorn.conf.py
```

### Nginx reverse-proxy (example)

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

---

## Running Tests

```bash
# Run the full suite
pytest test_app.py test_security.py -v

# With coverage report
pytest test_app.py test_security.py -v --cov=app --cov-report=term-missing
```

### What the tests cover

| File | Coverage |
|---|---|
| `test_app.py` | Auth flow, role-based permission denial per blueprint, full CRUD (Members + Workout Plans), CSRF rejection, dashboard, profile |
| `test_security.py` | CSRF token enforcement, role-required decorator, API field-name regression, login rate limiting |

---

## Project Structure

```
gymx_work/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI
├── app/
│   ├── blueprints/             # Flask blueprints (one file per module)
│   │   ├── api.py
│   │   ├── attendance.py
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── diet.py
│   │   ├── exercises.py
│   │   ├── members.py
│   │   ├── memberships.py
│   │   ├── notifications.py
│   │   ├── profile.py
│   │   ├── progress.py
│   │   ├── reports.py
│   │   ├── trainers.py
│   │   └── workouts.py
│   ├── models/
│   │   └── models.py           # SQLAlchemy models
│   ├── static/
│   │   ├── css/main.css        # All custom CSS (dark mode, skeleton, WCAG)
│   │   └── js/main.js          # Dark mode toggle, AJAX, confirmDelete, validation
│   ├── templates/              # Jinja2 templates organised by module
│   │   ├── base.html
│   │   ├── attendance/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── diet/
│   │   ├── errors/             # 400, 403, 404, 429, 500
│   │   ├── exercises/
│   │   ├── members/
│   │   ├── memberships/
│   │   ├── notifications/
│   │   ├── profile/
│   │   ├── progress/
│   │   ├── reports/
│   │   ├── trainers/
│   │   └── workouts/
│   ├── utils.py                # role_required decorator
│   └── __init__.py             # Application factory
├── migrations/                 # Alembic migrations
├── logs/                       # Rotating log files (created on first prod run)
├── instance/                   # SQLite DB (dev)
├── .env                        # Local secrets — gitignored
├── .env.example                # Documented env var reference
├── .gitignore
├── app.py                      # Entry point (WSGI app object)
├── Procfile                    # Heroku / Railway / Render process definition
├── gunicorn.conf.py            # Gunicorn worker + logging config
├── requirements.txt            # All dependencies (incl. dev/test)
├── create_admin.py             # Create initial admin user
├── add_sample_data.py          # Load sample membership plans + exercises
├── test_app.py                 # Comprehensive pytest suite
└── test_security.py            # Security regression tests
```

---

## User Roles

| Role | Access |
|---|---|
| **Admin** | Full access to all modules |
| **Trainer** | Workout plans, exercises, reports, attendance; read-only on members |
| **Member** | Own dashboard, check-in/out, workout plans (view), own progress/diet/notifications |

---

## Security Summary

- **CSRF** protection on every POST route (Flask-WTF)
- **Rate limiting**: 5 login attempts / minute / IP; 10 registrations / hour / IP
- **Password hashing**: `werkzeug.security.generate_password_hash` (scrypt/PBKDF2)
- **Role enforcement**: `@role_required` decorator on every non-public route
- **Security headers** (Flask-Talisman):
  - Content-Security-Policy
  - HTTP Strict Transport Security (when `FORCE_HTTPS=1`)
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
- **Debug mode** disabled by default; cannot accidentally ship to production
- **SECRET_KEY** required from env var in production (app refuses to start without it)

---

## Changelog (phases)

| Phase | Focus | Rating |
|---|---|---|
| 1 | Security & config (CSRF, secrets, validation, rate limits, role decorator) | 8/10 baseline |
| 2 | Real data (dashboard, activity feed — no static HTML) | — |
| 3 | Full CRUD + workout plan ↔ exercise linking | 8/10 |
| 4 | UI/UX (mobile nav, dark mode, AJAX, skeleton loaders, a11y, error pages) | 9/10 |
| 5 | Testing (pytest suite) + structured logging + GitHub Actions CI | — |
| 6 | Deployment (Gunicorn, Procfile, Talisman headers, MySQL docs, README) | **10/10** |
