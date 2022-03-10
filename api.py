"""
REST API implementation
ProgrammableWeb Project, Workout  planner

Author: Eemil Hyvari, Antti Luukkonen and Oskar Byman
"""

import json
from turtle import pos
from flask import Flask, Response, request
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from jsonschema import validate, ValidationError
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, MethodNotAllowed
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

    def post(self) -> Union[Response, tuple[str, int]]:
        try:
            if request.json == None:
                raise UnsupportedMediaType

            try:
                validate(request.json, json.loads("schemas/user_schema.json"))
            except ValidationError as e:
                raise BadRequest(description=str(e))

            username  = request.json["username"]

            user = models.User(username=username)
            db.session.add(user)
            db.session.commit()
            return Response(api.url_for(user), status=200)
        except models.IntegrityError:
            db.session.rollback()
            raise Conflict(
                409,
                "User already exists"
            )

    def get(self) -> tuple[list, int]:

        users = []
        for user in models.User.query.all():
            users.append(
                {
                    "username": user.username
                }
            )
        return users, 200

class UserItem(Resource):
    """
    User resource
    Contains methods for  adding users and retrieving the whole list of users.
    """

    def put(self, user) -> Union[Response, tuple[str, int]]:
        if request.json == None:
            raise UnsupportedMediaType

        try:
            validate(request.json, models.User.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        
        current_user = models.User.query.filter_by(username=user)
        if not current_user:
            raise NotFound
        current_user.username  = request.json["username"]

        db.session.commit()
        return Response(api.url_for(user), status=200)

    def get(self, user) -> tuple[list, int]:

        query_result = models.User.query.filter_by(username=user).first()

        if not query_result:
            raise NotFound

        return query_result, 200



class WorkoutPlanCollection(Resource):
    """
    Workout plan resource
    Contains methods for adding 
    """

    def post(self) -> Union[Response, tuple[str, int]]:
        try:
            if request.json == None:
                raise UnsupportedMediaType

            try:
                validate(request.json, models.WorkoutPlan.json_schema())
            except ValidationError as e:
                raise BadRequest(description=str(e))

            name  = request.json["name"]
            username = models.User.query.filter_by(username=request.json["username"])

            plan = models.WorkoutPlan(name=name, username=username)

            db.session.add(plan)
            db.session.commit()
            return Response(api.url_for(plan), status=200)
        except KeyError:
            return "Incomplete request", 400
        except models.IntegrityError:
            db.session.rollback()
            raise Conflict(
                409,
                "Workout plan already exists"
            )

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
                    "creator": models.User.query.get(plan.username).username
                }
            )
        return plans, 200

class WorkoutPlanItem(Resource):
    """
    Workout plan resource
    Contains methods for adding 
    """

    def put(self, user, workout) -> Union[Response, tuple[str, int]]:
        try:
            if request.json == None:
                raise UnsupportedMediaType

            try:
                validate(request.json, models.WorkoutPlan.json_schema())
            except ValidationError as e:
                raise BadRequest(description=str(e))

            user_id = models.User.query.get(user).id
            current_workout = models.WorkoutPlan.query.filter_by(user_id=user_id, name=workout)
            if not current_workout:
                raise NotFound
            current_workout.name = request.json["name"]

            db.session.commit()
            return Response(api.url_for(current_workout), status=200)
        except KeyError:
            return "Incomplete request", 400

    def get(self, workout, user=None) -> tuple[list, int]:

        if user:
            user_id = models.User.query.get(user).id
            query_result = models.WorkoutPlan.query.filter_by(name=workout, user_id=user_id).first()
        else:
            query_result = models.WorkoutPlan.query.filter_by(name=workout).first()
        if not query_result:
            raise NotFound
        return query_result, 200

class MoveCollection(Resource):
    """
    Workout move resource
    Contains methods for adding a new move or retrieving the whole collection

    Available at the following URI:s
    /api/users/{user}/workouts/{workout}/moves
    /api/users/{user}/moves  TODO Get portion and check that poster is same as in json
    /api/moves
    """

    def post(self, user=None, workout=None) -> Union[Response, tuple[str, int]]:
        try:
            if request.json == None:
                raise UnsupportedMediaType
            #  If the target URI is a move in a users workout uses the move list item wrapper model
            if workout and user:
                try:
                    validate(request.json, models.MoveListItem.json_schema())
                except ValidationError as e:
                    raise BadRequest(description=str(e))
                #  Get link ids to link the correct move and plan to the wrapper
                plan_id  = models.WorkoutPlan.query.filter_by(user=user, name=workout).first().id
                creator_id = models.User.query.filter_by(username=user).first().id
                move_id = models.Move.query.filter_by(name=request.json["move_name"], user_id=creator_id).first().id
                #  Checks if the optional repetitions is present in the request
                if "repetitions" in request.json:
                    repetitions = request.json["repetitions"]
                else:
                    repetitions = None
                #  Checks if the optional position is present in the request
                if "position" in request.json:
                    position = request.json["position"]
                    #  Queries current positions of the moves in the same plan 
                    #  with a position equal or larger than the on in the request.
                    #  Increments the current positions with one to enable inserting the new position
                    current_positions = models.MoveListItem.query.filter(plan_id == plan_id, position >= position)
                    for pos in current_positions:
                        pos += 1
                else:
                    #  If the position was not present in the request set it to the last position in the plan.
                    #  The next free index will be the length of the result array
                    current_position = len(models.MoveListItem.query.filter_by(plan_id=plan_id))
                    position = current_position
                if not move_id or not plan_id or not creator_id:
                    raise NotFound
                move = models.MoveListItem(position=position, plan_id=plan_id, move_id=move_id, repetitions=repetitions)
            elif user and not workout:
                #  If the move was posted to the /api/moves URI it will be added as a move item
                try:
                    validate(request.json, models.Move.json_schema())
                except ValidationError as e:
                    raise BadRequest(description=str(e))
                name  = request.json["name"]
                user_id = models.User.query.filter_by(username=user).id
                description = request.json["description"]

                if name is None or user_id is None or description is None:
                    return "Incomplete request", 400

                move = models.Move(name=name, user_id=user_id, description=description)
            else:
                raise MethodNotAllowed
            #  Adds the move in to the database and commits all the changes
            db.session.add(move)
            db.session.commit()
            return Response(api.url_for(move), status=200)
        except KeyError:
            return "Incomplete request", 400
        except models.IntegrityError:
            db.session.rollback()
            raise Conflict(
                409,
                "Move already exists"
            )

    def get(self, user=None, workout=None) -> tuple[list, int]:
        
        moves = []
        if user and workout:
        #  If the query is to a users workout, filter the results based on it
        #  Queries the needed information from the wrapped move based on the move_id in the move list item
            plan_id  = models.WorkoutPlan.query.filter_by(user=user, name=workout).first().id
            query = models.MoveListItem.query.filter_by(plan_id=plan_id).all()
            for move in query:
                moves.append(
                    {
                        "name": models.Move.query.filter_by(id=move.move_id).first().name,
                        "creator": models.User.query.get(
                                        models.Move.query.filter_by(id=move.move_id).first().creator_id
                                    ).username,
                        "description": models.Move.query.filter_by(id=move.move_id).first().description,
                        "repetitions": move.repetitions,
                        "position": move.position
                    }
                )
        else:
        #  If the query was to the general move collection, only return the base info of a move
            query = models.Move.query.all()
            for move in query:
                moves.append(
                    {
                        "name": move.name,
                        "creator": models.User.query.get(move.creator_id).username,
                        "description": move.description
                    }
                )
        return moves, 200

class MoveItem(Resource):
    """
    Workout move resource
    Contains methods for adding 
    """

    def put(self) -> Union[Response, tuple[str, int]]:
        try:
            if request.json == None:
                raise UnsupportedMediaType

            try:
                validate(request.json, models.Move.json_schema())
            except ValidationError as e:
                raise BadRequest(description=str(e))

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
            raise Conflict(
                409,
                "Move already exists"
            )

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

