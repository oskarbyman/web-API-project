import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger, swag_from


db = SQLAlchemy()

from workoutplanner.links import *

# Based on http://flask.pocoo.org/docs/1.0/tutorial/factory/#the-application-factory
# Modified to use Flask SQLAlchemy
def create_app(test_config=None):
    """
    App factory for the api
    """

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    
    app.config["SWAGGER"] = {
        "title": "Workout planner API",
        "openapi": "3.0.3",
        "uiversion": 3,
    }
    swagger = Swagger(app, template_file="doc/workoutplanner.yml")
    
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)
        
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    db.init_app(app)
    
    from . import api as api_
    from . import models

    app.register_blueprint(api_.api_bp)
    api = api_.make_api(app)

    # Register cli commands to create and populate db
    app.cli.add_command(models.initialize_db_command)
    app.cli.add_command(models.populate_db_command)
    app.cli.add_command(models.nuke_db_command)

    return app
