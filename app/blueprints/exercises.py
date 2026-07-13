from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models.models import Exercise
from app.utils import role_required

exercises_bp = Blueprint('exercises', __name__)

SORT_COLS = {
    'name':       Exercise.name,
    'muscle':     Exercise.muscle_group,
    'difficulty': Exercise.difficulty,
}


@exercises_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    q    = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'name')

    query = Exercise.query
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                Exercise.name.ilike(like),
                Exercise.muscle_group.ilike(like),
                Exercise.equipment.ilike(like),
            )
        )
    order_col = SORT_COLS.get(sort, Exercise.name)
    query = query.order_by(order_col)

    pagination = query.paginate(page=page, per_page=20, error_out=False)
    return render_template('exercises/index.html',
                           exercises=pagination.items,
                           pagination=pagination,
                           q=q, sort=sort)


@exercises_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'trainer')
def add():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        muscle_group = (request.form.get('muscle_group') or '').strip()
        equipment = (request.form.get('equipment') or '').strip()
        difficulty = (request.form.get('difficulty') or '').strip()
        description = (request.form.get('description') or '').strip()
        default_sets = request.form.get('default_sets', type=int)
        default_reps = request.form.get('default_reps', type=int)
        default_rest_seconds = request.form.get('default_rest_seconds', type=int)

        errors = []
        if not name:
            errors.append('Exercise name is required.')
        for label, value in (('Sets', default_sets), ('Reps', default_reps), ('Rest seconds', default_rest_seconds)):
            if value is not None and value < 0:
                errors.append(f'{label} cannot be negative.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('exercises/add.html', form_data=request.form)

        exercise = Exercise(
            name=name,
            muscle_group=muscle_group,
            equipment=equipment,
            difficulty=difficulty,
            description=description,
            default_sets=default_sets,
            default_reps=default_reps,
            default_rest_seconds=default_rest_seconds
        )
        db.session.add(exercise)
        db.session.commit()

        flash('Exercise added successfully!', 'success')
        return redirect(url_for('exercises.index'))

    return render_template('exercises/add.html')


@exercises_bp.route('/<int:exercise_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'trainer')
def edit(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        muscle_group = (request.form.get('muscle_group') or '').strip()
        equipment = (request.form.get('equipment') or '').strip()
        difficulty = (request.form.get('difficulty') or '').strip()
        description = (request.form.get('description') or '').strip()
        default_sets = request.form.get('default_sets', type=int)
        default_reps = request.form.get('default_reps', type=int)
        default_rest_seconds = request.form.get('default_rest_seconds', type=int)

        errors = []
        if not name:
            errors.append('Exercise name is required.')
        for label, value in (('Sets', default_sets), ('Reps', default_reps), ('Rest seconds', default_rest_seconds)):
            if value is not None and value < 0:
                errors.append(f'{label} cannot be negative.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('exercises/edit.html', exercise=exercise, form_data=request.form)

        exercise.name = name
        exercise.muscle_group = muscle_group
        exercise.equipment = equipment
        exercise.difficulty = difficulty
        exercise.description = description
        exercise.default_sets = default_sets
        exercise.default_reps = default_reps
        exercise.default_rest_seconds = default_rest_seconds
        db.session.commit()

        flash('Exercise updated successfully!', 'success')
        return redirect(url_for('exercises.index'))

    return render_template('exercises/edit.html', exercise=exercise)


@exercises_bp.route('/<int:exercise_id>/delete', methods=['POST'])
@login_required
@role_required('admin', 'trainer')
def delete(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    db.session.delete(exercise)
    db.session.commit()
    flash('Exercise deleted successfully.', 'success')
    return redirect(url_for('exercises.index'))
