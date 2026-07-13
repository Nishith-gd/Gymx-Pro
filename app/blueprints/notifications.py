from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.models import Notification
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/')
@login_required
def index():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('notifications/index.html', notifications=notifications)


@notifications_bp.route('/<int:id>/read', methods=['POST'])
@login_required
def mark_read(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id != current_user.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'ok': False, 'error': 'Access denied.'}), 403
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard.index'))

    notification.is_read = True
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': True})

    return redirect(url_for('notifications.index'))


@notifications_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id != current_user.id:
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard.index'))
    db.session.delete(notification)
    db.session.commit()
    flash('Notification dismissed.', 'success')
    return redirect(url_for('notifications.index'))
