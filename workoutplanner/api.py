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

#TODO: Add routing for rest of the resources
api.add_resource(UserCollection, "/users/")
