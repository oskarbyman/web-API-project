from os import stat
from flask import Response, request
from flask_restful import Resource, url_for
from jsonschema import validate, ValidationError
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, MethodNotAllowed, InternalServerError
from typing import Union
from workoutplanner.models import *
from workoutplanner import db
from workoutplanner.utils import MasonBuilder
from werkzeug.routing import BaseConverter
from workoutplanner.links import *
from flasgger import swag_from

class WorkoutPlanConverter(BaseConverter):
    def to_python(self, user):
        db_user = User.query.filter_by(username=user).first()
        if db_user is None:
            raise NotFound
        return db_user
    def to_url(self, db_user):
        return db_user.username

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
            '201':
                description: URI of the new plan
                headers:
                    Location: 
                        description: URI of the new workout
                        schema:
                            type: string
                            example: /api/users/Noob/workouts/Light Excercise
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
                #return Response(url_for(plan), status=200)
                return Response(status=201, headers={
                    "Location": plan.get_url()#url_for("api.workoutplanitem", user=user, workout=name)
                })
        except KeyError:
            db.session.rollback()
            raise BadRequest
        except IntegrityError:
            db.session.rollback()
            raise Conflict(
                "Workout plan already exists",
                409
            )

    @swag_from("/workoutplanner/doc/workouts/get_collection.yml")
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
            user_obj = User.query.filter_by(username=user).first()
            user_id = user_obj.id
            query = WorkoutPlan.query.filter_by(user_id=user_id).all()
        else:
            query = WorkoutPlan.query.all()
        
        body = WorkoutPlanCollectionBuilder(items=[])
        body.add_namespace("workoutplanner", LINK_RELATIONS_URL)
        body.add_control("self", href=request.path)
        body.add_control("profile", href=WORKOUT_COLLECTION_PROFILE_URL)
        #body.add_control("collection", href=url_for("api.workoutplancollection"))
        if user:
            body.add_control("up", href=user_obj.get_url(), title="Up")
            body.add_control_add_workout(user_obj)
        else:
            body.add_control("up", href=url_for("api_entry"), title="Up")
        
        for workout in query:
            item = WorkoutPlanBuilder(workout.serialize(short_form=True))
            item.add_control("self", workout.get_url())
            body["items"].append(item)
        
        return Response(json.dumps(body), 200, mimetype=MASON)

class WorkoutPlanItem(Resource):
    """
    Workout plan item resource
    Implements methods for handling a single workout

    Covers the following URIs:
    /api/users/{user}/workouts/{workout}, GET, PUT, DELETE
    """

    def put(self, user: str=None, workout: str=None) -> Union[Response, tuple[str, int]]:
        """
        Edit a workout.
        ---
        description: "Allows PUT to the following URI:  /api/users/{user}/workouts/{workout}"
        parameters:
        - $ref: '#/components/parameters/user' 
        - $ref: '#/components/parameters/workout'
        - $ref: '#/components/parameters/workoutitem'   
        responses:
            '201':
                description: Workout replaced successfully
                headers:
                    Location: 
                        description: URI of the new workout
                        schema:
                            type: string
                            example: /api/users/Noob/workouts/Light Excercise
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
                return Response(status=201, headers={
                    "Location": current_workout.get_url()#url_for("api.workoutplanitem", user=user, workout=name)
                })
            else:
                raise MethodNotAllowed
        except KeyError:
            db.session.rollback()
            raise BadRequest
    
    
    @swag_from("/workoutplanner/doc/workouts/get_item.yml")
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
            user_obj = User.query.filter_by(username=user).first()
            user_id = user_obj.id
            query_result = WorkoutPlan.query.filter_by(name=workout, user_id=user_id).first()
        else:
            query_result = WorkoutPlan.query.filter_by(name=workout).first()
            if not query_result:
                raise NotFound
            user_id = query_result.user_id
        if not query_result:
            raise NotFound
        
        body = WorkoutPlanBuilder(query_result.serialize())
        body.add_namespace("workoutplanner", LINK_RELATIONS_URL)
        body.add_control("self", href=request.path)
        body.add_control("profile", href=WORKOUT_PROFILE_URL)
        body.add_control("collection", url_for("api.workoutplancollection"), title="All workouts")
        body.add_control("up", query_result.get_collection_url(), title="Up")
        body.add_control_get_all_move_list_items(query_result)
        body.add_control_add_move_list_item(query_result)
        body.add_control_edit_workout_plan(query_result)
        body.add_control_delete_workout_plan(query_result)
        return Response(json.dumps(body), 200, mimetype=MASON)

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


class WorkoutPlanCollectionBuilder(MasonBuilder):

    def add_control_add_workout(self, user):
        self.add_control_post(
            ctrl_name="workoutplanner:add-workout",
            title="Add a workout",
            href=user.get_url() + "workouts/",
            schema=WorkoutPlan.json_schema()
        )


class WorkoutPlanBuilder(MasonBuilder):

    def add_control_get_all_move_list_items(self, obj):
        self.add_control(
            ctrl_name="workoutplanner:movelistitems-by",
            href=obj.get_url() + "moves/",
            method="GET",
            title="Get all movelist items in the workout"
        )

    def add_control_delete_workout_plan(self, obj):
        self.add_control_delete(
            ctrl_name="workoutplanner:delete",
            title="Delete this workout",
            href=obj.get_url()
        )
    
    def add_control_add_move_list_item(self, obj):
        self.add_control_post(
            ctrl_name="workoutplanner:add-movelistitem",
            title="Add a movelist item to this workout",
            href=obj.get_url() + "moves/",
            schema=MoveListItem.json_schema()
        )
    
    def add_control_edit_workout_plan(self, obj):
        self.add_control_put(
            ctrl_name="edit",
            title="Edit this workout",
            href=obj.get_url(),
            schema=WorkoutPlan.json_schema()
        )
