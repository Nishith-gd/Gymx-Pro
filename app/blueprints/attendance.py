from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.models import Attendance, Member, User
from datetime import datetime

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/')
@login_required
def index():
    if current_user.role in ['admin', 'trainer']:
        records = Attendance.query.order_by(Attendance.check_in.desc()).all()
    else:
        member = Member.query.filter_by(user_id=current_user.id).first()
        records = Attendance.query.filter_by(member_id=member.id).order_by(Attendance.check_in.desc()).all() if member else []

    return render_template('attendance/index.html', records=records)


@attendance_bp.route('/check-in', methods=['GET', 'POST'])
@login_required
def check_in():
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member and current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        if current_user.role == 'admin':
            member_id = request.form.get('member_id', type=int)
            if not member_id or not Member.query.get(member_id):
                flash('Please select a valid member.', 'danger')
                return redirect(url_for('attendance.check_in'))
        else:
            member_id = member.id

        existing = Attendance.query.filter_by(member_id=member_id, check_out=None).first()
        if existing:
            flash('Already checked in! Please check out first.', 'warning')
            return redirect(url_for('attendance.index'))

        record = Attendance(
            member_id=member_id,
            check_in=datetime.utcnow()
        )
        db.session.add(record)
        db.session.commit()

        flash('Checked in successfully!', 'success')
        return redirect(url_for('attendance.index'))

    members = Member.query.all()
    return render_template('attendance/check_in.html', members=members)


@attendance_bp.route('/check-out/<int:record_id>', methods=['POST'])
@login_required
def check_out(record_id):
    record = Attendance.query.get_or_404(record_id)

    if current_user.role not in ('admin', 'trainer'):
        member = Member.query.filter_by(user_id=current_user.id).first()
        if not member or record.member_id != member.id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'ok': False, 'error': 'Access denied.'}), 403
            flash('Access denied!', 'danger')
            return redirect(url_for('attendance.index'))

    record.check_out = datetime.utcnow()
    db.session.commit()

    # AJAX response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        duration_mins = int((record.check_out - record.check_in).total_seconds() // 60)
        return jsonify({
            'ok': True,
            'check_out': record.check_out.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_mins': duration_mins,
        })

    flash('Checked out successfully!', 'success')
    return redirect(url_for('attendance.index'))
