from app import create_app, db
from app.models.models import Exercise, MembershipPlan

app = create_app()

with app.app_context():
    # Add sample membership plans
    plans = [
        MembershipPlan(name='Monthly', duration_months=1, price=50.0, description='Monthly membership'),
        MembershipPlan(name='Quarterly', duration_months=3, price=135.0, description='3 months membership with 10% discount'),
        MembershipPlan(name='Yearly', duration_months=12, price=480.0, description='12 months membership with 20% discount')
    ]
    for plan in plans:
        if not MembershipPlan.query.filter_by(name=plan.name).first():
            db.session.add(plan)
    
    # Add sample exercises
    exercises = [
        Exercise(name='Bench Press', muscle_group='Chest', equipment='Barbell', difficulty='Intermediate',
                 default_sets=3, default_reps=10, default_rest_seconds=90),
        Exercise(name='Squats', muscle_group='Legs', equipment='Barbell', difficulty='Intermediate',
                 default_sets=4, default_reps=12, default_rest_seconds=120),
        Exercise(name='Deadlift', muscle_group='Back', equipment='Barbell', difficulty='Advanced',
                 default_sets=3, default_reps=8, default_rest_seconds=180),
        Exercise(name='Bicep Curls', muscle_group='Arms', equipment='Dumbbell', difficulty='Beginner',
                 default_sets=3, default_reps=12, default_rest_seconds=60),
        Exercise(name='Plank', muscle_group='Core', equipment='Bodyweight', difficulty='Beginner',
                 default_sets=3, default_reps=1, default_rest_seconds=30)
    ]
    for exercise in exercises:
        if not Exercise.query.filter_by(name=exercise.name).first():
            db.session.add(exercise)
    
    db.session.commit()
    print('Sample data added successfully!')
