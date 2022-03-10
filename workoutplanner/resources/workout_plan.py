from os import stat
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
    Contains methods for adding a workout and getting all of the workouts

    Covers the following URIs:
    /api/users/{user}/workouts
    /api/workouts/
    """

    def post(self, user: str=None) -> Response:
        """
        Allows POST to the following URI:     
        /api/users/{user}/workouts
        """
        try:
            if not user:
                raise MethodNotAllowed
            else:
                if request.json == None:
                    raise UnsupportedMediaType

                try:
                    validate(request.json, WorkoutPlan.json_schema())
                except ValidationError as e:
                    raise BadRequest(description=str(e))
                
                name  = request.json["name"]
                user_id = User.query.get(username=request.json["username"]).id

                plan = WorkoutPlan(name=name, user_id=user_id)

                db.session.add(plan)
                db.session.commit()
                return Response(url_for(plan), status=200)
        except KeyError:
            db.session.rollback()
            raise BadRequest
        except IntegrityError:
            db.session.rollback()
            raise Conflict(
                "Workout plan already exists",
                409
            )

    def get(self, user: str=None) -> list:
        """
        Allows GET from the following URIs:
        /api/users/{user}/workouts
        /api/workouts/
        """
        plans = []
        #   If user is specified only gets workouts made by the user, else gets them all
        if user:
            user_id = User.query.get(username=request.json["username"]).id
            query = WorkoutPlan.query.filter_by(user_id=user_id).all()
        else:
            query = WorkoutPlan.query.all()
        for plan in query:
            plans.append(
                {
                    "name": plan.name,
                    "creator": User.query.get(plan.user_id).username
                }
            )
        return plans, 200

class WorkoutPlanItem(Resource):
    """
    Workout plan item resource
    Implements methods for handling a single workout

    Covers the following URIs:
    /api/users/{user}/workouts/{workout}, GET, PUT, DELETE
    /api/workouts/{workout}, GET
    """

    def put(self, user, workout) -> Union[Response, tuple[str, int]]:
        """
        Replaces a users workouts name
        Allows PUT to the following URI:
        /api/users/{user}/workouts/{workout}
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
            db.session.rollback()
            raise BadRequest

    def get(self, workout: str, user: str=None) -> tuple[dict, int]:
        """
        Gets the requested workout

        Allows GET from the following URIs:
        /api/users/{user}/workouts/{workout}
        /api/workouts/{workout}
        """
        if user:
            user_id = User.query.get(user).id
            query_result = WorkoutPlan.query.filter_by(name=workout, user_id=user_id).first()
        else:
            query_result = WorkoutPlan.query.filter_by(name=workout).first()
        if not query_result:
            raise NotFound
        result = {
            "name": query_result.name,
            "creator": User.query.get(query_result.user_id).username
        }
        return result, 200

    def delete(self, user: str, workout: str) -> Response:
        """
        Allows deletion of a users workout
        Obviously should require the user to be authenticated, but auth is not implemented yet

        Allows DELETE of the following URI:
            /api/users/{user}/workouts/{workout}
        """
        if user and workout:
            user_id = User.query.get(user).id
            query_result = WorkoutPlan.query.filter_by(name=workout, user_id=user_id).first()
            if not query_result:
                raise NotFound
            else:
                db.session.delete(query_result)
                db.session.commit()
                return Response(status=200)
        else:
            raise MethodNotAllowed
