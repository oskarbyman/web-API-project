from enum import unique
from workoutplanner import db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.orderinglist import ordering_list
import json
import click
from flask.cli import with_appcontext

class User(db.Model):
    """
    Database model for User. Includes unique username and relationships to moves and workouts created by the user.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)

    user_moves = db.relationship("Move", back_populates="user")
    workouts = db.relationship("WorkoutPlan", back_populates="user")

    @staticmethod
    def json_schema():
        return json.load(open('workoutplanner/schemas/user_schema.json'))

class WorkoutPlan(db.Model):
    """
    Database model for WorkoutPlan. Includes references to the creator of the plan and ordered list of moves in the plan.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user = db.relationship("User", back_populates="workouts", uselist=False)
    workout_moves = db.relationship("MoveListItem", back_populates="plan", order_by="MoveListItem.position", collection_class=ordering_list("position"))

    __table_args__ = (db.UniqueConstraint("name", "user_id", name="_name_user_constraint"),)

    @staticmethod
    def json_schema():
        return json.load(open('workoutplanner/schemas/workout_plan_schema.json'))

class MoveListItem(db.Model):
    """
    Database model for MoveListItem. Is an instance of a list item in a workout plan.
    """

    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer, nullable=False)

    repetitions = db.Column(db.Integer)

    plan_id = db.Column(db.Integer, db.ForeignKey("workout_plan.id"), nullable=False)
    move_id = db.Column(db.Integer, db.ForeignKey("move.id"), nullable=False)

    move = db.relationship("Move", back_populates="workout_move", uselist=False)
    plan = db.relationship("WorkoutPlan", back_populates="workout_moves", uselist=False)


    @staticmethod
    def json_schema():
        return json.load(open('workoutplanner/schemas/move_list_item_schema.json'))

class Move(db.Model):
    """
    Database model for Move. Includes references to the creator of the move information about the move.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    user = db.relationship("User", back_populates="user_moves", uselist=False)
    workout_move = db.relationship("MoveListItem", back_populates="move")

    __table_args__ = (db.UniqueConstraint("name", "user_id", name="_name_user_constraint"),)

    @staticmethod
    def json_schema():
        return json.load(open('workoutplanner/schemas/move_schema.json'))


#MASONBUILDER
class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    
    Note that child classes should set the *DELETE_RELATION* to the application
    specific relation name from the application namespace. The IANA standard
    does not define a link relation for deleting something.
    """

    DELETE_RELATION = ""

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.
        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.
        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.
        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.
        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md
        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href
        
    def add_control_post(self, ctrl_name, title, href, schema):
        """
        Utility method for adding POST type controls. The control is
        constructed from the method's parameters. Method and encoding are
        fixed to "POST" and "json" respectively.
        
        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """
    
        self.add_control(
            ctrl_name,
            href,
            method="POST",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_put(self, ctrl_name, title, href, schema):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control name, method and
        encoding are fixed to "edit", "PUT" and "json" respectively.
        
        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            ctrl_name,
            href,
            method="PUT",
            encoding="json",
            title=title,
            schema=schema
        )
        
    def add_control_delete(self, ctrl_name, title, href):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control method is fixed to
        "DELETE", and control's name is read from the class attribute
        *DELETE_RELATION* which needs to be overridden by the child class.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        """
        
        self.add_control(
            ctrl_name,
            href,
            method="DELETE",
            title=title,
        )




# Utility functions to create and populate a database
@click.command("init-db")
@with_appcontext
def initialize_db_command():
    db.create_all()

@click.command("gen-testdata")
@with_appcontext
def populate_db_command():
    u1 = User(username="ProAthlete35")
    u2 = User(username="Noob")

    db.session.add(u1)
    db.session.add(u2)
    db.session.commit()

    m1 = Move(name="Push Up", description="Push your body up with your hands", user=u1)
    m2 = Move(name="Opening Fridge", description="Walk to the nearest fridge and open it", user=u1)
    m3 = Move(name="Plank", description="Use your muscles to keep your body in a straight horizontal line", user=u2)

    db.session.add(m1)
    db.session.add(m2)
    db.session.add(m3)
    db.session.commit()

    p1 = WorkoutPlan(name="Light Exercise", user=u1)
    p2 = WorkoutPlan(name="Max Suffering", user=u2)

    db.session.add(p1)
    db.session.add(p2)
    db.session.commit()

    p1.workout_moves.append(MoveListItem(move=m1))
    p1.workout_moves.append(MoveListItem(move=m3))
    p1.workout_moves.append(MoveListItem(move=m1))

    p2.workout_moves.append(MoveListItem(move=m2, repetitions=4))

    db.session.commit()
    