from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models.models import User, Trainer
from app.utils import role_required
import re

trainers_bp = Blueprint('trainers', __name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


@trainers_bp.route('/')
@login_required
@role_required('admin')
def index():
    trainers = Trainer.query.all()
    return render_template('trainers/index.html', trainers=trainers)


@trainers_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add():
    if request.method == 'POST':
        first_name = (request.form.get('first_name') or '').strip()
        last_name = (request.form.get('last_name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        phone = (request.form.get('phone') or '').strip()
        specialization = (request.form.get('specialization') or '').strip()
        experience_years = request.form.get('experience_years', type=int)

        errors = []
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not email or not EMAIL_RE.match(email):
            errors.append('A valid email is required.')
        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if experience_years is not None and experience_years < 0:
            errors.append('Experience years cannot be negative.')

        if not errors and User.query.filter_by(email=email).first():
            errors.append('Email already exists!')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('trainers/add.html', form_data=request.form)

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role='trainer',
            phone=phone
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        trainer = Trainer(
            user_id=user.id,
            specialization=specialization,
            experience_years=experience_years
        )
        db.session.add(trainer)
        db.session.commit()

        flash('Trainer added successfully!', 'success')
        return redirect(url_for('trainers.index'))

    return render_template('trainers/add.html')


@trainers_bp.route('/<int:trainer_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit(trainer_id):
    trainer = Trainer.query.get_or_404(trainer_id)
    user = trainer.user

    if request.method == 'POST':
        first_name = (request.form.get('first_name') or '').strip()
        last_name = (request.form.get('last_name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        phone = (request.form.get('phone') or '').strip()
        specialization = (request.form.get('specialization') or '').strip()
        experience_years = request.form.get('experience_years', type=int)
        bio = (request.form.get('bio') or '').strip()
        new_password = request.form.get('new_password') or ''

        errors = []
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not email or not EMAIL_RE.match(email):
            errors.append('A valid email is required.')

        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            errors.append('Email already in use by another account.')

        if experience_years is not None and experience_years < 0:
            errors.append('Experience years cannot be negative.')

        if new_password:
            if len(new_password) < 8:
                errors.append('New password must be at least 8 characters.')
            elif new_password.strip() != new_password:
                errors.append('Password must not start or end with whitespace.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('trainers/edit.html', trainer=trainer, form_data=request.form)

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone
        if new_password:
            user.set_password(new_password)

        trainer.specialization = specialization
        trainer.experience_years = experience_years
        trainer.bio = bio
        db.session.commit()

        flash('Trainer updated successfully!', 'success')
        return redirect(url_for('trainers.index'))

    return render_template('trainers/edit.html', trainer=trainer)


@trainers_bp.route('/<int:trainer_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete(trainer_id):
    trainer = Trainer.query.get_or_404(trainer_id)
    user = trainer.user
    db.session.delete(trainer)
    db.session.delete(user)
    db.session.commit()
    flash('Trainer deleted successfully.', 'success')
    return redirect(url_for('trainers.index'))
