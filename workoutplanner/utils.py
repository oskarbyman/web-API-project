from models import db, User, WorkoutPlan, MoveList, Move

def create_db():
    db.create_all()

def populate_db():
    u1 = User(username="ProAthlete35")
    u2 = User(username="Noob")

    db.session.add(u1)
    db.session.add(u2)
    db.session.commit()

    m1 = Move(name="Push Up", user=u1)
    m2 = Move(name="Opening Fridge", user=u1)
    m3 = Move(name="Plank", user=u2)

    db.session.add(m1)
    db.session.add(m2)
    db.session.add(m3)
    db.session.commit()

    p1 = WorkoutPlan(name="Light Exercise", user=u1)
    p2 = WorkoutPlan(name="Max Suffering", user=u2)

    db.session.add(p1)
    db.session.add(p2)
    db.session.commit()

    p1.workout_moves.append(MoveList(move=m1))
    p1.workout_moves.append(MoveList(move=m3))
    p1.workout_moves.append(MoveList(move=m1))

    p2.workout_moves.append(MoveList(move=m2, repetitions=4))

    db.session.commit()
