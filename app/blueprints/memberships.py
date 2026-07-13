from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models.models import MembershipPlan, Membership, Member, User
from app.utils import role_required
from datetime import datetime, timedelta

memberships_bp = Blueprint('memberships', __name__)


@memberships_bp.route('/plans')
@login_required
@role_required('admin')
def plans():
    plans = MembershipPlan.query.filter_by(is_active=True).all()
    return render_template('memberships/plans.html', plans=plans)


@memberships_bp.route('/plans/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_plan():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        duration_months = request.form.get('duration_months', type=int)
        price = request.form.get('price', type=float)
        description = (request.form.get('description') or '').strip()

        errors = []
        if not name:
            errors.append('Plan name is required.')
        if not duration_months or duration_months <= 0:
            errors.append('Duration must be a positive number of months.')
        if price is None or price < 0:
            errors.append('Price must be zero or greater.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('memberships/add_plan.html', form_data=request.form)

        plan = MembershipPlan(
            name=name,
            duration_months=duration_months,
            price=price,
            description=description,
            is_active=True
        )
        db.session.add(plan)
        db.session.commit()

        flash('Membership plan added successfully!', 'success')
        return redirect(url_for('memberships.plans'))

    return render_template('memberships/add_plan.html')


@memberships_bp.route('/plans/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_plan(plan_id):
    plan = MembershipPlan.query.get_or_404(plan_id)

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        duration_months = request.form.get('duration_months', type=int)
        price = request.form.get('price', type=float)
        description = (request.form.get('description') or '').strip()

        errors = []
        if not name:
            errors.append('Plan name is required.')
        if not duration_months or duration_months <= 0:
            errors.append('Duration must be a positive number of months.')
        if price is None or price < 0:
            errors.append('Price must be zero or greater.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('memberships/edit_plan.html', plan=plan, form_data=request.form)

        plan.name = name
        plan.duration_months = duration_months
        plan.price = price
        plan.description = description
        db.session.commit()

        flash('Membership plan updated successfully!', 'success')
        return redirect(url_for('memberships.plans'))

    return render_template('memberships/edit_plan.html', plan=plan)


@memberships_bp.route('/plans/<int:plan_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_plan(plan_id):
    plan = MembershipPlan.query.get_or_404(plan_id)
    plan.is_active = False
    db.session.commit()
    flash('Membership plan deactivated successfully.', 'success')
    return redirect(url_for('memberships.plans'))


@memberships_bp.route('/')
@login_required
@role_required('admin', 'trainer')
def index():
    memberships = Membership.query.order_by(Membership.created_at.desc()).all()
    return render_template('memberships/index.html', memberships=memberships)


@memberships_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_membership():
    members = Member.query.join(User).order_by(User.first_name, User.last_name).all()
    plans = MembershipPlan.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        member_id = request.form.get('member_id', type=int)
        plan_id = request.form.get('plan_id', type=int)
        start_date_str = (request.form.get('start_date') or '').strip()
        status = (request.form.get('status') or 'active').strip()
        payment_status = (request.form.get('payment_status') or 'pending').strip()

        errors = []
        member = Member.query.get(member_id) if member_id else None
        plan = MembershipPlan.query.get(plan_id) if plan_id else None
        start_date = None

        if not member:
            errors.append('Please select a member.')
        if not plan:
            errors.append('Please select a membership plan.')
        if not start_date_str:
            errors.append('Start date is required.')
        else:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append('Start date must be a valid date.')

        if status not in ('active', 'expired', 'cancelled'):
            errors.append('Invalid status.')
        if payment_status not in ('pending', 'paid', 'failed'):
            errors.append('Invalid payment status.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('memberships/add_membership.html',
                                    members=members, plans=plans, form_data=request.form)

        end_date = start_date + timedelta(days=30 * plan.duration_months)

        membership = Membership(
            member_id=member.id,
            plan_id=plan.id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            payment_status=payment_status
        )
        db.session.add(membership)
        db.session.commit()

        flash('Membership assigned successfully!', 'success')
        return redirect(url_for('memberships.index'))

    return render_template('memberships/add_membership.html', members=members, plans=plans)


@memberships_bp.route('/<int:membership_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_membership(membership_id):
    membership = Membership.query.get_or_404(membership_id)
    members = Member.query.join(User).order_by(User.first_name, User.last_name).all()
    plans = MembershipPlan.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        member_id = request.form.get('member_id', type=int)
        plan_id = request.form.get('plan_id', type=int)
        start_date_str = (request.form.get('start_date') or '').strip()
        end_date_str = (request.form.get('end_date') or '').strip()
        status = (request.form.get('status') or 'active').strip()
        payment_status = (request.form.get('payment_status') or 'pending').strip()

        errors = []
        member = Member.query.get(member_id) if member_id else None
        plan = MembershipPlan.query.get(plan_id) if plan_id else None
        start_date = end_date = None

        if not member:
            errors.append('Please select a member.')
        if not plan:
            errors.append('Please select a membership plan.')

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            errors.append('Start date must be a valid date.')

        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            errors.append('End date must be a valid date.')

        if start_date and end_date and end_date < start_date:
            errors.append('End date cannot be before the start date.')

        if status not in ('active', 'expired', 'cancelled'):
            errors.append('Invalid status.')
        if payment_status not in ('pending', 'paid', 'failed'):
            errors.append('Invalid payment status.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('memberships/edit_membership.html',
                                    membership=membership, members=members, plans=plans,
                                    form_data=request.form)

        membership.member_id = member.id
        membership.plan_id = plan.id
        membership.start_date = start_date
        membership.end_date = end_date
        membership.status = status
        membership.payment_status = payment_status
        db.session.commit()

        flash('Membership updated successfully!', 'success')
        return redirect(url_for('memberships.index'))

    return render_template('memberships/edit_membership.html',
                            membership=membership, members=members, plans=plans)


@memberships_bp.route('/<int:membership_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_membership(membership_id):
    membership = Membership.query.get_or_404(membership_id)
    db.session.delete(membership)
    db.session.commit()
    flash('Membership record deleted successfully.', 'success')
    return redirect(url_for('memberships.index'))
