import json
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, MethodNotAllowed, InternalServerError
from typing import Union
from workoutplanner.models import *
from workoutplanner import db

class MoveCollection(Resource):
    """
    Workout move resource
    Contains methods for adding a new move or retrieving the whole collection

    Available at the following URI:s
    /api/users/{user}/moves
    /api/moves
    """

    def post(self, user=None, workout=None) -> Union[Response, tuple[str, int]]:
        try:
            if request.json == None:
                raise UnsupportedMediaType
            if user and not workout:
                #  If the move was posted to the /api/moves URI it will be added as a move item
                try:
                    validate(request.json, Move.json_schema())
                except ValidationError as e:
                    raise BadRequest(description=str(e))
                name  = request.json["name"]
                user_id = User.query.filter_by(username=user).id
                description = request.json["description"]

                if name is None or user_id is None or description is None:
                    return "Incomplete request", 400

                move = Move(name=name, user_id=user_id, description=description)
            else:
                raise MethodNotAllowed
            #  Adds the move in to the database and commits all the changes
            db.session.add(move)
            db.session.commit()
            return Response(url_for(move), status=200)
        except KeyError:
            return "Incomplete request", 400
        except IntegrityError:
            db.session.rollback()
            raise Conflict(
                409,
                "Move already exists"
            )

    def get(self, user=None, workout=None) -> tuple[list, int]:
        
        moves = []
        #  If the query was to the general move collection, only return the base info of a move
        query = Move.query.all()
        for move in query:
            moves.append(
                {
                    "name": move.name,
                    "creator": User.query.get(move.creator_id).username,
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
                validate(request.json, Move.json_schema())
            except ValidationError as e:
                raise BadRequest(description=str(e))

            name  = request.json["name"]
            creator = User.query.filter_by(username=request.json["username"])
            description = request.json["description"]

            if name is None or creator is None or description is None:
                return "Incomplete request", 400

            move = Move(name=name, creator=creator, description=description)

            db.session.add(move)
            db.session.commit()
            return Response(url_for(move), status=200)
        except KeyError:
            return "Incomplete request", 400
        except IntegrityError:
            db.session.rollback()
            raise Conflict(
                409,
                "Move already exists"
            )

    def get(self, name: str="") -> tuple[list, int]:
        
        moves = []
        if name:
            query = Move.query.filter_by(name=name).all()
        else:
            query = Move.query.all()
        for move in query:
            moves.append(
                {
                    "name": move.name,
                    "creator": User.query.get(move.creator_id).username,
                    "description": move.description
                }
            )
        return moves, 200

    def delete(self, user, move):
        """
        Allows deletion of a users workout
        Obviously requires the user to be authenticated, but auth is not implemented yet
        """
        if user and move:
            user_id = User.query.get(user).id
            query_result = Move.query.filter_by(name=move, user_id=user_id).first()
            if not query_result:
                raise NotFound
            else:
                db.session.delete(query_result)
                db.session.commit()
        else:
            raise MethodNotAllowed

