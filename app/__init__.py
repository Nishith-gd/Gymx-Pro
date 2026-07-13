from flask import Flask, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from dotenv import load_dotenv
import os
import logging
import secrets as secrets_module
from logging.handlers import RotatingFileHandler

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
talisman = Talisman()


def _configure_logging(app):
    """Set up console + rotating-file logging for the application."""
    fmt = '%(asctime)s %(levelname)s %(name)s [%(filename)s:%(lineno)d]: %(message)s'
    date_fmt = '%Y-%m-%d %H:%M:%S'
    level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO

    # --- Console handler (always on) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(fmt, date_fmt))

    # --- Rotating file handler (production only) ---
    handlers = [console_handler]
    if not app.config.get('DEBUG') and not app.config.get('TESTING'):
        log_dir = os.path.join(app.root_path, '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'gymx_pro.log'),
            maxBytes=10 * 1024 * 1024,  # 10 MB per file
            backupCount=5,
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(fmt, date_fmt))
        handlers.append(file_handler)

    # Apply to root logger so all libraries (SQLAlchemy, Werkzeug, etc.) go through it.
    logging.basicConfig(level=level, format=fmt, datefmt=date_fmt, handlers=handlers)

    # Also wire Flask's own logger to the same handlers.
    for h in handlers:
        app.logger.addHandler(h)
    app.logger.setLevel(level)
    app.logger.propagate = False


def create_app():
    app = Flask(__name__)
    load_dotenv()

    debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'
    testing = os.getenv('TESTING', '0') == '1'
    secret_key = os.getenv('SECRET_KEY')

    if not secret_key:
        if debug_mode or testing:
            secret_key = secrets_module.token_hex(32)
            logging.warning(
                'No SECRET_KEY set — using a temporary random key for this run. '
                'Set SECRET_KEY in .env for persistent sessions.'
            )
        else:
            raise RuntimeError(
                'SECRET_KEY environment variable is required in production. '
                'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
            )

    app.config['SECRET_KEY'] = secret_key
    app.config['DEBUG'] = debug_mode
    app.config['TESTING'] = testing
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 'sqlite:///gymx_pro.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    _configure_logging(app)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)

    # -----------------------------------------------------------------------
    # Security headers via Flask-Talisman
    # -----------------------------------------------------------------------
    # FORCE_HTTPS defaults off so local dev / HTTP deployments still work.
    # Set FORCE_HTTPS=1 in production when the app sits behind an HTTPS
    # terminating proxy (Heroku, Railway, Render, nginx with SSL, etc.)
    force_https = os.getenv('FORCE_HTTPS', '0') == '1'

    csp = {
        'default-src': ["'self'"],
        # Bootstrap 5 CDN + Bootstrap Icons CDN
        'style-src': [
            "'self'",
            "'unsafe-inline'",          # Bootstrap uses inline style for offcanvas/collapse
            'cdn.jsdelivr.net',
            'fonts.googleapis.com',
        ],
        'script-src': [
            "'self'",
            "'unsafe-inline'",          # our onclick= attributes; tighten with nonces later
            'cdn.jsdelivr.net',
        ],
        'font-src': [
            "'self'",
            'cdn.jsdelivr.net',
            'fonts.gstatic.com',
        ],
        'img-src': ["'self'", 'data:'],
        'connect-src': ["'self'"],
    }

    talisman.init_app(
        app,
        force_https=force_https,
        session_cookie_secure=force_https,
        strict_transport_security=force_https,       # only send HSTS when HTTPS is on
        strict_transport_security_max_age=31536000,
        strict_transport_security_include_subdomains=True,
        content_security_policy=csp,
        referrer_policy='strict-origin-when-cross-origin',
        feature_policy={
            'geolocation': "'none'",
            'microphone': "'none'",
            'camera': "'none'",
        },
        x_content_type_options=True,
        x_xss_protection=True,
    )

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.members import members_bp
    from app.blueprints.trainers import trainers_bp
    from app.blueprints.memberships import memberships_bp
    from app.blueprints.exercises import exercises_bp
    from app.blueprints.workouts import workouts_bp
    from app.blueprints.attendance import attendance_bp
    from app.blueprints.progress import progress_bp
    from app.blueprints.diet import diet_bp
    from app.blueprints.notifications import notifications_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.api import api_bp
    from app.blueprints.profile import profile_bp
    from app.models.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp,          url_prefix='/auth')
    app.register_blueprint(dashboard_bp,     url_prefix='/dashboard')
    app.register_blueprint(members_bp,       url_prefix='/members')
    app.register_blueprint(trainers_bp,      url_prefix='/trainers')
    app.register_blueprint(memberships_bp,   url_prefix='/memberships')
    app.register_blueprint(exercises_bp,     url_prefix='/exercises')
    app.register_blueprint(workouts_bp,      url_prefix='/workouts')
    app.register_blueprint(attendance_bp,    url_prefix='/attendance')
    app.register_blueprint(progress_bp,      url_prefix='/progress')
    app.register_blueprint(diet_bp,          url_prefix='/diet')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(reports_bp,       url_prefix='/reports')
    app.register_blueprint(api_bp)
    app.register_blueprint(profile_bp,       url_prefix='/profile')

    @app.route('/')
    def home():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    # -----------------------------------------------------------------------
    # Error handlers
    # -----------------------------------------------------------------------
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning('400 Bad Request: %s', error)
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(error):
        app.logger.warning('403 Forbidden: %s', error)
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(429)
    def rate_limited(error):
        app.logger.warning('429 Rate Limited: %s', error)
        return render_template('errors/429.html'), 429

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception('500 Internal Server Error')
        db.session.rollback()       # don't leave a broken transaction open
        return render_template('errors/500.html'), 500

    return app
