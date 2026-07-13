from functools import wraps
from flask import redirect, url_for, flash, jsonify, request
from flask_login import current_user


def role_required(*roles):
    """Restrict a route to the given user roles.

    Usage:
        @role_required('admin')
        @role_required('admin', 'trainer')

    For JSON/API routes (path starts with /api), returns a 403 JSON body
    instead of redirecting, since there's no page to flash a message onto.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                if request.path.startswith('/api'):
                    return jsonify({'error': 'Access denied'}), 403
                flash('Access denied!', 'danger')
                return redirect(url_for('dashboard.index'))
            return fn(*args, **kwargs)
        return wrapped
    return decorator
