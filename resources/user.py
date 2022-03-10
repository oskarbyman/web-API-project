import json
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, MethodNotAllowed, InternalServerError
from typing import Union
from models import *

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

            user = User(username=username)
            db.session.add(user)
            db.session.commit()
            return Response(url_for(user), status=200)
        except IntegrityError:
            db.session.rollback()
            raise Conflict(
                409,
                "User already exists"
            )

    def get(self) -> tuple[list, int]:

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

    def get(self, user) -> tuple[list, int]:

        query_result = User.query.filter_by(username=user).first()

        if not query_result:
            raise NotFound

        return query_result, 200