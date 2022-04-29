from flask import Response, request
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, MethodNotAllowed
from sqlalchemy.exc import IntegrityError
from workoutplanner.models import *
from workoutplanner import db
from workoutplanner.utils import MasonBuilder
from werkzeug.routing import BaseConverter
from workoutplanner.links import *
from flasgger import swag_from

class MoveListItemConverter(BaseConverter):
    def to_python(self, user):
        db_user = User.query.filter_by(username=user).first()
        if db_user is None:
            raise NotFound
        return db_user
    def to_url(self, db_user):
        return db_user.username

class MoveListItemCollection(Resource):
    """
    MoveListItem collection is a collection of wrapped move items in a workout
    Wrapping a move item adds repetitions and a position to the move.

    
    This resource covers the following URI:s,
    /api/users/{user}/workouts/{workout}/moves, GET, POST
    """
    
    def post(self, user: str=None, workout: str=None) -> Response:
        """
        POST a new movelist.
        ---
        description: "Allows POST to the following URI(s): /api/users/{user}/workouts/{workout}/moves"
        parameters:
        - $ref: '#/components/parameters/user'   
        - $ref: '#/components/parameters/workout'  
        - $ref: '#/components/parameters/movelistitem'   
        responses:
            '201':
                description: MoveList item posted successfully
                headers:
                    Location: 
                        description: URI of the new movelist
                        schema:
                            type: string
                            example: /api/users/ProAthlete35/workouts/Light Exercise/moves
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
            #  If the target URI is a move in a users workout uses the move list item wrapper model
            if workout and user:
                try:
                    validate(request.json, MoveListItem.json_schema())
                except ValidationError as err:
                    raise BadRequest(description=str(err))
                #  Get link ids to link the correct move and plan to the wrapper
                creator = User.query.filter_by(username=user).first()
                if not creator:
                    raise NotFound(f"No such user as {user} found")
                creator_id = creator.id              
                
                plan = WorkoutPlan.query.filter_by(user_id=creator_id, name=workout).first()  
                if not plan:
                    raise NotFound(f"No such workout as {workout} found")
                plan_id = plan.id    
                
                move_creator = User.query.filter_by(username=request.json["move_creator"]).first()
                if not move_creator:
                    raise NotFound(f"No such user as {move_creator} found")
                   
                move = Move.query.filter_by(name=request.json["move_name"], user_id=move_creator.id).first()
                if not move:
                    move_name = request.json["move_name"]
                    raise NotFound(f"No such move as {move_name} found")
                move_id = move.id

                
                
                #  Checks if the optional repetitions is present in the request
                if "repetitions" in request.json:
                    repetitions = request.json["repetitions"]
                else:
                    repetitions = None
                #  Checks if the optional position is present in the request
                if "position" in request.json:
                
                    position = request.json["position"]
                    #  Get all current moves in workout plan
                    current_moves = MoveListItem.query.filter((MoveListItem.plan_id == plan_id) & (MoveListItem.position >= position)).all()
                    #  Figure out the last position
                    last_position = 0
                    if current_moves:
                        last_position = max([int(c_move.position) for c_move in current_moves])
                    #  If the requested position is larger than the currently last position
                    #  Set it to the length of the movelist array, else set the requested value
                    if position > last_position:
                        position = len(MoveListItem.query.filter_by(plan_id=plan_id).all())
                    #  Queries current positions of the moves in the same plan 
                    #  with a position equal or larger than the on in the request.
                    #  Returns an empty list if the position does not exist
                    #  Increments the current positions with one to enable inserting the new position
                    
                    for current_move in current_moves:
                        current_move.position += 1
                else:
                    #  If the position was not present in the request set it to the last position in the plan.
                    #  The next free index will be the length of the result array
                    position = len(MoveListItem.query.filter_by(plan_id=plan_id).all())
                    
                if not move_id or not plan_id or not creator_id:
                    raise NotFound
                move = MoveListItem(position=position, plan_id=plan_id, move_id=move_id, repetitions=repetitions)
            else:
                raise MethodNotAllowed
            db.session.add(move)
            db.session.commit()
            #return Response(url_for(move), status=200)
            return Response(status=201, headers={
                "Location": move.get_url()#url_for("api.movelistitemitem", user=user, workout=workout, position=position)
            })
            
        except KeyError:
            db.session.rollback()
            raise BadRequest
        except IntegrityError:
            db.session.rollback()
            raise Conflict

    @swag_from("/workoutplanner/doc/movelistitems/get_collection.yml")
    def get(self, workout: str, user: str=None) -> tuple[list, int]:
        """ 
        Get the list of workout move list items.
        ---
        description: "Allows GET from the following URIs: /api/users/{user}/workouts/{workout}/moves"
        parameters:
        - $ref: '#/components/parameters/user'     
        - $ref: '#/components/parameters/workout' 
        responses:
            '200':
                description: List of movelist items returned successfully
                content:
                    application/json:
                        schema:
                            $ref: '#/definitions/MoveListItem_response'
                        example:
                        -   name: Push Up
                            creator: ProAthlete35
                            repetitions: 20
                            position: 0
                        -   name: Plank
                            creator: ProAthlete35
                            repetitions: 60
                            position: 1
            '404':
                description: Not found
            '405':
                description: Method not allowed
        """
        moves = []
        if user and workout:
        #  If the query is to a users workout, filter the results based on it
        #  Queries the needed information from the wrapped move based on the move_id in the move list item
            user_obj = User.query.filter_by(username=user).first()
            if not user_obj:
                raise NotFound(f"The user {user} does not exist")
            user_id = user_obj.id
            plan_obj = WorkoutPlan.query.filter_by(user_id=user_id, name=workout).first()
            plan_id  = plan_obj.id
            if not plan_id:
                raise NotFound(f"The user {user} or their workout {workout} does not exist")
        else:
            raise MethodNotAllowed

        query = MoveListItem.query.filter_by(plan_id=plan_id).all()
        query.sort(key=lambda x: x.position)
        
        body = MoveListItemCollectionBuilder(items=[])
        body.add_namespace("workoutplanner", LINK_RELATIONS_URL)
        body.add_control("self", href=request.path)
        body.add_control("profile", href=MOVELISTITEM_COLLECTION_PROFILE_URL)
        body.add_control("up", href=plan_obj.get_url(), title="Up")
        if user and workout:
            body.add_control_add_move_list_item(plan_obj)
        
        for movelistitem in query:
            item = MoveListItemBuilder(movelistitem.serialize(short_form=True))
            item.add_control("self", movelistitem.get_url())
            body["items"].append(item)
        
        return Response(json.dumps(body), 200, mimetype=MASON)


class MoveListItemItem(Resource):
    """
    Move list item is a single wrapped move item in a workout
    A wrapped move is a move with repetitions and a position added

    Covers the following URI:s,
    /api/users/{user}/workouts/{workout}/moves/{move_list_item}, GET, PUT, DELETE
    """

    def put(self, user: str=None, workout: str=None, position: int=None) -> Response:
        """
        
        Edit/create a movelist item.
        ---
        description: "Allows PUT the the following URIs: /api/users/{user}/workouts/{workout}/moves/{move_list_item}, where move_list_item is the position of the move, i.e. the array index of it."
        parameters:
        - $ref: '#/components/parameters/user'   
        - $ref: '#/components/parameters/workout'  
        - $ref: '#/components/parameters/position' 
        - $ref: '#/components/parameters/movelistitem'
        responses:
            '200':
                description: Movelist item posted successfully
                headers:
                    Location: 
                        description: URI of the new movelistitem
                        schema:
                            type: string
                            example: /api/users/Noob/workouts/Light Exercise/moves/0
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

        if not request.content_type == "application/json":
            raise UnsupportedMediaType

        try:
            validate(request.json, MoveListItem.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        try:
            #  If the target URI is a move in a users workout uses the move list item wrapper model
            if workout is not None and user is not None and position is not None:
                #  Id:s
                creator = User.query.filter_by(username=user).first()
                if not creator:
                    raise NotFound(f"No such user as {user} found")
                creator_id = creator.id

                plan = WorkoutPlan.query.filter_by(user_id=creator_id, name=workout).first()  
                if not plan:
                    raise NotFound(f"No such workout as {workout} found")
                plan_id = plan.id

                move_creator = User.query.filter_by(username=request.json["move_creator"]).first()
                if not move_creator:
                    raise NotFound(f"No such user as {move_creator} found")

                move = Move.query.filter_by(name=request.json["move_name"], user_id=move_creator.id).first()
                if not move:
                    move_name = request.json["move_name"]
                    raise NotFound(f"No such move as {move_name} found")
                move_id = move.id

                #  Get the current Move list item object
                move_list_item = MoveListItem.query.filter_by(plan_id=plan_id, position=position).first()
                if not move_list_item:
                    db.session.rollback()
                    raise NotFound(f"No move at position {position}")

                if "position" in request.json:
                    new_position = request.json["position"]
                    if new_position != position:
                        #  Get all current moves in workout plan
                        current_moves = MoveListItem.query.filter((MoveListItem.plan_id == plan_id) & (MoveListItem.position >= position)).all()
                        #  Remove moveitem from old position
                        for c_move in current_moves:
                            c_move.position -= 1

                        #  Add move to new position

                        current_moves = MoveListItem.query.filter((MoveListItem.plan_id == plan_id) & (MoveListItem.position >= new_position)).all()
                        #  Figure out the last position
                        last_position = 0
                        if current_moves:
                            last_position = max([int(c_move.position) for c_move in current_moves])
                        #  If the requested position is larger than the currently last position
                        #  Set it to the length of the movelist array - 1, else set the requested value
                        if new_position > last_position:
                            new_position = len(MoveListItem.query.filter_by(plan_id=plan_id).all()) - 1
                        #  Queries current positions of the moves in the same plan 
                        #  with a position equal or larger than the on in the request.
                        #  Returns an empty list if the position does not exist
                        #  Increments the current positions with one to enable inserting the new position

                        for current_move in current_moves:
                            current_move.position += 1
                else:
                    #  If the position was not present in the request set it to the last position in the plan.
                    #  The next free index will be the length of the result array
                    new_position = position

                if "repetitions" in request.json:
                    new_repetitions = request.json["repetitions"]
                else:
                    new_repetitions = None

                print(new_position)
                print(move_list_item.position)
                #  Change the values of the requested move list object
                move_list_item.move_id = move_id
                move_list_item.position = new_position
                move_list_item.repetitions = new_repetitions

            else:
                raise MethodNotAllowed
        except KeyError as e:
            db.session.rollback()
            raise BadRequest(e)
        except IntegrityError:
            db.session.rollback()
            raise Conflict
        else:
            db.session.commit()
            #return Response(url_for(move_list_item), status=200)
            return Response(status=200, headers={
                "Location": move_list_item.get_url()#url_for("api.movelistitemitem", user=user, workout=workout, position=new_position)
            })

    @swag_from("/workoutplanner/doc/movelistitems/get_item.yml")
    def get(self, workout: str, position: int, user: str=None) -> tuple[dict, int]:
        """
        Get a workout move list item.
        ---
        description: "Allows GET from the following URIs: /api/users/{user}/workouts/{workout}/moves/{move_list_item}, where move_list_item is the position of the move, i.e. the array index of it."
        parameters:
        - $ref: '#/components/parameters/user'     
        - $ref: '#/components/parameters/workout' 
        - $ref: '#/components/parameters/position'
        responses:
            '200':
                description: A movelist item returned successfully
                content:
                    application/json:
                        schema:
                            $ref: '#definitions/MoveListItem_response'
                        example:
                        -   name: Push Up
                            creator: ProAthlete35
                            description: Push your body up with your hands
                            repetitions: 20
                            position: 0
            '404':
                description: Not found
            '405':
                description: Method not allowed
        """
        if user:
            user_id = User.query.filter_by(username=user).first().id
            plan_id = WorkoutPlan.query.filter_by(name=workout, user_id=user_id).first().id
            query_result = MoveListItem.query.filter_by(plan_id=plan_id, position=position).first()
        else:
            raise MethodNotAllowed
        if not query_result:
            raise NotFound(f"No such move exists")

        body = MoveListItemBuilder(query_result.serialize())
        body.add_namespace("workoutplanner", LINK_RELATIONS_URL)
        body.add_control("self", href=request.path)
        body.add_control("profile", href=MOVELISTITEM_PROFILE_URL)
        body.add_control("up", href=query_result.get_collection_url(), title="Up")
        body.add_control_get_workout_plan(query_result)
        body.add_control_get_move(query_result)
        body.add_control_edit_movelist_item(query_result)
        body.add_control_delete_movelist_item(query_result)
        return Response(json.dumps(body), 200, mimetype=MASON)

    def delete(self, user: str, workout: str, position: int) -> Response:
        """
        Allows deletion of a users movelist item.
        ---
        description: "Allows DELETE of the following URIs: /api/users/{user}/workouts/{workout}/moves/{move_list_item}, here move_list_item is the position of the move, i.e. the array index of it. Obviously should require the user to be authenticated, but auth is not implemented yet."
        parameters:
        - $ref: '#/components/parameters/user' 
        - $ref: '#/components/parameters/workout'    
        - $ref: '#/components/parameters/position' 
        responses:
            '200':
                description: Move list item deleted successfully
            '404':
                description: Not found
            '405':
                description: Method not allowed
        """
        #if user and workout and position:
        if (workout!=None) and (user!=None) and (position!=None):
            #  Id:s
            creator = User.query.filter_by(username=user).first()
            if not creator:
                raise NotFound(f"No such user as {user} found")
            creator_id = creator.id              

            plan = WorkoutPlan.query.filter_by(user_id=creator_id, name=workout).first()  
            if not plan:
                raise NotFound(f"No such workout as {workout} found")
            plan_id = plan.id    

            query_result = MoveListItem.query.filter_by(plan_id=plan_id, position=position).first()
            if not query_result:
                raise NotFound
            else:
                db.session.delete(query_result)
                #  Reduce all list item positions that were larger than the deleted position
                for item in MoveListItem.query.filter(MoveListItem.plan_id == plan_id, MoveListItem.position > position).all():
                    item.position -= 1
                db.session.commit()
                return Response(status=200)
        else:
            raise MethodNotAllowed

class MoveListItemCollectionBuilder(MasonBuilder):

    def add_control_add_move_list_item(self, plan):
        '''POST a new movelistitem'''
        self.add_control_post(
            ctrl_name="workoutplanner:add-movelistitem",
            title="Add a move list item to the workout",
            href=plan.get_url() + "moves/",
            schema=MoveListItem.json_schema()
        )

class MoveListItemBuilder(MasonBuilder):

    def add_control_get_move(self, obj):
        '''GET the move of the movelistitem'''
        self.add_control(
            ctrl_name="workoutplanner:move",
            href= obj.move.get_url(),
            method="GET",
            title="Get the move of the movelist item"
        )

    def add_control_get_workout_plan(self, obj):
        '''GET the workout plan the movelistitem is a part of'''
        self.add_control(
            ctrl_name="workoutplanner:workout",
            href= obj.plan.get_url(),
            method="GET",
            title="Get the workout the movelist item is a part of"
        )

    def add_control_delete_movelist_item(self, obj):
        '''DELETE the movelistitem'''
        self.add_control_delete(
            ctrl_name="workoutplanner:delete",
            title="Delete this move list item",
            href=obj.get_url()
        )

    def add_control_edit_movelist_item(self, obj):
        '''PUT a movelistitem'''
        self.add_control_put(
            ctrl_name="edit",
            title="Edit this move list item",
            href=obj.get_url(),
            schema=MoveListItem.json_schema()
        )
