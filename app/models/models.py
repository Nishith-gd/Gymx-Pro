from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    profile_pic = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Member(db.Model):
    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.id'))

    user = db.relationship('User', backref=db.backref('member', uselist=False))
    trainer = db.relationship('Trainer', backref='members')


class Trainer(db.Model):
    __tablename__ = 'trainers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    specialization = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    bio = db.Column(db.Text)
    certifications = db.Column(db.Text)

    user = db.relationship('User', backref=db.backref('trainer', uselist=False))


class MembershipPlan(db.Model):
    __tablename__ = 'membership_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    features = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)


class Membership(db.Model):
    __tablename__ = 'memberships'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('membership_plans.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='active')
    payment_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', backref='memberships')
    plan = db.relationship('MembershipPlan', backref='memberships')


class Exercise(db.Model):
    __tablename__ = 'exercises'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    muscle_group = db.Column(db.String(50))
    equipment = db.Column(db.String(100))
    difficulty = db.Column(db.String(20))
    description = db.Column(db.Text)
    default_sets = db.Column(db.Integer)
    default_reps = db.Column(db.Integer)
    default_rest_seconds = db.Column(db.Integer)
    image_url = db.Column(db.String(256))
    video_url = db.Column(db.String(256))


class WorkoutPlan(db.Model):
    __tablename__ = 'workout_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    trainer = db.relationship('Trainer', backref='workout_plans')
    creator = db.relationship('User', backref='workout_plans')


class WorkoutPlanExercise(db.Model):
    __tablename__ = 'workout_plan_exercises'

    id = db.Column(db.Integer, primary_key=True)
    workout_plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    sets = db.Column(db.Integer)
    reps = db.Column(db.Integer)
    rest_seconds = db.Column(db.Integer)
    order = db.Column(db.Integer)

    workout_plan = db.relationship('WorkoutPlan', backref='plan_exercises')
    exercise = db.relationship('Exercise', backref='plan_exercises')


class WorkoutLog(db.Model):
    __tablename__ = 'workout_logs'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    workout_plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.id'))
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'))
    date = db.Column(db.Date, nullable=False)
    sets_completed = db.Column(db.Integer)
    reps_completed = db.Column(db.Integer)
    weight_used = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', backref='workout_logs')
    workout_plan = db.relationship('WorkoutPlan', backref='logs')
    exercise = db.relationship('Exercise', backref='logs')


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    member = db.relationship('Member', backref='attendance_records')


class Progress(db.Model):
    __tablename__ = 'progress'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    body_fat_percent = db.Column(db.Float)
    chest = db.Column(db.Float)
    waist = db.Column(db.Float)
    arms = db.Column(db.Float)
    legs = db.Column(db.Float)
    shoulders = db.Column(db.Float)
    notes = db.Column(db.Text)
    photo_url = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', backref='progress_records')


class DietPlan(db.Model):
    __tablename__ = 'diet_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.id'))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', backref='diet_plans')
    trainer = db.relationship('Trainer', backref='diet_plans')


class Meal(db.Model):
    __tablename__ = 'meals'

    id = db.Column(db.Integer, primary_key=True)
    diet_plan_id = db.Column(db.Integer, db.ForeignKey('diet_plans.id'), nullable=False)
    meal_type = db.Column(db.String(20))
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    calories = db.Column(db.Integer)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat = db.Column(db.Float)

    diet_plan = db.relationship('DietPlan', backref='meals')


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    membership_id = db.Column(db.Integer, db.ForeignKey('memberships.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    membership = db.relationship('Membership', backref='payments')
