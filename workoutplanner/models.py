from enum import unique
from workoutplanner import db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.orderinglist import ordering_list
import json
import click
from flask.cli import with_appcontext
from workoutplanner.links import *
from flask import url_for

class User(db.Model):
    """
    Database model for User. Includes unique username and relationships to moves and workouts created by the user.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)

    user_moves = db.relationship("Move", back_populates="user")
    workouts = db.relationship("WorkoutPlan", back_populates="user")
    
    def serialize(self):
        return {
            "username": self.username
        }
        
    def deserialize(self, doc):
        self.username = doc["username"]

    def get_url(self):
        return "/api/users/" + self.username + "/"
    
    def get_collection_url(self):
        return "/api/users/"

    @staticmethod
    def json_schema():
        return json.load(open('workoutplanner/schemas/user_schema.json'))

class WorkoutPlan(db.Model):
    """
    Database model for WorkoutPlan. Includes references to the creator of the plan and ordered list of moves in the plan.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user = db.relationship("User", back_populates="workouts", uselist=False)
    workout_moves = db.relationship("MoveListItem", back_populates="plan", order_by="MoveListItem.position", collection_class=ordering_list("position"))

    __table_args__ = (db.UniqueConstraint("name", "user_id", name="_name_user_constraint"),)

    def serialize(self, short_form=False):
        if short_form:
            return {
                "name": self.name
            }
        return {
            "name": self.name,
            "user": self.user.username
        }
        
    def deserialize(self, doc):
        self.name = doc["name"]
        self.user_id = doc["user_id"]
        
    def get_url(self):
        return "/api/users/" + self.user.username + "/workouts/" + self.name + "/"
    
    def get_collection_url(self):
        return "/api/users/" + self.user.username + "/workouts/"

    @staticmethod
    def json_schema():
        return json.load(open('workoutplanner/schemas/workout_plan_schema.json'))

class MoveListItem(db.Model):
    """
    Database model for MoveListItem. Is an instance of a list item in a workout plan.
    """

    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer, nullable=False)

    repetitions = db.Column(db.Integer)

    plan_id = db.Column(db.Integer, db.ForeignKey("workout_plan.id", ondelete="CASCADE"), nullable=False)
    move_id = db.Column(db.Integer, db.ForeignKey("move.id"), nullable=False)

    move = db.relationship("Move", back_populates="workout_move", uselist=False)
    plan = db.relationship("WorkoutPlan", back_populates="workout_moves", uselist=False)

    def serialize(self, short_form=False):
        if short_form:
            return {
                "position": self.position,
                "move": self.move.name
            }
        return {
            "position": self.position,
            "repetitions": self.repetitions,
            "plan": self.plan.name,
            "move": self.move.name
        }
        
    def deserialize(self, doc):
        self.position = doc["position"]
        self.repetitions = doc["repetitions"]
        self.plan_id = doc["plan_id"]
        self.move_id = doc["move_id"]

    def get_url(self):
        return "/api/users/" + self.plan.user.username + "/workouts/" + self.plan.name + "/moves/" + str(self.position) + "/"
    
    def get_collection_url(self):
        return "/api/users/" + self.plan.user.username + "/workouts/" + self.plan.name + "/moves/"

    @staticmethod
    def json_schema():
        return json.load(open('workoutplanner/schemas/move_list_item_schema.json'))

class Move(db.Model):
    """
    Database model for Move. Includes references to the creator of the move information about the move.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    user = db.relationship("User", back_populates="user_moves", uselist=False)
    workout_move = db.relationship("MoveListItem", back_populates="move")

    __table_args__ = (db.UniqueConstraint("name", "user_id", name="_name_user_constraint"),)

    def serialize(self, short_form=False):
        if short_form:
            return {
                "name": self.name,
            }
        return {
            "name": self.name,
            "description": self.description,
            "user": self.user.username
        }
        
    def deserialize(self, doc):
        self.name = doc["name"]
        self.description = doc["description"]
        self.user_id = doc["user_id"]

    def get_url(self):
        return "/api/users/" + self.user.username + "/moves/" + self.name + "/"
        
    def get_collection_url(self):
        return "/api/users/" + self.user.username + "/moves/"


    @staticmethod
    def json_schema():
        return json.load(open('workoutplanner/schemas/move_schema.json'))



# Utility functions to create and populate a database
@click.command("init-db")
@with_appcontext
def initialize_db_command():
    db.create_all()

@click.command("gen-testdata")
@with_appcontext
def populate_db_command():
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

    p1.workout_moves.append(MoveListItem(move=m1))
    p1.workout_moves.append(MoveListItem(move=m3))
    p1.workout_moves.append(MoveListItem(move=m1))

    p2.workout_moves.append(MoveListItem(move=m2, repetitions=4))

    db.session.commit()
    
@click.command("nuke-db")
@with_appcontext
def nuke_db_command():
    db.drop_all()
    db.session.commit()
    