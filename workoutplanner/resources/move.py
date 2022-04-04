import json
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, MethodNotAllowed
from workoutplanner.models import *
from workoutplanner import db
from workoutplanner.utils import MasonBuilder
from werkzeug.routing import BaseConverter
from workoutplanner.links import *

class MoveConverter(BaseConverter):
    def to_python(self, user):
        db_user = User.query.filter_by(username=user).first()
        if db_user is None:
            raise NotFound
        return db_user
    def to_url(self, db_user):
        return db_user.username

class MoveCollection(Resource):
    """
    Workout move resource
    Contains methods for adding a new move or retrieving the whole collection

    Available at the following URI:s
    /api/users/{user}/moves, GET, POST
    /api/moves, GET
    """

    def post(self, user: str=None) -> Response:
        """
        POST a new workout move.
        ---
        description: "Allows POST to the following URI:  /api/users/{user}/moves"
        parameters:
        - $ref: '#/components/parameters/user'
        - $ref: '#/components/parameters/moveitem'       
        responses:
            '201':
                description: Move posted successfully
                headers:
                    Location: 
                        description: URI of the new move
                        schema:
                            type: string
                            example: /api/users/Noob/moves/Plank
        """
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
            #return Response(url_for(move), status=200)
            return Response(status=201, headers={
                "Location": url_for("api.moveitem", user=user, move=name)
            })
            
        except KeyError:
            db.session.rollback()
            raise BadRequest
        except IntegrityError:
            db.session.rollback()
            raise Conflict("Move already exists")

    def get(self, user: str=None) -> tuple[list, int]:
        """
        Queries all the moves or moves created by a user
        ---
        description: "Allows GET from the following URIs: /api/users/{user}/moves, /api/moves"
        parameters:
        - $ref: '#/components/parameters/username'
        - $ref: '#/components/parameters/move'
        responses:
            '200':
                description: Moves returned successfully  
                content:
                    application/json:
                        schema:
                            $ref: '#definitions/MoveItem'
                        example: 
                        -   name: Plank
                            creator: Noob
                            description: Use your muscles to keep your body in a straight horizontal line
                        -   name: Opening Fridge
                            creator: ProAthlete35
                            description: Walk to the nearest fridge and open it
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
        """
        Edit a workout move.
        ---
        description: "Allows PUT to the following URI:  /api/users/{user}/moves/{move}"
        parameters:
        - $ref: '#/components/parameters/user'    
        - $ref: '#/components/parameters/move'         
        - $ref: '#/components/parameters/moveitem' 
        responses:
            '201':
                description: Move edited successfully
                Location: 
                    description: URI of the move
                    schema:
                        type: string
                        example: /api/users/Noob/moves/Plank
        """
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
                return Response(status=201, headers={
                    "Location": url_for("api.moveitem", user=user, move=name)
                })
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
        ---
        description: "Allows GET from the following URI: /api/users/{user}/moves/{move}"
        parameters:
        - $ref: '#/components/parameters/user'
        - $ref: '#/components/parameters/move'
        responses:
            '200':
                description: Move returned successfully
                content:
                    application/json:
                        schema:
                            $ref: '#definitions/MoveItem'
                        example: 
                        -   name: Plank
                            creator: Noob
                            description: Use your muscles to keep your body in a straight horizontal line
        """
        if user and move:
            #  Get user id based on the user given by the URI
            user_id = User.query.filter_by(username=user).first().id
            #  Filter the move based on the previous user id and the moves name
            query = Move.query.filter_by(name=move, user_id=user_id).first()
        else:
            raise MethodNotAllowed
     
        body = MoveBuilder(query.serialize())
        body.add_namespace("workoutplanner", LINK_RELATIONS_URL)
        body.add_control("self", href=request.path)
        body.add_control("profile", href=MOVE_PROFILE_URL)
        body.add_control("collection", url_for("api.movecollection"))
        body.add_control("up", query.get_collection_url())
        body.add_control_edit_move(query)
        body.add_control_delete_move(query)
        return Response(json.dumps(body), 200, mimetype=MASON)        

    def delete(self, user, move):
        """
        Allows deletion of a users workout move
        ---
        description: Obviously requires the user to be authenticated, but auth is not implemented yet
        parameters:
        - $ref: '#/components/parameters/user'
        - $ref: '#/components/parameters/move'   
        responses:
            '200':
                description: Move deleted successfully
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
                return Response(status=200)
        else:
            raise MethodNotAllowed
          

class MoveBuilder(MasonBuilder):

    def add_control_delete_move(self, obj):
        self.add_control_delete(
            ctrl_name="workoutplanner:delete",
            title="Delete this move",
            href=obj.get_url()
        )
    
    def add_control_edit_move(self, obj):
        self.add_control_put(
            ctrl_name="edit",
            title="Edit this move",
            href=obj.get_url(),
            schema=Move.json_schema()
        )
