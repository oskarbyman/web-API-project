"""
REST API implementation
ProgrammableWeb Project, Workout  planner

Author: Eemil Hyvari, Antti Luukkonen and Oskar Byman
"""

import json
from flask import Flask, Response, request
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from typing import Union
import models

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api = Api(app)

class UserCollection(Resource):
    """
    User resource
    Contains methods for  adding users and retrieving the whole list of users.
    """

    def post(self, user: dict) -> Union[Response, tuple[str, int]]:
        try:
            if request.json == None:
                return "Request content type must be JSON", 415

            username  = request.json["username"]

            if username is None:
                return "Incomplete request", 400

            user = models.User(username=username)
            db.session.add(user)
            db.session.commit()
            return Response(api.url_for(user), status=200)
        except KeyError:
            return "Incomplete requests", 400
        except models.IntegrityError:
            db.session.rollback()
            return "User already exists", 409

    def get(self) -> tuple[list, int]:

        users = []
        for user in models.User.query.all():
            users.append(
                {
                    "username": user.username
                }
            )
        return users, 200

class WorkoutPlanCollection(Resource):
    """
    Workout plan resource
    Contains methods for adding 
    """

    def post(self, plan: dict) -> Union[Response, tuple[str, int]]:
        try:
            if request.json == None:
                return "Request content type must be JSON", 415

            name  = request.json["name"]
            creator = models.User.query.filter_by(username=request.json["username"])
            moves = "TODO"

            if name is None or creator is None:
                return "Incomplete request", 400

            plan = models.WorkoutPlan(name=name, creator=creator, moves=moves)

            db.session.add(plan)
            db.session.commit()
            return Response(api.url_for(plan), status=200)
        except KeyError:
            return "Incomplete request", 400
        except models.IntegrityError:
            db.session.rollback()
            return "Plan already exists", 409

    def get(self, name: str="") -> tuple[list, int]:
        
        plans = []
        if name:
            query = models.WorkoutPlan.query.filter_by(name=name).all()
        else:
            query = models.WorkoutPlan.query.all()
        for plan in query:
            plans.append(
                {
                    "name": plan.name,
                    "creator": models.User.query.get(plan.creator_id).username,
                    "moves": "TODO"
                }
            )
        return plans, 200

class WorkoutMoveCollection(Resource):
    """
    Workout move resource
    Contains methods for adding 
    """

    def post(self, move: dict) -> Union[Response, tuple[str, int]]:
        try:
            if request.json == None:
                return "Request content type must be JSON", 415

            name  = request.json["name"]
            creator = models.User.query.filter_by(username=request.json["username"])
            description = request.json["description"]

            if name is None or creator is None or description is None:
                return "Incomplete request", 400

            move = models.WorkoutMove(name=name, creator=creator, description=description)

            db.session.add(move)
            db.session.commit()
            return Response(api.url_for(move), status=200)
        except KeyError:
            return "Incomplete request", 400
        except models.IntegrityError:
            db.session.rollback()
            return "Plan already exists", 409

    def get(self, name: str="") -> tuple[list, int]:
        
        moves = []
        if name:
            query = models.WorkoutMove.query.filter_by(name=name).all()
        else:
            query = models.WorkoutMove.query.all()
        for move in query:
            moves.append(
                {
                    "name": move.name,
                    "creator": models.User.query.get(move.creator_id).username,
                    "description": move.description
                }
            )
        return moves, 200
