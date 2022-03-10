import json
from unicodedata import name
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, MethodNotAllowed, InternalServerError
from typing import Union
from models import *
from workoutplanner import db

class MoveListItemCollection(Resource):
    """
    MoveListItem collection is a collection of wrapped move items in a workout
    Wrapping a move item adds repetitions and a position to the move.

    
    This resource covers the following URI:s,
    /api/workouts/{workout}/moves, GET
    /api/users/{user}/workouts/{workout}/moves, GET, POST
    """
    def post(self, user=None, workout=None):
        try:
            if request.json == None:
                raise UnsupportedMediaType
            #  If the target URI is a move in a users workout uses the move list item wrapper model
            if workout and user:
                try:
                    validate(request.json, MoveListItem.json_schema())
                except ValidationError as e:
                    raise BadRequest(description=str(e))
                #  Get link ids to link the correct move and plan to the wrapper
                plan_id  = WorkoutPlan.query.filter_by(user=user, name=workout).first().id
                creator_id = User.query.filter_by(username=user).first().id
                move_id = Move.query.filter_by(name=request.json["move_name"], user_id=creator_id).first().id
                #  Checks if the optional repetitions is present in the request
                if "repetitions" in request.json:
                    repetitions = request.json["repetitions"]
                else:
                    repetitions = None
                #  Checks if the optional position is present in the request
                if "position" in request.json:
                    #  Get all current moves in workout plan
                    current_moves = MoveListItem.query.filter(plan_id == plan_id).all()
                    #  Figure out the last position
                    last_position = max([int(c_move.position) for c_move in current_moves].sort())
                    #  If the requested position is larger than the currently last position
                    #  Set it to the length of the movelist array, else set the requested value
                    if request.json["position"] > last_position:
                        position = len(MoveListItem.query.filter_by(plan_id=plan_id).all())
                    else:
                        position = request.json["position"]
                    #  Queries current positions of the moves in the same plan 
                    #  with a position equal or larger than the on in the request.
                    #  Returns an empty list if the position does not exist
                    #  Increments the current positions with one to enable inserting the new position
                    current_moves = MoveListItem.query.filter(plan_id == plan_id, position >= position).all()
                    for current_move in current_moves:
                        current_move.position += 1
                else:
                    #  If the position was not present in the request set it to the last position in the plan.
                    #  The next free index will be the length of the result array
                    current_position = len(MoveListItem.query.filter_by(plan_id=plan_id).all())
                    position = current_position
                if not move_id or not plan_id or not creator_id:
                    raise NotFound
                move = MoveListItem(position=position, plan_id=plan_id, move_id=move_id, repetitions=repetitions)
            else:
                raise MethodNotAllowed
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

    def get(self, user=None, workout=None):
        """
        
        """
        moves = []
        if user and workout:
        #  If the query is to a users workout, filter the results based on it
        #  Queries the needed information from the wrapped move based on the move_id in the move list item
            plan_id  = WorkoutPlan.query.filter_by(user=user, name=workout).first().id
            if not plan_id:
                raise NotFound(f"The user {user} or their workout {workout} does not exist")
            query = MoveListItem.query.filter_by(plan_id=plan_id).all()
            for move in query:
                moves.append(
                    {
                        "name": Move.query.filter_by(id=move.move_id).first().name,
                        "creator": User.query.get(
                                        Move.query.filter_by(id=move.move_id).first().creator_id
                                    ).username,
                        "description": Move.query.filter_by(id=move.move_id).first().description,
                        "repetitions": move.repetitions,
                        "position": move.position
                    }
                )
        elif workout and not user:
            plan_id  = WorkoutPlan.query.filter_by(name=workout).first().id
            if not plan_id:
                raise NotFound(f"The  workout {workout} does not exist")
            query = MoveListItem.query.filter_by(plan_id=plan_id).all()
            for move in query:
                moves.append(
                    {
                        "name": Move.query.filter_by(id=move.move_id).first().name,
                        "creator": User.query.get(
                                        Move.query.filter_by(id=move.move_id).first().creator_id
                                    ).username,
                        "description": Move.query.filter_by(id=move.move_id).first().description,
                        "repetitions": move.repetitions,
                        "position": move.position
                    }
                )
        return moves, 200


class MoveListItemItem(Resource):
    """
    Move list item is a single wrapped move item in a workout
    A wrapped move is a move with repetitions and a position added

    Covers the following URI:s,
    /api/workouts/{workout}/moves/{move_list_item}, GET
    /api/users/{user}/workouts/{workout}/moves/{move_list_item}, GET, PUT, DELETE
    """

    def put(self, user=None, workout=None, position=None):
        try:
            validate(request.json, MoveListItem.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        try:
            if request.json == None:
                raise UnsupportedMediaType
            #  If the target URI is a move in a users workout uses the move list item wrapper model
            if workout and user and position:
                #  Id:s
                user_id = User.query.filter_by(username=user).first().id
                plan_id = WorkoutPlan.query.filter_by(name=workout, user=user_id).first().id
                move_id = Move.query.filter_by(name=request.json["move_name"]).first().id
                if not user_id:
                    raise NotFound(f"No such user as {user} found")
                if not plan_id:
                    raise NotFound(f"No such workout as {workout} found")
                if not move_id:
                    move_name = request.json["move_name"]
                    raise NotFound(f"No such move as {move_name} found")
                #  Get the current Move list item object
                move_list_item = MoveListItem.query.filter_by(position=position, plan_id=plan_id).first()
                if not move_list_item:
                    raise NotFound(f"No move at position {position}")
                #  Change the 
                move_list_item.move_id = move_id
                if "position" in request.json:
                    #  Get all current moves in workout plan
                    current_moves = MoveListItem.query.filter(plan_id == plan_id).all()
                    #  Figure out the last position
                    last_position = max([int(c_move.position) for c_move in current_moves].sort())
                    #  If the requested position is larger than the currently last position
                    #  Set it to the length of the movelist array, else set the requested value
                    if request.json["position"] > last_position:
                        position = len(MoveListItem.query.filter_by(plan_id=plan_id).all())
                    else:
                        position = request.json["position"]
                    #  Queries current positions of the moves in the same plan 
                    #  with a position equal or larger than the on in the request.
                    #  Returns an empty list if the position does not exist
                    #  Increments the current positions with one to enable inserting the new position
                    current_moves = MoveListItem.query.filter(plan_id == plan_id, position >= position).all()
                    for current_move in current_moves:
                        current_move.position += 1
                else:
                    #  If the position was not present in the request set it to the last position in the plan.
                    #  The next free index will be the length of the result array
                    current_position = len(MoveListItem.query.filter_by(plan_id=plan_id).all())
                    position = current_position
            else:
                raise MethodNotAllowed
            db.session.commit()
            return Response(url_for(move_list_item), status=200)
        except KeyError as e:
            raise BadRequest(e)
        except IntegrityError:
            db.session.rollback()
            raise Conflict("Move already exists")

    def get(self, user, workout, position):
        pass

    def delete(self, user, workout, position):
        pass