"""
REST API implementation
ProgrammableWeb Project, Workout  planner

Author: Eemil Hyvari, Antti Luukkonen and Oskar Byman
"""

from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from models import *

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api = Api(app)

