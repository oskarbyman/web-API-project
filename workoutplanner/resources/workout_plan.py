from os import stat
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, MethodNotAllowed, InternalServerError
from typing import Union
from workoutplanner.models import *
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
        Create a new workout plan
        ---
        description: "Allows POST to the following URI:    /api/users/{user}/workouts, NOT from /api/workouts"
        parameters:
        - $ref: '#/components/parameters/user'
        - $ref: '#/components/parameters/workoutitem'        
        responses:
            '200':
                description: URI of the new plan
                content:
                    string:
                        example:
                            /api/users/Noob/workouts/Light Excercise

            '409':
                description: Workout plan already exists
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
                user_id = User.query.filter_by(username=user).first().id

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
        Get the list of workout plans
        ---
        description: "Allows GET from the following URIs: /api/users/{user}/workouts and /api/workouts/"
        parameters:
        - $ref: '#/components/parameters/username'   
        responses:
            '200':
                description: List of workout plans returned successfully
                content:
                    application/json:
                        schema:
                            $ref: '#definitions/WorkoutItem'
                        example:
                        -   name: Light Exercise
                            creator: Noob
                        -   name: Max Suffering
                            creator: ProAthlete35
        """
        plans = []
        #   If user is specified only gets workouts made by the user, else gets them all
        if user:
            user_id = User.query.filter_by(username=user).first().id
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
    """

    def put(self, user: str=None, workout: str=None) -> Union[Response, tuple[str, int]]:
        """
        Edit/create a workout.
        ---
        description: "Allows PUT to the following URI:  /api/users/{user}/workouts/{workout}"
        parameters:
        - $ref: '#/components/parameters/user' 
        - $ref: '#/components/parameters/workout'
        - $ref: '#/components/parameters/workoutitem'   
        responses:
            '200':
                description: Workout replaced successfully
                content:
                    string:
                        example:
                            /api/users/Noob/workouts/Light Excercise
        """
        try:
            if workout and user:
                if request.json == None:
                    raise UnsupportedMediaType
                try:
                    validate(request.json, WorkoutPlan.json_schema())
                except ValidationError as e:
                    raise BadRequest(description=str(e))

                user_id = User.query.filter_by(username=user).first().id
                current_workout = WorkoutPlan.query.filter_by(user_id=user_id, name=workout)
                if not current_workout:
                    raise NotFound
                current_workout.name = request.json["name"]

                db.session.commit()
                return Response(url_for(current_workout), status=200)
            else:
                raise MethodNotAllowed
        except KeyError:
            db.session.rollback()
            raise BadRequest

    def get(self, workout: str, user: str=None) -> tuple[dict, int]:
        """
        Gets the requested workout
        ---
        description: "Allows GET from the following URIs: /api/users/{user}/workouts/{workout} and /api/workouts/{workout}"
        parameters:
        - $ref: '#/components/parameters/username'
        - $ref: '#/components/parameters/workout'         
        responses:
            '200':
                description: Workout plan returned successfully
                content:
                    application/json:
                        schema:
                            $ref: '#definitions/WorkoutItem'
                        example:
                        -   name: Light Exercise
                            creator: Noob
        """
 
        if user:
            user_id = User.query.filter_by(username=user).first().id
            query_result = WorkoutPlan.query.filter_by(name=workout, user_id=user_id).first()
        else:
            query_result = WorkoutPlan.query.filter_by(name=workout).first()
            if not query_result:
                raise NotFound
            user_id = query_result.user_id
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
        ---
        description: "Obviously should require the user to be authenticated, but auth is not implemented yet. Allows DELETE of the following URIs: /api/users/{user}/workouts/{workout} and /api/workouts/{workout}"
        parameters:
        - $ref: '#/components/parameters/user' 
        - $ref: '#/components/parameters/workout'         
        responses:
            '200':
                description: Workout plan deleted successfully
        """
        if workout:
            if user:
                user_id = User.query.filter_by(username=user).first().id
                query_result = WorkoutPlan.query.filter_by(name=workout, user_id=user_id).first()          
            else:
                query_result = WorkoutPlan.query.filter_by(name=workout).first()
            if not query_result:
                raise NotFound
                return

            db.session.delete(query_result)
            db.session.commit()
            return Response(status=200)
        else:
            raise MethodNotAllowed
