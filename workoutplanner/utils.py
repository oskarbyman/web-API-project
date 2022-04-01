from workoutplanner import create_app, db
from workoutplanner.models import User, WorkoutPlan, MoveListItem, Move
from werkzeug.routing import BaseConverter


class ListConverter(BaseConverter):

    def to_python(self, value):
        return value.split('+')

    def to_url(self, values):
        return '+'.join(BaseConverter.to_url(value)
                        for value in values)

#Utility functions to create and populate db
def create_db():
    app = create_app()
    with app.app_context():
        db.create_all()

def populate_db():
    app = create_app()
    with app.app_context():
        u1 = User(username="ProAthlete35")
        u2 = User(username="Noob")

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        m1 = Move(name="Push Up", description="Push your body up with your hands", user=u1)
        m2 = Move(name="Opening Fridge", description="Walk to the nearest fridge and open it", user=u1)
        m3 = Move(name="Plank", description="Use your muscles to keep your body in a straight horizontal line", user=u2)

        db.session.add(m1)
        db.session.add(m2)
        db.session.add(m3)
        db.session.commit()

        p1 = WorkoutPlan(name="Light Exercise", user=u1)
        p2 = WorkoutPlan(name="Max Suffering", user=u2)

        db.session.add(p1)
        db.session.add(p2)
        db.session.commit()

        p1.workout_moves.append(MoveListItem(move=m1, repetitions=20))
        p1.workout_moves.append(MoveListItem(move=m3, repetitions=60))
        p1.workout_moves.append(MoveListItem(move=m1, repetitions=20))

        p2.workout_moves.append(MoveListItem(move=m2, repetitions=4))

        db.session.commit()
