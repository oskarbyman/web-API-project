"""
Test script for the project api,
uses the requests library to send requests to the different api URI:s

Author: Oskar Byman
"""
import json
import logging
from requests import get, post, put, delete, Response
from workoutplanner.utils import create_db, populate_db

class Tester():

    """
    Testing class that contains the needed parameters and methods for testing
    """

    def __init__(self, user: str="testuser", move: str="testmove", workout: str="testworkout") -> None:
        
        self.test_user = user
        self.test_move = move
        self.test_workout = workout
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.FileHandler("log.txt", encoding="utf-8"))
        self.logger.addHandler(logging.StreamHandler())
        
        #  URIs
        #  Both URIs that end in /moves point to a list that can be accessed with an index (move position in list)

        self.uri_obj_list = [
            {"uri": f"/api/users", "correct_data": {}, "incorrect_data": {}},
            {"uri": f"/api/users/{self.test_user}", "correct_data": {}, "incorrect_data": {}},
            {"uri": f"/api/users/{self.test_user}/moves", "correct_data": {}, "incorrect_data": {}},
            {"uri": f"/api/users/{self.test_user}/moves/{self.test_move}", "correct_data": {}, "incorrect_data": {}},
            {"uri": f"/api/users/{self.test_user}/workouts", "correct_data": {}, "incorrect_data": {}},
            {"uri": f"/api/users/{self.test_user}/workouts/{self.test_workout}", "correct_data": {}, "incorrect_data": {}},
            {"uri": f"/api/users/{self.test_user}/workouts/{self.test_workout}/moves", "correct_data": {}, "incorrect_data": {}},
            {"uri": f"/api/moves", "correct_data": {}, "incorrect_data": {}},
            {"uri": f"/api/moves/{self.test_move}", "correct_data": {}, "incorrect_data": {}},
            {"uri": f"/api/workouts/", "correct_data": {}, "incorrect_data": {}},
            {"uri": f"/api/workouts/{self.test_workout}", "correct_data": {}, "incorrect_data": {}},
            {"uri": f"/api/workouts/{self.test_workout}/moves", "correct_data": {}, "incorrect_data": {}},
        ]

    #  Utilities

    def _get_from_uri(self, uri: str) -> Response:
        result = get(uri)
        return result

    def _post_to_uri(self, uri: str, data: dict) -> Response:
        result = post(uri, data=json.dumps(data), headers={"Content-Type": "application/json"})
        return result

    def _put_to_uri(self, uri: str, data: dict) -> Response:
        result = put(uri, data=json.dumps(data), headers={"Content-Type": "application/json"})
        return result

    def _delete_from_uri(self, uri: str) -> Response:
        result = delete(uri)
        return result

    #  Test methods

    def test_get(self, test_obj: dict) -> None:
        """Test resource creation

        Steps:
        GET from an URI

        PASS requirements:
        All requests receive a status code of 200
        """
        uri = test_obj["uri"]
        #  POST event
        self.logger.debug(f"GETting from {uri}")
        get_result = self._get_from_uri(uri)
        self.logger.debug(f"GET response: {get_result.text}")
        assert get_result.status_code == 200

    def test_post(self, test_obj: dict) -> None:
        pass

    def test_put(self, test_obj: dict) -> None:
        pass

    def test_delete(self, test_obj: dict) -> None:
        pass

    def test_resource_creation(self, test_obj: dict) -> None:
        """Test resource creation

        Steps:
        POST a new object to URI
        GET the respective object from the response URI

        PASS requirements:
        All requests receive a status code of 200
        """
        #  URI and POST data
        uri = test_obj["uri"]
        data = test_obj["correct_data"]
        #  POST event
        self.logger.debug(f"POSTing {data} to {uri}")
        post_result = self._post_to_uri(uri, data)
        self.logger.debug(f"POST response: {post_result.text}")
        #  Assert status code
        assert post_result.status_code == 200, f"Status code for POST was not 200, URI: {uri}, data: {data}"
        #  GET event
        self.logger.debug(f"GETting from URI: {uri}")
        get_result = self._get_from_uri(uri)
        self.logger.debug(f"GET result: {get_result.text}")
        assert get_result.status_code == 200, f"Status code for GET was not 200, URI: {uri}, data: {data}"
        assert data in get_result.text, f"Could not find the POSTed data from response, URI: {uri}, data: {data}"



if __name__ == "__main__":

    tester = Tester()
    create_db()
    populate_db()

    pass_n = 0
    fail_n = 0

    #  Generic GET tests
    for obj in tester.uri_obj_list:
        try:
            tester.test_get(obj)
        except AssertionError as e:
            tester.logger.error(e)
            fail_n += 1
            continue
        else:
            uri = obj["uri"]
            tester.logger.info(f"PASS, GET test, URI: {uri}")
            pass_n += 1

    #  Generic POST tests
    for obj in tester.uri_obj_list:
        try:
            tester.test_post(obj)
        except AssertionError as e:
            tester.logger.error(e)
            fail_n += 1
            continue
        else:
            uri = obj["uri"]
            data = obj["correct_data"]
            tester.logger.info(f"PASS, POST test, URI: {uri}, data: {data}")
            pass_n += 1

    #  Generic PUT tests
    for obj in tester.uri_obj_list:
        try:
            tester.test_put(obj)
        except AssertionError as e:
            tester.logger.error(e)
            fail_n += 1
            continue
        else:
            uri = obj["uri"]
            data = obj["correct_data"]
            tester.logger.info(f"PASS, PUT test, URI: {uri}, data: {data}")
            pass_n += 1

    #  Generic DELETE tests
    for obj in tester.uri_obj_list:
        try:
            tester.test_put(obj)
        except AssertionError as e:
            tester.logger.error(e)
            fail_n += 1
            continue
        else:
            uri = obj["uri"]
            tester.logger.info(f"PASS, PUT test, URI: {uri}")
            pass_n += 1

    tester.logger.info(f"Results, Passed tests: {pass_n}, Failed tests: {fail_n}, PASS%: {(pass_n/(pass_n + fail_n)) * 100}")