from workoutplanner import db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.orderinglist import ordering_list
import json

class User(db.Model):
    """
    Database model for User. Includes unique username and relationships to moves and workouts created by the user.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)

    user_moves = db.relationship("Move", back_populates="user")
    workouts = db.relationship("WorkoutPlan", back_populates="user")

    @staticmethod
    def json_schema():
        #return json.loads(open("schemas/user_schema.json"))
        return {
            "description": "A workout move",
            "type": "object",
            "required": ["username"],
            "properties":
            {
                "username": {
                    "description": "An unique username",
                    "type": "string"
                }
            }
        }

class WorkoutPlan(db.Model):
    """
    Database model for WorkoutPlan. Includes references to the creator of the plan and ordered list of moves in the plan.
    """

    #id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(64), primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)

    user = db.relationship("User", back_populates="workouts", uselist=False)
    workout_moves = db.relationship("MoveListItem", back_populates="plan", order_by="MoveListItem.position", collection_class=ordering_list("position"))

    @staticmethod
    def json_schema():
        return json.loads("schemas/workout_plan_schema.json")

class MoveListItem(db.Model):
    """
    Database model for MoveListItem. Is an instance of a list item in a workout plan.
    """

    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer, nullable=False)

    repetitions = db.Column(db.Integer)

    plan_id = db.Column(db.Integer, db.ForeignKey("workout_plan.id"), nullable=False)
    move_id = db.Column(db.Integer, db.ForeignKey("move.id"), nullable=False)

    move = db.relationship("Move", back_populates="workout_move", uselist=False)
    plan = db.relationship("WorkoutPlan", back_populates="workout_moves", uselist=False)

    @staticmethod
    def json_schema():
        return json.loads("schemas/move_item_schema.json")

class Move(db.Model):
    """
    Database model for Move. Includes references to the creator of the move information about the move.
    """

    #id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer, nullable=False)
    #name = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), primary_key=True)
    description = db.Column(db.String(256), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)

    user = db.relationship("User", back_populates="user_moves", uselist=False)
    workout_move = db.relationship("MoveListItem", back_populates="move")

    @staticmethod
    def json_schema():
        return json.loads("schemas/move_schema.json")
