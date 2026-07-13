from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models.models import DietPlan, Member, Meal

diet_bp = Blueprint('diet', __name__)


@diet_bp.route('/')
@login_required
def index():
    if current_user.role == 'member':
        member = Member.query.filter_by(user_id=current_user.id).first()
        if not member:
            flash('Please complete your profile first.', 'warning')
            return redirect(url_for('dashboard.index'))
        plans = DietPlan.query.filter_by(member_id=member.id).all()
    else:
        plans = DietPlan.query.all()

    return render_template('diet/index.html', plans=plans)


@diet_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()

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
                return render_template('diet/add.html', members=members, form_data=request.form)

        if not name:
            flash('Diet plan name is required.', 'danger')
            members = Member.query.all() if current_user.role != 'member' else []
            return render_template('diet/add.html', members=members, form_data=request.form)

        trainer_id = None
        if current_user.role == 'trainer':
            trainer = current_user.trainer
            if trainer:
                trainer_id = trainer.id

        plan = DietPlan(
            name=name,
            description=request.form.get('description'),
            member_id=member.id,
            trainer_id=trainer_id
        )

        db.session.add(plan)
        db.session.commit()
        flash('Diet plan created successfully!', 'success')
        return redirect(url_for('diet.index'))

    members = Member.query.all() if current_user.role != 'member' else []
    return render_template('diet/add.html', members=members)


@diet_bp.route('/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(plan_id):
    plan = DietPlan.query.get_or_404(plan_id)

    # Members can only edit their own diet plans
    if current_user.role == 'member':
        member = Member.query.filter_by(user_id=current_user.id).first()
        if not member or plan.member_id != member.id:
            flash('Access denied!', 'danger')
            return redirect(url_for('diet.index'))

    members = Member.query.all() if current_user.role != 'member' else []

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()

        if not name:
            flash('Diet plan name is required.', 'danger')
            return render_template('diet/edit.html', plan=plan, members=members, form_data=request.form)

        if current_user.role != 'member':
            member_id = request.form.get('member_id', type=int)
            if member_id:
                plan.member_id = member_id

        plan.name = name
        plan.description = request.form.get('description')
        db.session.commit()

        flash('Diet plan updated successfully!', 'success')
        return redirect(url_for('diet.index'))

    return render_template('diet/edit.html', plan=plan, members=members)


@diet_bp.route('/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete(plan_id):
    plan = DietPlan.query.get_or_404(plan_id)

    # Members can only delete their own diet plans
    if current_user.role == 'member':
        member = Member.query.filter_by(user_id=current_user.id).first()
        if not member or plan.member_id != member.id:
            flash('Access denied!', 'danger')
            return redirect(url_for('diet.index'))

    # Delete associated meals first
    for meal in plan.meals:
        db.session.delete(meal)
    db.session.delete(plan)
    db.session.commit()
    flash('Diet plan deleted successfully.', 'success')
    return redirect(url_for('diet.index'))
