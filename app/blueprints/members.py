from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models.models import User, Member, Membership, Attendance, Progress, WorkoutLog
from app.utils import role_required
import re

members_bp = Blueprint('members', __name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


@members_bp.route('/')
@login_required
@role_required('admin')
def index():
    page = request.args.get('page', 1, type=int)
    q    = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'name')

    query = Member.query.join(User)
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                User.email.ilike(like),
            )
        )
    if sort == 'email':
        query = query.order_by(User.email)
    else:
        query = query.order_by(User.first_name, User.last_name)

    pagination = query.paginate(page=page, per_page=20, error_out=False)
    return render_template('members/index.html',
                           members=pagination.items,
                           pagination=pagination,
                           q=q, sort=sort)


@members_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add():
    if request.method == 'POST':
        first_name = (request.form.get('first_name') or '').strip()
        last_name = (request.form.get('last_name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        phone = (request.form.get('phone') or '').strip()

        errors = []
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not email or not EMAIL_RE.match(email):
            errors.append('A valid email is required.')
        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        elif password.strip() != password:
            errors.append('Password must not start or end with whitespace.')

        if not errors and User.query.filter_by(email=email).first():
            errors.append('Email already exists!')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('members/add.html', form_data=request.form)

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role='member',
            phone=phone
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        member = Member(user_id=user.id)
        db.session.add(member)
        db.session.commit()

        flash('Member added successfully!', 'success')
        return redirect(url_for('members.index'))

    return render_template('members/add.html')


@members_bp.route('/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit(member_id):
    member = Member.query.get_or_404(member_id)
    user = member.user

    if request.method == 'POST':
        first_name = (request.form.get('first_name') or '').strip()
        last_name = (request.form.get('last_name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        phone = (request.form.get('phone') or '').strip()
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

        if new_password:
            if len(new_password) < 8:
                errors.append('New password must be at least 8 characters.')
            elif new_password.strip() != new_password:
                errors.append('Password must not start or end with whitespace.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('members/edit.html', member=member, form_data=request.form)

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone
        if new_password:
            user.set_password(new_password)
        db.session.commit()

        flash('Member updated successfully!', 'success')
        return redirect(url_for('members.index'))

    return render_template('members/edit.html', member=member)


@members_bp.route('/<int:member_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete(member_id):
    member = Member.query.get_or_404(member_id)
    user = member.user

    # These tables require member_id (NOT NULL) — delete dependent rows first,
    # or SQLAlchemy tries to null out member_id on them and violates the constraint.
    Membership.query.filter_by(member_id=member.id).delete()
    Attendance.query.filter_by(member_id=member.id).delete()
    Progress.query.filter_by(member_id=member.id).delete()
    WorkoutLog.query.filter_by(member_id=member.id).delete()

    db.session.delete(member)
    db.session.delete(user)
    db.session.commit()
    flash('Member deleted successfully.', 'success')
    return redirect(url_for('members.index'))