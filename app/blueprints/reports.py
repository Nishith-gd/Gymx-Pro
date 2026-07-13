from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models.models import Attendance, Member, Membership
from app.utils import role_required
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/')
@login_required
@role_required('admin', 'trainer')
def index():
    # Get today's attendance count
    today_start = datetime.combine(datetime.today(), datetime.min.time())
    today_attendance = Attendance.query.filter(Attendance.check_in >= today_start).count()
    
    # Total active members
    active_members = Member.query.count()
    
    # Total membership plans
    membership_plans = Membership.query.count()
    
    return render_template('reports/index.html', 
        today_attendance=today_attendance, 
        active_members=active_members,
        membership_plans=membership_plans)
