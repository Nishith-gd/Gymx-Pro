from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.models import Member, Trainer, Exercise, WorkoutPlan, Attendance
from app.utils import role_required
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')


# Members API
@api_bp.route('/members', methods=['GET'])
@login_required
@role_required('admin', 'trainer')
def get_members():
    members = Member.query.all()
    data = []
    for member in members:
        data.append({
            'id': member.id,
            'first_name': member.user.first_name,
            'last_name': member.user.last_name,
            'email': member.user.email
        })
    return jsonify({'members': data})


@api_bp.route('/members/<int:id>', methods=['GET'])
@login_required
def get_member(id):
    member = Member.query.get_or_404(id)
    if current_user.role not in ('admin', 'trainer') and member.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    return jsonify({
        'id': member.id,
        'first_name': member.user.first_name,
        'last_name': member.user.last_name,
        'email': member.user.email
    })


# Exercises API
@api_bp.route('/exercises', methods=['GET'])
@login_required
def get_exercises():
    exercises = Exercise.query.all()
    data = []
    for ex in exercises:
        data.append({
            'id': ex.id,
            'name': ex.name,
            'muscle_group': ex.muscle_group,
            'difficulty': ex.difficulty,
            'description': ex.description
        })
    return jsonify({'exercises': data})


@api_bp.route('/exercises', methods=['POST'])
@login_required
@role_required('admin', 'trainer')
def create_exercise():
    data = request.get_json(silent=True) or {}

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name is required'}), 400

    def to_int(value):
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    exercise = Exercise(
        name=name,
        muscle_group=data.get('muscle_group'),
        equipment=data.get('equipment'),
        difficulty=data.get('difficulty'),
        description=data.get('description'),
        default_sets=to_int(data.get('sets')),
        default_reps=to_int(data.get('reps')),
        default_rest_seconds=to_int(data.get('rest_seconds')),
    )

    db.session.add(exercise)
    db.session.commit()

    return jsonify({'id': exercise.id}), 201


# Workout Plans API
@api_bp.route('/workout-plans', methods=['GET'])
@login_required
def get_workout_plans():
    plans = WorkoutPlan.query.all()
    data = []
    for plan in plans:
        data.append({
            'id': plan.id,
            'name': plan.name,
            'description': plan.description
        })
    return jsonify({'plans': data})


# Attendance API
@api_bp.route('/attendance', methods=['GET'])
@login_required
def get_attendance():
    attendance_records = Attendance.query.order_by(Attendance.check_in.desc()).limit(50).all()
    data = []
    for record in attendance_records:
        data.append({
            'id': record.id,
            'member_id': record.member_id,
            'check_in': record.check_in.isoformat() if record.check_in else None,
            'check_out': record.check_out.isoformat() if record.check_out else None
        })
    return jsonify({'attendance': data})
