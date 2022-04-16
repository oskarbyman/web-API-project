"""
REST API implementation
Programmable Web Project, Workout planner

Author: Eemil Hyvari, Antti Luukkonen and Oskar Byman
"""

import json
from flask import Flask, Blueprint, Response
from flask_restful import Api

from workoutplanner.resources.user import UserItem, UserCollection, UserConverter
from workoutplanner.resources.move import MoveItem, MoveCollection, MoveConverter
from workoutplanner.resources.workout_plan import WorkoutPlanItem, WorkoutPlanCollection, WorkoutPlanConverter
from workoutplanner.resources.move_list_item import MoveListItemItem, MoveListItemCollection, MoveListItemConverter

from workoutplanner.links import *

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

def make_api(app):
    #  User resources from resources/user.py
    api.add_resource(UserCollection, "/users/")
    api.add_resource(UserItem, "/users/<user>/")

    #  Move resources from resources/move.py
    api.add_resource(MoveCollection,
        "/users/<user>/moves/",
        "/moves/"
    )
    api.add_resource(MoveItem,
        "/users/<user>/moves/<move>/",
        "/moves/<move>/"
    )

    #  Workout resources from resource/workout_plan.py
    api.add_resource(WorkoutPlanCollection,
        "/users/<user>/workouts/",
        "/workouts/"
    )
    api.add_resource(WorkoutPlanItem,
        "/users/<user>/workouts/<workout>/",
        "/workouts/<workout>/"
    )

    #  MoveListItem resources from resources/move_list_item.py
    api.add_resource(MoveListItemCollection,
        "/users/<user>/workouts/<workout>/moves/",
        "/workouts/<workout>/moves/"
    )
    api.add_resource(MoveListItemItem,
        "/users/<user>/workouts/<workout>/moves/<int:position>/",
        "/workouts/<workout>/moves/<int:position>/"
    )
    
    app.url_map.converters["user"] = UserConverter
    app.url_map.converters["move"] = MoveConverter
    app.url_map.converters["workout_plan"] = WorkoutPlanConverter
    app.url_map.converters["move_list_item"] = MoveListItemConverter

    @app.route("/api/")
    def api_entry():
        api_entrypoint = {
            "@namespaces": {
                "workoutplanner": {
                    "name": "http://localhost:5000/link-relations/"
                }
            },
            "@controls": {
                "workoutplanner:users-all": {
                    "href": "/api/users/"
                },
                "workoutplanner:moves-all": {
                    "href": "/api/moves/"
                },
                "workoutplanner:workouts-all": {
                    "href": "/api/workouts/"
                }
            }
        }
        return Response(json.dumps(api_entrypoint), 200, mimetype=MASON)
        
    @app.route(USER_PROFILE_URL)
    def profile_user():
        return "Absolute nonsense"
        
    @app.route(MOVE_PROFILE_URL)
    def profile_move():
        return "Absolute nonsense"
        
    @app.route(WORKOUT_PROFILE_URL)
    def profile_workout():
        return "Absolute nonsense"

    @app.route(MOVELISTITEM_PROFILE_URL)
    def profile_movelist():
        return "Absolute nonsense"        
    
    @app.route(USER_COLLECTION_PROFILE_URL)
    def profile_user_collection():
        return "Absolute nonsense"
        
    @app.route(MOVE_COLLECTION_PROFILE_URL)
    def profile_move_collection():
        return "Absolute nonsense"
        
    @app.route(WORKOUT_COLLECTION_PROFILE_URL)
    def profile_workout_collection():
        return "Absolute nonsense"

    @app.route(MOVELISTITEM_COLLECTION_PROFILE_URL)
    def profile_movelist_collection():
        return "Absolute nonsense"      
    

    @app.route(ERROR_PROFILE)
    def profile_error():
        return "Lorem Ipsum"

    @app.route(LINK_RELATIONS_URL)
    def link_relations():
        return "Try looking elsewhere"
        
        
    return api

