"""
Test script for the project api,
uses the requests library to send requests to the different api URI:s

Author: Oskar Byman
"""
import os
import sys
import json
import logging
from requests import get, post, put, delete, Response

sys.path.append("..")
from workoutplanner.utils import create_db, populate_db

class Tester():

    """
    Testing class that contains the needed parameters and methods for testing
    """

    def __init__(self, user: str="testuser", move: str="testmove", workout: str="testworkout", base_uri: str="http://127.0.0.1:5000") -> None:
        
        self.test_user = user
        self.test_move = move
        self.test_workout = workout
        self.base_uri = base_uri
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.FileHandler("log.txt"))
        self.logger.addHandler(logging.StreamHandler())
        
        #  URIs
        #  Both URIs that end in /moves point to a list that can be accessed with an index (move position in list)

        self.uri_obj_list = [
            {
                "uri": f"/api/users",
                "allowed_methods": ["get", "post"],
                "correct_data": [
                    {"username": self.test_user}
                ], 
                "incorrect_data": [
                    {"username": 1234},
                    {"user_id": 1234},
                    {"user_id": self.test_user},
                    "just a string",
                    1234
                ]
            },
            {
                "uri": f"/api/users/{self.test_user}",
                "allowed_methods": ["get", "put", "delete"],
                "correct_data": [
                    {"username": f"{self.test_user}_new"}
                ], 
                "incorrect_data": [
                    {"username": 1234},
                    {"user_id": 1234},
                    {"user_id": self.test_user},
                    "just a string",
                    1234
                ]
            },
            {
                "uri": f"/api/users/{self.test_user}/moves",
                "allowed_methods": ["get", "post"],
                "correct_data": [
                    {"name": self.test_move, "description": "This is a test move for testing purposes"}
                ], 
                "incorrect_data": [
                    {"username": 1234, "description": "This is a test move for testing purposes"},
                    {"name": 1234, "description": "This is a test move for testing purposes"},
                    {"name": self.test_move, "description": 1234},
                    "just a string",
                    1234
                    ]
            },
            {
                "uri": f"/api/users/{self.test_user}/moves/{self.test_move}",
                "allowed_methods": ["get", "put", "delete"],
                "correct_data": [
                    {"name": self.test_move, "description": "This is a test move for testing purposes"}
                ], 
                "incorrect_data": [
                    {"username": 1234, "description": "This is a test move for testing purposes"},
                    {"name": 1234, "description": "This is a test move for testing purposes"},
                    {"name": self.test_move, "description": 1234},
                    "just a string",
                    1234
                    ]
            },
            {
                "uri": f"/api/users/{self.test_user}/workouts",
                "allowed_methods": ["get", "post"],
                "correct_data": [
                    {"name": self.test_workout}
                ],
                "incorrect_data": [
                    {"workout_name": self.test_workout},
                    {"name": 123412341234},
                    {"name": self.test_workout, "moves":[{"name": self.test_move, "description": "This is a test move for testing purposes"}]},
                    "just a string",
                    1234
                ]
            },
            {
                "uri": f"/api/users/{self.test_user}/workouts/{self.test_workout}",
                "allowed_methods": ["get", "put", "delete"],
                "correct_data": [
                    {"name": f"{self.test_workout}_new"}
                ],
                "incorrect_data": [
                    {"workout_name": self.test_workout},
                    {"name": 123412341234},
                    {"name": self.test_workout, "moves":[{"name": self.test_move, "description": "This is a test move for testing purposes"}]},
                    "just a string",
                    1234
                ]
            },
            {
                "uri": f"/api/users/{self.test_user}/workouts/{self.test_workout}/moves",
                "allowed_methods": ["get", "post"],
                "correct_data": [
                    {"move_name": self.test_move},
                    {"move_name": self.test_move, "repetitions": 10},
                    {"move_name": self.test_move, "position": 10000000},
                    {"move_name": self.test_move, "repetitions": 0, "position": 1},
                    {"move_name": self.test_move, "repetitions": 1010101, "position": 0}
                ],
                "incorrect_data": [
                    {"move_name": self.test_move, "repetitions": -10},
                    {"move_name": self.test_move, "position": -10000000},
                    {"move_name": self.test_move, "repetitions": "0", "position": 1},
                    {"move_name": self.test_move, "repetitions": "-10"},
                    {"move_name": self.test_move, "position": "-10000000"},
                    {"move_name": self.test_move, "repetitions": "0", "position": "1"},
                    {"repetitions": "0", "position": "1"},
                    "just a string",
                    1234
                ]
            },
            {
                "uri": f"/api/users/{self.test_user}/workouts/{self.test_workout}/moves/0",
                "allowed_methods": ["get", "put", "delete"],
                "correct_data": [
                    {"move_name": self.test_move},
                    {"move_name": self.test_move, "repetitions": 10},
                    {"move_name": self.test_move, "position": 10000000},
                    {"move_name": self.test_move, "repetitions": 0, "position": 1},
                    {"move_name": self.test_move, "repetitions": 1010101, "position": 0}
                ],
                "incorrect_data": [
                    {"move_name": self.test_move, "repetitions": -10},
                    {"move_name": self.test_move, "position": -10000000},
                    {"move_name": self.test_move, "repetitions": "0", "position": 1},
                    {"move_name": self.test_move, "repetitions": "-10"},
                    {"move_name": self.test_move, "position": "-10000000"},
                    {"move_name": self.test_move, "repetitions": "0", "position": "1"},
                    {"repetitions": "0", "position": "1"},
                    "just a string",
                    1234
                ]
            },
            {
                "uri": f"/api/moves",
                "allowed_methods": ["get"],
                "correct_data": [],
                "incorrect_data": []
            },
            {
                "uri": f"/api/workouts/",
                "allowed_methods": ["get"],
                "correct_data": [],
                "incorrect_data": []
            }
        ]

    #  Utilities

    def _get_from_uri(self, uri: str) -> Response:
        full_uri = self.base_uri + uri
        result = get(full_uri)
        return result

    def _post_to_uri(self, uri: str, data: dict) -> Response:
        full_uri = self.base_uri + uri
        result = post(full_uri, data=json.dumps(data), headers={"Content-Type": "application/json"})
        return result

    def _put_to_uri(self, uri: str, data: dict) -> Response:
        full_uri = self.base_uri + uri
        result = put(full_uri, data=json.dumps(data), headers={"Content-Type": "application/json"})
        return result

    def _delete_from_uri(self, uri: str) -> Response:
        full_uri = self.base_uri + uri
        result = delete(full_uri)
        return result

    #  Test methods

    def test_get(self, test_obj: dict) -> None:
        """Test get from uri
        Steps:
        GET from an URI

        PASS requirements:
        All requests receive a status code of 200
        """
        uri = test_obj["uri"]
        self.logger.debug(f"GETting from {uri}")
        get_result = self._get_from_uri(uri)
        self.logger.debug(f"GET response: {get_result.text}")
        assert get_result.status_code == 200

    def test_post(self, test_obj: dict) -> None:
        """Test post to uri
        Steps:
        POST from an URI

        PASS requirements:
        All correct requests receive a status code of 200
        All incorrect requests receive a status code of 200
        """
        uri = test_obj["uri"]
        #  POST event
        self.logger.debug(f"POSTing {uri}")
        for correct_item in test_obj["correct_data"]:
            get_result = self._post_to_uri(uri, correct_item)
            self.logger.debug(f"Post response: {get_result.text}")
            if "post" in test_obj["allowed_methods"]:
                assert get_result.status_code == 200
            else:
                assert get_result.status_code != 200
        for incorrect_item in test_obj["incorrect_data"]:
            get_result = self._post_to_uri(uri, incorrect_item)
            self.logger.debug(f"Post response: {get_result.text}")
            assert get_result.status_code != 200

    def test_put(self, test_obj: dict) -> None:
        """Test put to uri
        Steps:
        PUT from an URI

        PASS requirements:
        All correct requests receive a status code of 200
        All incorrect requests receive a status code of 200
        """
        uri = test_obj["uri"]
        #  PUT event
        self.logger.debug(f"PUTing {uri}")
        for correct_item in test_obj["correct_data"]:
            get_result = self._put_to_uri(uri, correct_item)
            self.logger.debug(f"Put response: {get_result.text}")
            if "put" in test_obj["allowed_methods"]:
                assert get_result.status_code == 200
            else:
                assert get_result.status_code != 200
        for incorrect_item in test_obj["incorrect_data"]:
            get_result = self._put_to_uri(uri, incorrect_item)
            self.logger.debug(f"Put response: {get_result.text}")
            assert get_result.status_code != 200

    def test_delete(self, test_obj: dict) -> None:
        """Test delete from uri
        Steps:
        PUT from an URI

        PASS requirements:
        All correct requests receive a status code of 200
        All incorrect requests receive a status code of 200
        """
        uri = test_obj["uri"]
        self.logger.debug(f"DELETing from {uri}")
        get_result = self._get_from_uri(uri)
        self.logger.debug(f"DELETE response: {get_result.text}")
        if "delete" in test_obj["allowed_methods"]:
            assert get_result.status_code == 200
        else:
            assert get_result.status_code != 200

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
    #populate_db()

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