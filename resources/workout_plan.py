import json
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, MethodNotAllowed, InternalServerError
from typing import Union
from models import *
from workoutplanner import db

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
                validate(request.json, WorkoutPlan.json_schema())
            except ValidationError as e:
                raise BadRequest(description=str(e))

            name  = request.json["name"]
            username = User.query.filter_by(username=request.json["username"])

            plan = WorkoutPlan(name=name, username=username)

            db.session.add(plan)
            db.session.commit()
            return Response(url_for(plan), status=200)
        except KeyError:
            return "Incomplete request", 400
        except IntegrityError:
            db.session.rollback()
            raise Conflict(
                409,
                "Workout plan already exists"
            )

    def get(self, name: str="") -> tuple[list, int]:
        
        plans = []
        if name:
            query = WorkoutPlan.query.filter_by(name=name).all()
        else:
            query = WorkoutPlan.query.all()
        for plan in query:
            plans.append(
                {
                    "name": plan.name,
                    "creator": User.query.get(plan.username).username
                }
            )
        return plans, 200

class WorkoutPlanItem(Resource):
    """
    Workout plan resource
    Contains methods for adding 
    """

    def put(self, user, workout) -> Union[Response, tuple[str, int]]:
        """
        Replaces a users workouts name
        """
        try:
            if request.json == None:
                raise UnsupportedMediaType

            try:
                validate(request.json, WorkoutPlan.json_schema())
            except ValidationError as e:
                raise BadRequest(description=str(e))

            user_id = User.query.get(user).id
            current_workout = WorkoutPlan.query.filter_by(user_id=user_id, name=workout)
            if not current_workout:
                raise NotFound
            current_workout.name = request.json["name"]

            db.session.commit()
            return Response(url_for(current_workout), status=200)
        except KeyError:
            return "Incomplete request", 400

    def get(self, workout, user=None) -> tuple[list, int]:
        """
        Gets all workouts or all of a certain users workouts
        """
        if user:
            user_id = User.query.get(user).id
            query_result = WorkoutPlan.query.filter_by(name=workout, user_id=user_id).first()
        else:
            query_result = WorkoutPlan.query.filter_by(name=workout).first()
        if not query_result:
            raise NotFound
        return query_result, 200

    def delete(self, user, workout):
        """
        Allows deletion of a users workout
        Obviously requires the user to be authenticated, but auth is not implemented yet
        """
        if user and workout:
            user_id = User.query.get(user).id
            query_result = WorkoutPlan.query.filter_by(name=workout, user_id=user_id).first()
            if not query_result:
                raise NotFound
            else:
                db.session.delete(query_result)
                db.session.commit()
        else:
            raise MethodNotAllowed
