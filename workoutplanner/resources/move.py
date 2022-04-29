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
from flasgger import swag_from

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
            '400':
                description: Bad request
            '404':
                description: Not found
            '405':
                description: Method not allowed
            '409':
                description: Conflict (already exists)
            '415':
                description: Unsupported media type
        """
        try:
            if not request.content_type == "application/json":
                raise UnsupportedMediaType
            #  Check if user is present in the path
            if user:
                try:
                    validate(request.json, Move.json_schema())
                except ValidationError as err:
                    raise BadRequest(description=str(err))

                name  = request.json["name"]
                user_obj = User.query.filter_by(username=user).first()
                if user_obj is None:
                    raise NotFound
                user_id = user_obj.id
                    
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
                "Location": move.get_url()#url_for("api.moveitem", user=user, move=name)
            })

        except KeyError:
            db.session.rollback()
            raise BadRequest
        except IntegrityError:
            db.session.rollback()
            raise Conflict("Move already exists")

    @swag_from("/workoutplanner/doc/moves/get_collection.yml")
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
        #  Check if user was present in the URI.
        #  If so, query only the moves by that user.
        #  Else query all moves in the database.
        if user:
            user_obj = User.query.filter_by(username=user).first()
            user_id = user_obj.id
            query = Move.query.filter_by(user_id=user_id).all()
        else:
            query = Move.query.all()

        body = MoveCollectionBuilder(items=[])
        body.add_namespace("workoutplanner", LINK_RELATIONS_URL)
        body.add_control("self", href=request.path)
        body.add_control("profile", href=MOVE_COLLECTION_PROFILE_URL)
        
        if user:
            body.add_control("up", href=user_obj.get_url(), title="Up")
            body.add_control_add_move(user_obj)
        else:
            body.add_control("up", href=url_for("api_entry"), title="Up")
        
        for move in query:
            item = MoveBuilder(move.serialize(short_form=True))
            item.add_control("self", move.get_url())
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

class MoveItem(Resource):
    """
    Workout move resource
    Contains PUT and GET methods

    Covers the following paths:
        /api/users/{user}/moves/{move}, GET, PUT
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
            '200':
                description: Move edited successfully
                Location: 
                    description: URI of the move
                    schema:
                        type: string
                        example: /api/users/Noob/moves/Plank
            '400':
                description: Bad request
            '404':
                description: Not found
            '405':
                description: Method not allowed
            '409':
                description: Conflict (already exists)
            '415':
                description: Unsupported media type
        """
        try:
            #  Check if PUTting to a specific users move.
            #  Else don't allow PUTting.
            if user and move:
                if not request.content_type == "application/json":
                    raise UnsupportedMediaType

                try:
                    validate(request.json, Move.json_schema())
                except ValidationError as err:
                    raise BadRequest(description=str(err))

                #  Query the creator id for the move
                creator_obj = User.query.filter_by(username=user).first()
                if creator_obj is None:
                    raise NotFound
                creator_id = creator_obj.id
                #  Query the requested move
                move = Move.query.filter_by(name=move, user_id=creator_id).first()
                #  Change it's attributes
                move.name  = request.json["name"]
                move.description = request.json["description"]

                db.session.commit()
                return Response(status=200, headers={
                    "Location": move.get_url()
                })
            else:
                raise MethodNotAllowed
        except KeyError:
            db.session.rollback()
            raise BadRequest
        except IntegrityError:
            db.session.rollback()
            raise Conflict("Move already exists")

    @swag_from("/workoutplanner/doc/moves/get_item.yml")
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
            '404':
                description: Not found
            '405':
                description: Method not allowed
        """
        if user and move:
            #  Get user id based on the user given by the URI
            user_obj = User.query.filter_by(username=user).first()
            if not user_obj:
                raise NotFound
            user_id = user_obj.id
            #  Filter the move based on the previous user id and the moves name
            query = Move.query.filter_by(name=move, user_id=user_id).first()
        else:
            raise MethodNotAllowed

        body = MoveBuilder(query.serialize())
        body.add_namespace("workoutplanner", LINK_RELATIONS_URL)
        body.add_control("self", href=request.path)
        body.add_control("profile", href=MOVE_PROFILE_URL)
        body.add_control("collection", url_for("api.movecollection"), title="All moves")
        body.add_control("up", query.get_collection_url(), title="Up")
        body.add_control_edit_move(query)
        #body.add_control_delete_move(query)
        return Response(json.dumps(body), 200, mimetype=MASON)

class MoveCollectionBuilder(MasonBuilder):

    def add_control_add_move(self, user):
        self.add_control_post(
            ctrl_name="workoutplanner:add-move",
            title="Add a move",
            href=user.get_url() + "moves/",
            schema=Move.json_schema()
        )

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
