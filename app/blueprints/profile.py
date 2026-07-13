from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models.models import User, Member, Trainer
import re

profile_bp = Blueprint('profile', __name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


@profile_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    member = Member.query.filter_by(user_id=current_user.id).first()
    trainer = Trainer.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        first_name = (request.form.get('first_name') or '').strip()
        last_name  = (request.form.get('last_name')  or '').strip()
        email      = (request.form.get('email')       or '').strip().lower()
        phone      = (request.form.get('phone')       or '').strip()
        new_password    = request.form.get('new_password')    or ''
        confirm_password = request.form.get('confirm_password') or ''

        errors = []
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not email or not EMAIL_RE.match(email):
            errors.append('A valid email address is required.')

        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != current_user.id:
            errors.append('That email is already in use by another account.')

        if new_password:
            if len(new_password) < 8:
                errors.append('New password must be at least 8 characters.')
            elif new_password != confirm_password:
                errors.append('Passwords do not match.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('profile/index.html',
                                   member=member, trainer=trainer,
                                   form_data=request.form)

        current_user.first_name = first_name
        current_user.last_name  = last_name
        current_user.email      = email
        current_user.phone      = phone
        if new_password:
            current_user.set_password(new_password)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.index'))

    return render_template('profile/index.html', member=member, trainer=trainer)
