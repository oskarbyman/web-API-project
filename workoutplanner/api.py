"""
REST API implementation
Programmable Web Project, Workout planner

Author: Eemil Hyvari, Antti Luukkonen and Oskar Byman
"""

from flask import Flask, Blueprint
from flask_restful import Api

from workoutplanner.resources.move import MoveCollection, MoveItem
from workoutplanner.resources.move_list_item import MoveListItemCollection, MoveListItemItem
from workoutplanner.resources.user import UserCollection, UserItem
from workoutplanner.resources.workout_plan import WorkoutPlanCollection, WorkoutPlanItem

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

#  User resources from resources/user.py
api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<user>")

#  Move resources from resources/move.py
api.add_resource(MoveCollection,
    "/users/<user>/moves",
    "/moves"
)
api.add_resource(MoveItem,
    "/users/<user>/moves/<move>",
    "/moves/<move>"
)

#  Workout resources from resource/workout_plan.py
api.add_resource(WorkoutPlanCollection,
    "/users/<user>/workouts",
    "/workouts"
)
api.add_resource(WorkoutPlanItem,
    "/users/<user>/workouts/<workout>",
    "/workouts/<workout>"
)

#  MoveListItem resources from resources/move_list_item.py
api.add_resource(MoveListItemCollection,
    "/users/<user>/workouts/<workout>/moves",
    "/workouts/<workout>/moves"
)
api.add_resource(MoveListItemItem,
    "/users/<user>/workouts/<workout>/moves/<int:position>",
    "/workouts/<workout>/moves/<int:position>"
)
