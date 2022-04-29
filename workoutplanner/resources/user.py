import json
from flask import Response, request, url_for
from flask_restful import Resource, Api
from jsonschema import validate, ValidationError
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, MethodNotAllowed, InternalServerError
from typing import Union
from workoutplanner.models import *
from workoutplanner import db
from workoutplanner.utils import MasonBuilder
from werkzeug.routing import BaseConverter
from workoutplanner.links import *
from flasgger import swag_from

class UserConverter(BaseConverter):
    def to_python(self, user):
        db_user = User.query.filter_by(username=user).first()
        if db_user is None:
            raise NotFound
        return db_user
    def to_url(self, db_user):
        return db_user.username

class UserCollection(Resource):
    """
    User resource
    Contains methods for  adding users and retrieving the whole list of users.
    """

    def post(self) -> Union[Response, tuple[str, int]]:
        """
        Add a new user
        ---
        description: Create a new user
        parameters:
        - $ref: '#/components/parameters/useritem'
        responses:
            '201':
                description: User added successfully
                headers:
                    Location: 
                        description: URI of the new user
                        schema:
                            type: string
                            example: /api/users/Noob

            '400':
                description: Bad request
            '409':
                description: Conflict (already exists)
            '415':
                description: Unsupported media type
        """
        if not request.content_type == "application/json":
            raise UnsupportedMediaType
        try:
            validate(request.json, User.json_schema())
        except ValidationError as err:
            raise BadRequest(description=str(err))

        username  = request.json["username"]
        user = User(username=username)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise Conflict

        return Response(status=201, headers={
            "Location": user.get_url()#url_for("api.useritem", user=user)
        })

    @swag_from("/workoutplanner/doc/users/get_collection.yml")
    def get(self) -> tuple[list, int]:
        """
        Get all users
        ---
        description: Get all the users in the API
        responses:
            '200':
                description: Users returned successfully
                content:
                    application/json:
                        schema:
                            $ref: '#definitions/UserItem'
                        example: 
                        -   username: Noob
                        -   username: ProAthlete35
        """

        body = UserCollectionBuilder(items=[])
        body.add_namespace("workoutplanner", LINK_RELATIONS_URL)
        body.add_control("self", href=request.path)
        body.add_control("profile", href=USER_COLLECTION_PROFILE_URL)
        body.add_control("up", href="/api/", title="Up")
        body.add_control_add_user()

        for user in User.query.all():
            item = UserBuilder(user.serialize())
            item.add_control("self", user.get_url())
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)


class UserItem(Resource):
    """
    User resource
    Contains methods for  adding users and retrieving the whole list of users.
    """

    def put(self, user) -> Union[Response, tuple[str, int]]:
        """
        Edit an user
        ---
        description: Add/change a user. Can be used to change a username to another
        parameters:
        - $ref: '#/components/parameters/user'
        - $ref: '#/components/parameters/useritem'
        responses:
            '200':
                description: User edited successfully
                headers:
                    Location: 
                        description: URI of the user
                        schema:
                            type: string
                            example: /api/users/Noob
            '400':
                description: Bad request
            '404':
                description: Not found
            '415':
                description: Unsupported media type
        """
        if not request.content_type == "application/json":
            raise UnsupportedMediaType

        try:
            validate(request.json, User.json_schema())
        except ValidationError as err:
            raise BadRequest(description=str(err))

        current_user = User.query.filter_by(username=user).first()
        if current_user is None:
            raise NotFound
        current_user.username  = request.json["username"]

        db.session.commit()
        return Response(status=200, headers={
            "Location": current_user.get_url()
        })

    @swag_from("/workoutplanner/doc/users/get_item.yml")
    def get(self, user) -> tuple[str, int]:
        """
        Get the user
        ---
        description: Get the username of the user
        parameters:
        - $ref: '#/components/parameters/user'   
        responses:
            '200':
                description: Username returned successfully
                content:
                    application/json:
                        schema:
                            $ref: '#definitions/UserItem'
            '404':
                description: Not found
        """
        user_obj = User.query.filter_by(username=user).first()

        if not user_obj:
            raise NotFound
        result = user_obj.username

        body = UserBuilder(user_obj.serialize())
        body.add_namespace("workoutplanner", LINK_RELATIONS_URL)
        body.add_control("self", href=request.path)
        body.add_control("profile", href=USER_PROFILE_URL)
        body.add_control("up", href=url_for("api.usercollection"), title="Up")# href=api.url_for(UserCollection))
        body.add_control_get_all_moves(user_obj)
        body.add_control_get_all_workouts(user_obj)
        body.add_control_add_move(user_obj)
        body.add_control_add_workout(user_obj)
        body.add_control_edit_user(user_obj)
        return Response(json.dumps(body), 200, mimetype=MASON)

class UserCollectionBuilder(MasonBuilder):

    def add_control_add_user(self):
        '''POST a new user'''
        self.add_control_post(
            ctrl_name="workoutplanner:add-user",
            title="Add an user",
            href="/api/users/",
            schema=User.json_schema()
        )



class UserBuilder(MasonBuilder):

    def add_control_get_all_moves(self, user):
        '''GET all the moves of the user'''
        self.add_control(
            ctrl_name="workoutplanner:moves-by",
            href=user.get_url() + "moves/",
            method="GET",
            title="Get all moves of this user"
        )

    def add_control_get_all_workouts(self, user):
        '''GET all the workouts of the user'''
        self.add_control(
            ctrl_name="workoutplanner:workouts-by",
            href=user.get_url() + "workouts/",
            method="GET",
            title="Get all workouts of this user"
        )

    def add_control_delete_user(self, user):
        '''DELETE this user'''
        self.add_control_delete(
            ctrl_name="workoutplanner:delete",
            title="Delete this user",
            href=user.get_url()
        )

    def add_control_add_move(self, user):
        '''POST a new move for this user'''
        self.add_control_post(
            ctrl_name="workoutplanner:add-move",
            title="Add a move for this user",
            href=user.get_url() + "moves/",
            schema=Move.json_schema()
        )

    def add_control_add_workout(self, user):
        '''POST a new workout for this user'''
        self.add_control_post(
            ctrl_name="workoutplanner:add-workout",
            title="Add a workout for this user",
            href=user.get_url() + "workouts/",
            schema=WorkoutPlan.json_schema()
        )

    def add_control_edit_user(self, user):
        '''PUT an user'''
        self.add_control_put(
            ctrl_name="edit",
            title="Edit this user",
            href=user.get_url(),
            schema=User.json_schema()
        )
