from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models.models import WorkoutPlan, Exercise, WorkoutPlanExercise
from app.utils import role_required

workouts_bp = Blueprint('workouts', __name__)


@workouts_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    q    = request.args.get('q', '').strip()

    query = WorkoutPlan.query
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                WorkoutPlan.name.ilike(like),
                WorkoutPlan.category.ilike(like),
            )
        )
    query = query.order_by(WorkoutPlan.created_at.desc())
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    return render_template('workouts/index.html',
                           plans=pagination.items,
                           pagination=pagination,
                           q=q)


@workouts_bp.route('/<int:plan_id>')
@login_required
def detail(plan_id):
    plan = WorkoutPlan.query.get_or_404(plan_id)
    plan_exercises = (
        WorkoutPlanExercise.query
        .filter_by(workout_plan_id=plan_id)
        .order_by(WorkoutPlanExercise.order)
        .all()
    )
    return render_template('workouts/detail.html', plan=plan, plan_exercises=plan_exercises)


@workouts_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'trainer')
def add():
    exercises = Exercise.query.order_by(Exercise.name).all()

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        description = (request.form.get('description') or '').strip()
        category = (request.form.get('category') or '').strip()

        if not name:
            flash('Workout plan name is required.', 'danger')
            return render_template('workouts/add.html', exercises=exercises, form_data=request.form)

        plan = WorkoutPlan(
            name=name,
            description=description,
            category=category,
            created_by=current_user.id
        )
        db.session.add(plan)
        db.session.flush()

        exercise_ids = request.form.getlist('exercise_id[]')
        sets_list = request.form.getlist('sets[]')
        reps_list = request.form.getlist('reps[]')
        rest_list = request.form.getlist('rest_seconds[]')

        for idx, ex_id_str in enumerate(exercise_ids):
            try:
                ex_id = int(ex_id_str)
            except (ValueError, TypeError):
                continue
            if not Exercise.query.get(ex_id):
                continue

            def _int_or_none(lst, i):
                try:
                    return int(lst[i]) if i < len(lst) and lst[i] else None
                except (ValueError, TypeError):
                    return None

            pe = WorkoutPlanExercise(
                workout_plan_id=plan.id,
                exercise_id=ex_id,
                sets=_int_or_none(sets_list, idx),
                reps=_int_or_none(reps_list, idx),
                rest_seconds=_int_or_none(rest_list, idx),
                order=idx + 1
            )
            db.session.add(pe)

        db.session.commit()
        flash('Workout plan added successfully!', 'success')
        return redirect(url_for('workouts.detail', plan_id=plan.id))

    return render_template('workouts/add.html', exercises=exercises)


@workouts_bp.route('/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'trainer')
def edit(plan_id):
    plan = WorkoutPlan.query.get_or_404(plan_id)
    exercises = Exercise.query.order_by(Exercise.name).all()
    plan_exercises = (
        WorkoutPlanExercise.query
        .filter_by(workout_plan_id=plan_id)
        .order_by(WorkoutPlanExercise.order)
        .all()
    )

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        description = (request.form.get('description') or '').strip()
        category = (request.form.get('category') or '').strip()

        if not name:
            flash('Workout plan name is required.', 'danger')
            return render_template('workouts/edit.html', plan=plan, exercises=exercises,
                                   plan_exercises=plan_exercises, form_data=request.form)

        plan.name = name
        plan.description = description
        plan.category = category

        for pe in plan.plan_exercises:
            db.session.delete(pe)
        db.session.flush()

        exercise_ids = request.form.getlist('exercise_id[]')
        sets_list = request.form.getlist('sets[]')
        reps_list = request.form.getlist('reps[]')
        rest_list = request.form.getlist('rest_seconds[]')

        for idx, ex_id_str in enumerate(exercise_ids):
            try:
                ex_id = int(ex_id_str)
            except (ValueError, TypeError):
                continue
            if not Exercise.query.get(ex_id):
                continue

            def _int_or_none(lst, i):
                try:
                    return int(lst[i]) if i < len(lst) and lst[i] else None
                except (ValueError, TypeError):
                    return None

            pe = WorkoutPlanExercise(
                workout_plan_id=plan.id,
                exercise_id=ex_id,
                sets=_int_or_none(sets_list, idx),
                reps=_int_or_none(reps_list, idx),
                rest_seconds=_int_or_none(rest_list, idx),
                order=idx + 1
            )
            db.session.add(pe)

        db.session.commit()
        flash('Workout plan updated successfully!', 'success')
        return redirect(url_for('workouts.detail', plan_id=plan.id))

    return render_template('workouts/edit.html', plan=plan, exercises=exercises,
                           plan_exercises=plan_exercises)


@workouts_bp.route('/<int:plan_id>/delete', methods=['POST'])
@login_required
@role_required('admin', 'trainer')
def delete(plan_id):
    plan = WorkoutPlan.query.get_or_404(plan_id)
    for pe in plan.plan_exercises:
        db.session.delete(pe)
    db.session.delete(plan)
    db.session.commit()
    flash('Workout plan deleted successfully.', 'success')
    return redirect(url_for('workouts.index'))
