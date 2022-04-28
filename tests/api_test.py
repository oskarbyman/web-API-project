import json
import os
import pytest
import tempfile
from jsonschema import validate

from workoutplanner import create_app, db
from workoutplanner.models import User, Move, WorkoutPlan, MoveListItem, populate_db_command

@pytest.fixture(scope="function")
def app():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }
    
    app = create_app(config)
    
    with app.app_context():
        db.create_all()
        _populate_db()
        
    yield app

    os.close(db_fd)
    os.unlink(db_fname)

@pytest.fixture(scope="function")
def client(app):
    return app.test_client()

def _populate_db():
    for i in range(1, 5):
        user = User(username=f"testuser{i}")
        db.session.add(user)

    for i in range(1, 5):
        move = Move(
            name=f"testmove{i}", 
            description=f"test description for testmove{i}", 
            user=User.query.filter_by(username=f"testuser{i}").first()
            )
        db.session.add(move)

    for i in range(1, 5):
        workout = WorkoutPlan(
            name=f"testworkout{i}", 
            user=User.query.filter_by(username=f"testuser{i}").first()
            )
        workout.workout_moves.append(
            MoveListItem(
                move=Move.query.filter_by(name=f"testmove{i}").first(), repetitions=10
                )
            )
        db.session.add(workout)

    db.session.commit()

def _get_user_json(name: str="testuser") -> dict:
    """
    Return a valid json for the User Resource

    Args:
        name (str): The username, has to be unique
    Returns:
        (dict): the user json
    """
    return {"username": name}

def _get_move_json(name: str="testmove", desc: str="test description") -> dict:
    """
    Return a valid json for the Move Resource

    Args:
        name (str): The move name, has to be unique per user
        desc (str): The description of the move, essentially telling what to do
    Returns:
        (dict): the move json
    """
    return {"name": name, "description": desc}

def _get_workout_json(name: str="testworkout") -> dict:
    """
    Return a valid json for the Workout Resource

    Args:
        name (str): The workout name, has to be unique per user
    Returns:
        (dict): the workout json
    """
    return {"name": name}

def _get_movelistitem_json(name: str="testmove", creator: str="testuser", reps: int=0, position: int=0) -> dict:
    """
    Return a valid json for the Move list item Resource

    Args:
        name (str): The move name, used together with the creator to link the correct move
        creator (str): The creators name, used together with the name to link the correct move
        reps (int): The repetitions of the move in the workout
        position (int): The position of the move in the workout
    Returns:
        (dict): the move list item json
    """
    return {"move_name": name, "move_creator": creator, "repetitions": reps, "position": position}


def _check_namespace(client, response: dict) -> None:
    """
    Tests that the workoutplanner namespace is defined in the response
    """
    namespace_href = response["@namespaces"]["workoutplanner"]["name"]
    resp = client.get(namespace_href)
    assert resp.status_code == 200

def _check_control_get_method(ctrl: str, client, obj: dict) -> None:
    """
    Checks that the get method defined in the hypermedia controls works
    """

    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    assert resp.status_code == 200
    
def _check_control_delete_method(ctrl: str, client, obj: dict) -> None:
    """
    Chekcks that the delete method defined in the hypermedia controls works
    """

    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    assert resp.status_code == 200
    
def _check_control_put_method(ctrl: str, client, obj: dict, test_body: dict) -> None:
    """
    Checks that the put method defined in the hypermedia controls works
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "put"
    assert encoding == "json"
    validate(test_body, schema)
    resp = client.put(href, json=test_body)
    assert resp.status_code == 201
    
def _check_control_post_method(ctrl: str, client, obj: dict, test_body: dict) -> None:
    """
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "post"
    assert encoding == "json"
    validate(test_body, schema)
    resp = client.post(href, json=test_body)
    assert resp.status_code == 201

class TestUserCollection(object):

    RESOURCE_URL = "/api/users/"

    def test_get(self, client):
        response = client.get(self.RESOURCE_URL)
        assert response.status_code == 200
        response_body = json.loads(response.data)
        _check_namespace(client, response_body)
        _check_control_post_method("workoutplanner:add-user", client, response_body, _get_user_json())
        assert len(response_body["items"]) == 4, "The database did not contain 4 items"
        for item in response_body["items"]:
            _check_control_get_method("self", client, item)

    def test_post(self, client):
        valid = _get_user_json()

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=valid)
        assert resp.status_code == 415

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["username"] + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        # add nickname field for 400
        valid["nickname"] = "anakin"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

class TestUserItem(object):

    RESOURCE_URL = "/api/users/testuser1/"
    INVALID_URL = "/api/users/jiminy-cricket/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        response_body = json.loads(resp.data)
        _check_namespace(client, response_body)
        _check_control_get_method("profile", client, response_body)
        _check_control_get_method("up", client, response_body)
        _check_control_put_method("edit", client, response_body, _get_user_json(name="testuser12345"))
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        valid = _get_user_json()

        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=valid)
        assert resp.status_code == 415

        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404

        # add field for 400
        valid["user_nickname"] = "anakin"
        resp = client.put(self.RESOURCE_URL, json=valid)
        valid.pop("user_nickname")
        assert resp.status_code == 400

        # test a name change
        valid["username"] = "testuser1_new"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        
class TestMoveCollection(object):

    RESOURCE_URL = "/api/users/testuser1/moves/"
    INVALID_URL ="/api/users/jiminy-cricket/moves/"
    ALL_MOVES_URL = "/api/moves/"

    def test_get(self, client):
        response = client.get(self.RESOURCE_URL)
        assert response.status_code == 200
        response_body = json.loads(response.data)
        _check_namespace(client, response_body)
        _check_control_post_method("workoutplanner:add-move", client, response_body, _get_move_json())
        assert len(response_body["items"]) == 1, f"The database did not contain 4 items"
        for item in response_body["items"]:
            _check_control_get_method("self", client, item)

        response = client.get(self.ALL_MOVES_URL)
        assert response.status_code == 200
        response_body = json.loads(response.data)
        assert len(response_body["items"]) == 5, f"The database did not contain 4 items"
        for item in response_body["items"]:
            _check_control_get_method("self", client, item)

    def test_post(self, client):
        valid = _get_move_json()

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["name"] + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        # add type field for 400
        valid["type"] = "jedi mind trick"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

class TestMoveItem(object):

    RESOURCE_URL = "/api/users/testuser1/moves/testmove1/"
    INVALID_URL = "/api/users/jiminy-cricket/moves/testmove1/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        response_body = json.loads(resp.data)
        _check_namespace(client, response_body)
        _check_control_get_method("profile", client, response_body)
        _check_control_get_method("up", client, response_body)
        _check_control_get_method("collection", client, response_body)
        _check_control_put_method("edit", client, response_body, _get_move_json(name="testmove123"))
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        valid = _get_move_json()

        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=valid)
        assert resp.status_code == 415
        # test invalid url
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        # test valid url
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201

        # test the addtion of a field for 400
        valid["is_move_jedi_mind_trick"] = True
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

class TestWorkoutItem(object):

    RESOURCE_URL = "/api/users/testuser1/workouts/testworkout1/"
    INVALID_URL = "/api/users/jiminy-cricket/workouts/testworkout1/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        response_body = json.loads(resp.data)
        _check_namespace(client, response_body)
        _check_control_get_method("profile", client, response_body)
        _check_control_get_method("up", client, response_body)
        _check_control_get_method("collection", client, response_body)
        _check_control_put_method("edit", client, response_body, _get_workout_json(name="testmove123"))
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        valid = _get_workout_json()

        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=valid)
        assert resp.status_code == 415
        # test invalid url
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        # test valid url
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201

        # test the addtion of a field for 400
        valid["is_move_jedi_mind_trick"] = True
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

class TestWorkoutCollection(object):

    RESOURCE_URL = "/api/users/testuser1/workouts/"
    INVALID_URL ="/api/users/jiminy-cricket/workouts/"
    ALL_WORKOUTS_URL = "/api/workouts/"

    def test_get(self, client):
        response = client.get(self.RESOURCE_URL)
        assert response.status_code == 200
        response_body = json.loads(response.data)
        _check_namespace(client, response_body)
        _check_control_post_method("workoutplanner:add-workout", client, response_body, _get_workout_json())
        assert len(response_body["items"]) == 1, "The database did not contain a workout for testuser1"
        for item in response_body["items"]:
            _check_control_get_method("self", client, item)

        response = client.get(self.ALL_WORKOUTS_URL)
        assert response.status_code == 200
        response_body = json.loads(response.data)
        assert len(response_body["items"]) == 5, f"The database did not contain all 5 workouts"
        for item in response_body["items"]:
            _check_control_get_method("self", client, item)

    def test_post(self, client):
        valid = _get_workout_json()

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["name"] + "/"), "The location header was not correct"
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        # add type field for 400
        valid["type"] = "jedi mind trick training regime"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

class TestMoveListItemItem(object):

    RESOURCE_URL = "/api/users/testuser1/workouts/testworkout1/moves/0/"
    INVALID_URL = "/api/users/jiminy-cricket/workouts/testworkout1/move/0/"
    
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        response_body = json.loads(resp.data)
        _check_namespace(client, response_body)
        _check_control_get_method("profile", client, response_body)
        _check_control_get_method("up", client, response_body)
        _check_control_put_method("edit", client, response_body, _get_movelistitem_json("testmove1", "testuser1", 15))
        _check_control_delete_method("workoutplanner:delete", client, response_body)
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        valid = _get_movelistitem_json("testmove1", "testuser1", 15)

        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=valid)
        assert resp.status_code == 415
        # test invalid url
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        # test valid url
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201

        # test the addtion of a field for 400
        valid["is_move_jedi_mind_trick"] = True
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

class TestMoveListItemCollection(object):

    RESOURCE_URL = "/api/users/testuser1/workouts/testworkout1/moves/"
    INVALID_URL ="/api/users/jiminy-cricket/workouts/testworkout1/moves/"

    def test_get(self, client):
        response = client.get(self.RESOURCE_URL)
        assert response.status_code == 200
        response_body = json.loads(response.data)
        _check_namespace(client, response_body)
        _check_control_post_method("workoutplanner:add-movelistitem", client, response_body, _get_movelistitem_json("testmove1", "testuser1"))
        assert len(response_body["items"]) == 1, "The database did not contain a workout for testuser1"
        for item in response_body["items"]:
            _check_control_get_method("self", client, item)

    def test_post(self, client):
        valid = _get_movelistitem_json("testmove1", "testuser1", 15, 0)

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + str(valid["position"]) + "/"), "The location header was not correct"
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # send same data again to add the same move twice to the workout, should result in 201
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201

        # add type field for 400
        valid["type"] = "jedi mind trick training regime"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
