from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models.models import Progress, Member
from app.utils import role_required
from datetime import datetime

progress_bp = Blueprint('progress', __name__)


@progress_bp.route('/')
@login_required
def index():
    if current_user.role == 'member':
        member = Member.query.filter_by(user_id=current_user.id).first()
        if not member:
            flash('Please complete your profile first.', 'warning')
            return redirect(url_for('dashboard.index'))
        records = Progress.query.filter_by(member_id=member.id).order_by(Progress.date.desc()).all()
    else:
        records = Progress.query.order_by(Progress.date.desc()).all()

    return render_template('progress/index.html', records=records)


@progress_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        if current_user.role == 'member':
            member = Member.query.filter_by(user_id=current_user.id).first()
            if not member:
                flash('Please complete your profile first.', 'warning')
                return redirect(url_for('dashboard.index'))
        else:
            member_id = request.form.get('member_id', type=int)
            member = Member.query.get_or_404(member_id) if member_id else None
            if not member:
                flash('Please select a valid member.', 'danger')
                members = Member.query.all()
                return render_template('progress/add.html', members=members, form_data=request.form)

        date_str = request.form.get('date')
        try:
            record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            flash('A valid date is required.', 'danger')
            members = Member.query.all() if current_user.role != 'member' else []
            return render_template('progress/add.html', members=members, form_data=request.form)

        record = Progress(
            member_id=member.id,
            date=record_date,
            weight=request.form.get('weight', type=float),
            height=request.form.get('height', type=float),
            body_fat_percent=request.form.get('body_fat_percent', type=float),
            chest=request.form.get('chest', type=float),
            waist=request.form.get('waist', type=float),
            arms=request.form.get('arms', type=float),
            legs=request.form.get('legs', type=float),
            shoulders=request.form.get('shoulders', type=float),
            notes=request.form.get('notes')
        )

        db.session.add(record)
        db.session.commit()
        flash('Progress record added successfully!', 'success')
        return redirect(url_for('progress.index'))

    members = Member.query.all() if current_user.role != 'member' else []
    return render_template('progress/add.html', members=members)


@progress_bp.route('/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(record_id):
    record = Progress.query.get_or_404(record_id)

    # Members can only edit their own records
    if current_user.role == 'member':
        member = Member.query.filter_by(user_id=current_user.id).first()
        if not member or record.member_id != member.id:
            flash('Access denied!', 'danger')
            return redirect(url_for('progress.index'))

    members = Member.query.all() if current_user.role != 'member' else []

    if request.method == 'POST':
        date_str = request.form.get('date')
        try:
            record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            flash('A valid date is required.', 'danger')
            return render_template('progress/edit.html', record=record, members=members, form_data=request.form)

        # Admins/trainers can reassign member
        if current_user.role != 'member':
            member_id = request.form.get('member_id', type=int)
            if member_id:
                record.member_id = member_id

        record.date = record_date
        record.weight = request.form.get('weight', type=float)
        record.height = request.form.get('height', type=float)
        record.body_fat_percent = request.form.get('body_fat_percent', type=float)
        record.chest = request.form.get('chest', type=float)
        record.waist = request.form.get('waist', type=float)
        record.arms = request.form.get('arms', type=float)
        record.legs = request.form.get('legs', type=float)
        record.shoulders = request.form.get('shoulders', type=float)
        record.notes = request.form.get('notes')

        db.session.commit()
        flash('Progress record updated successfully!', 'success')
        return redirect(url_for('progress.index'))

    return render_template('progress/edit.html', record=record, members=members)


@progress_bp.route('/<int:record_id>/delete', methods=['POST'])
@login_required
def delete(record_id):
    record = Progress.query.get_or_404(record_id)

    # Members can only delete their own records
    if current_user.role == 'member':
        member = Member.query.filter_by(user_id=current_user.id).first()
        if not member or record.member_id != member.id:
            flash('Access denied!', 'danger')
            return redirect(url_for('progress.index'))

    db.session.delete(record)
    db.session.commit()
    flash('Progress record deleted successfully.', 'success')
    return redirect(url_for('progress.index'))
