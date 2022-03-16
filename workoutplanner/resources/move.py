import json
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, MethodNotAllowed
from workoutplanner.models import *
from workoutplanner import db

class MoveCollection(Resource):
    """
    Workout move resource
    Contains methods for adding a new move or retrieving the whole collection

    Available at the following URI:s
    /api/users/{user}/moves, GET, POST
    /api/moves, GET
    """

    def post(self, user: str=None) -> Response:
        try:
            if request.json == None:
                raise UnsupportedMediaType
            #  Check if user is present in the path
            if user:
                try:
                    validate(request.json, Move.json_schema())
                except ValidationError as e:
                    raise BadRequest(description=str(e))

                name  = request.json["name"]
                user_id = User.query.filter_by(username=user).first().id
                description = request.json["description"]
                #  Create a Move object
                move = Move(name=name, user_id=user_id, description=description)
            #  Don't allow posting to the general moves URI
            else:
                raise MethodNotAllowed
            #  Add the move in to the database and commit all the changes
            db.session.add(move)
            db.session.commit()
            return Response(url_for(move), status=200)
        except KeyError:
            db.session.rollback()
            raise BadRequest
        except IntegrityError:
            db.session.rollback()
            raise Conflict("Move already exists")

    def get(self, user: str=None) -> tuple[list, int]:
        """
        Queries all the moves or moves created by a user

        Allows GET from the following URIs:
        /api/users/{user}/moves
        /api/moves
        """
        moves = []
        #  Check if user was present in the URI. 
        #  If so, query only the moves by that user.
        #  Else query all moves in the database.
        if user:
            user_id = User.query.filter_by(username=user).first().id
            query = Move.query.filter_by(user_id=user_id).all()
        else:
            query = Move.query.all()
        for move in query:
            moves.append(
                {
                    "name": move.name,
                    "creator": User.query.get(move.user_id).username,
                    "description": move.description
                }
            )
        return moves, 200

class MoveItem(Resource):
    """
    Workout move resource
    Contains PUT, GET and DELETE methods

    Covers the following paths:
        /api/users/{user}/moves/{move}, GET, PUT, DELETE
    """

    def put(self, user: str=None, move: str=None) -> Response:
        try:
            #  Check if PUTting to a specific users move.
            #  Else don't allow PUTting.
            if user and move:
                if request.json == None:
                    raise UnsupportedMediaType

                try:
                    validate(request.json, Move.json_schema())
                except ValidationError as e:
                    raise BadRequest(description=str(e))

                #  Query the creator id for the move
                creator_id = User.query.filter_by(username=user).first().id
                #  Query the requested move
                move = Move.query.filter_by(name=move, user_id=creator_id)
                #  Change it's attributes
                move.name  = request.json["name"]
                move.description = request.json["description"]

                db.session.commit()
                return Response(url_for(move), status=200)
            else:
                raise MethodNotAllowed
        except KeyError:
            db.session.rollback()
            raise BadRequest
        except IntegrityError:
            db.session.rollback()
            raise Conflict("Move already exists")

    def get(self, user: str=None, move: str=None) -> tuple[dict, int]:
        """
        Gets the specific move from the general move endpoint or the user specific endpoint
        Allows GET from the following URIs:
            /api/users/{user}/moves/{move}
        """
        if user and move:
            #  Get user id based on the user given by the URI
            user_id = User.query.filter_by(username=user).first().id
            #  Filter the move based on the previous user id and the moves name
            query = Move.query.filter_by(name=move, user_id=user_id).first()
        else:
            raise MethodNotAllowed
        result = {
                    "name": query.name,
                    "creator": User.query.get(query.user_id).username,
                    "description": query.description
                }
        return result, 200

    def delete(self, user, move):
        """
        Allows deletion of a users workout
        Obviously requires the user to be authenticated, but auth is not implemented yet
        """
        if user and move:
            #  Get user id based on the user given by the URI
            user_id = User.query.filter_by(username=user).id
            query_result = Move.query.filter_by(name=move, user_id=user_id).first()
            #  Check if the query produced a result, if not then raise a NotFound exception
            if not query_result:
                raise NotFound
            else:
                db.session.delete(query_result)
                db.session.commit()
        else:
            raise MethodNotAllowed
