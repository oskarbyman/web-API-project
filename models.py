from api import db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.orderinglist import ordering_list

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)

    user_moves = db.relationship("Move", back_populates="user")
    workouts = db.relationship("WorkoutPlan", back_populates="user")

class WorkoutPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user = db.relationship("User", back_populates="workouts", uselist=False)
    workout_moves = db.relationship("MoveList", back_populates="plan", order_by="MoveList.position", collection_class=ordering_list("position"))

class MoveList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer, nullable=False)

    repetitions = db.Column(db.Integer)

    plan_id = db.Column(db.Integer, db.ForeignKey("workout_plan.id"), nullable=False)
    move_id = db.Column(db.Integer, db.ForeignKey("move.id"), nullable=False)

    move = db.relationship("Move", back_populates="workout_move", uselist=False)
    plan = db.relationship("WorkoutPlan", back_populates="workout_moves", uselist=False)

class Move(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user = db.relationship("User", back_populates="user_moves", uselist=False)
    workout_move = db.relationship("MoveList", back_populates="move")


