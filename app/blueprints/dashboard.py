from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.models import (
    Member, Attendance, Membership, Payment, WorkoutLog
)
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


def _build_activity_feed(attendance_q, workout_q, membership_q, limit=10):
    """Merge attendance / workout / membership events into one feed,
    newest first, capped at `limit`."""
    events = []

    for record in attendance_q:
        member_name = record.member.user.first_name or record.member.user.email
        events.append({
            'name': member_name,
            'action': 'Checked In',
            'badge': 'success',
            'time': record.check_in,
        })
        if record.check_out:
            events.append({
                'name': member_name,
                'action': 'Checked Out',
                'badge': 'secondary',
                'time': record.check_out,
            })

    for log in workout_q:
        member_name = log.member.user.first_name or log.member.user.email
        events.append({
            'name': member_name,
            'action': 'Workout Completed',
            'badge': 'primary',
            'time': log.created_at,
        })

    for membership in membership_q:
        member_name = membership.member.user.first_name or membership.member.user.email
        label = 'Membership Renewed' if membership.status == 'active' else 'Membership Updated'
        events.append({
            'name': member_name,
            'action': label,
            'badge': 'warning',
            'time': membership.created_at,
        })

    events = [e for e in events if e['time'] is not None]
    events.sort(key=lambda e: e['time'], reverse=True)
    return events[:limit]


def _admin_or_trainer_context():
    today_start = datetime.combine(datetime.today(), datetime.min.time())
    month_start = today_start.replace(day=1)
    week_from_now = datetime.today().date() + timedelta(days=7)

    active_members = Member.query.count()

    attendance_today = Attendance.query.filter(
        Attendance.check_in >= today_start
    ).count()

    expiring_soon = Membership.query.filter(
        Membership.status == 'active',
        Membership.end_date >= datetime.today().date(),
        Membership.end_date <= week_from_now,
    ).count()

    monthly_revenue = Payment.query.filter(
        Payment.status == 'completed',
        Payment.payment_date >= month_start,
    ).with_entities(Payment.amount).all()
    monthly_revenue_total = sum(amount for (amount,) in monthly_revenue)

    recent_attendance = Attendance.query.order_by(Attendance.check_in.desc()).limit(10).all()
    recent_workouts = WorkoutLog.query.order_by(WorkoutLog.created_at.desc()).limit(10).all()
    recent_memberships = Membership.query.order_by(Membership.created_at.desc()).limit(10).all()

    activity = _build_activity_feed(recent_attendance, recent_workouts, recent_memberships)

    return {
        'is_member_view': False,
        'stat1_label': 'Active Members',
        'stat1_value': active_members,
        'stat1_icon': 'bi-people',
        'stat2_label': 'Attendance Today',
        'stat2_value': attendance_today,
        'stat2_icon': 'bi-calendar-check',
        'stat3_label': 'Membership Expiry (7 days)',
        'stat3_value': expiring_soon,
        'stat3_icon': 'bi-ticket-perforated',
        'stat4_label': 'Revenue (This Month)',
        'stat4_value': f'${monthly_revenue_total:,.2f}',
        'stat4_icon': 'bi-cash-coin',
        'activity': activity,
    }


def _member_context():
    member = Member.query.filter_by(user_id=current_user.id).first()

    if not member:
        return {
            'is_member_view': True,
            'stat1_label': 'My Attendance (This Month)',
            'stat1_value': 0,
            'stat1_icon': 'bi-calendar-check',
            'stat2_label': "Today's Status",
            'stat2_value': 'No profile yet',
            'stat2_icon': 'bi-person-check',
            'stat3_label': 'Membership Expiry',
            'stat3_value': 'N/A',
            'stat3_icon': 'bi-ticket-perforated',
            'stat4_label': 'Workouts Logged',
            'stat4_value': 0,
            'stat4_icon': 'bi-list-check',
            'activity': [],
        }

    today_start = datetime.combine(datetime.today(), datetime.min.time())
    month_start = today_start.replace(day=1)

    my_attendance_month = Attendance.query.filter(
        Attendance.member_id == member.id,
        Attendance.check_in >= month_start,
    ).count()

    checked_in_today = Attendance.query.filter(
        Attendance.member_id == member.id,
        Attendance.check_in >= today_start,
        Attendance.check_out.is_(None),
    ).first() is not None

    active_membership = Membership.query.filter_by(
        member_id=member.id, status='active'
    ).order_by(Membership.end_date.desc()).first()

    if active_membership:
        days_left = (active_membership.end_date - datetime.today().date()).days
        expiry_display = f'{days_left} days left' if days_left >= 0 else 'Expired'
    else:
        expiry_display = 'No active plan'

    workouts_logged = WorkoutLog.query.filter_by(member_id=member.id).count()

    recent_attendance = Attendance.query.filter_by(member_id=member.id).order_by(
        Attendance.check_in.desc()).limit(10).all()
    recent_workouts = WorkoutLog.query.filter_by(member_id=member.id).order_by(
        WorkoutLog.created_at.desc()).limit(10).all()
    recent_memberships = Membership.query.filter_by(member_id=member.id).order_by(
        Membership.created_at.desc()).limit(10).all()

    activity = _build_activity_feed(recent_attendance, recent_workouts, recent_memberships)

    return {
        'is_member_view': True,
        'stat1_label': 'My Attendance (This Month)',
        'stat1_value': my_attendance_month,
        'stat1_icon': 'bi-calendar-check',
        'stat2_label': "Today's Status",
        'stat2_value': 'Checked In' if checked_in_today else 'Not Checked In',
        'stat2_icon': 'bi-person-check',
        'stat3_label': 'Membership Expiry',
        'stat3_value': expiry_display,
        'stat3_icon': 'bi-ticket-perforated',
        'stat4_label': 'Workouts Logged',
        'stat4_value': workouts_logged,
        'stat4_icon': 'bi-list-check',
        'activity': activity,
    }


@dashboard_bp.route('/')
@login_required
def index():
    if current_user.role in ('admin', 'trainer'):
        context = _admin_or_trainer_context()
    else:
        context = _member_context()

    return render_template('dashboard/index.html', **context)
