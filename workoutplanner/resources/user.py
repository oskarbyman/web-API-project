import json
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, MethodNotAllowed, InternalServerError
from typing import Union
from workoutplanner.models import *
from workoutplanner import db

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

            '409':
                description: User already exists
        """
        if request.json == None:
            raise UnsupportedMediaType
        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        username  = request.json["username"]
        user = User(username=username)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise Conflict(
                "User already exists",
                409
            )
            return Response("User already exists", 409)

        return Response(status=201, headers={
            "Location": url_for("api.useritem", user=user)
        })
        
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
        
        users = []
        for user in User.query.all():
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
                content:
                    string:
                        example: 
                            /api/users/Noob
        """
        if request.json == None:
            raise UnsupportedMediaType

        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        
        current_user = User.query.filter_by(username=user)
        if not current_user:
            raise NotFound
        current_user.username  = request.json["username"]

        db.session.commit()
        return Response(url_for(user), status=200)

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
        """

        query_result = User.query.filter_by(username=user).first()

        if not query_result:
            raise NotFound
        result = query_result.username
        return result, 200

    def delete(self, user: str) -> Response:
        """
        Delete user
        ---
        description: Delete the user
        parameters:
        - $ref: '#/components/parameters/user'   
        responses:
            '200':
                description: User deleted successfully
        """
        query_result = User.query.filter_by(username=user).first()
        if not query_result:
            raise NotFound
        else:
            db.session.delete(query_result)
            db.session.commit()
            return Response(status=200)
