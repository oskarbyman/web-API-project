"""
Test script for the project api,
uses the requests library to send requests to the different api URI:s

Author: Oskar Byman
"""
import sys
import json
import logging
from requests import get, post, put, delete, Response

sys.path.append("..")
from workoutplanner.utils import db, create_app

class api_test():

    """
    Testing class that contains the needed parameters and methods for testing
    """

    def __init__(self, base_uri: str="http://127.0.0.1:5000") -> None:

        self.base_uri = base_uri
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.FileHandler("log.txt"))
        self.logger.addHandler(logging.StreamHandler())
        
        #  URIs
        #  Both URIs that end in /moves point to a list that can be accessed with an index (move position in list)

    def api_suite_setup(self):
        """
        Suite setup for the Api tests.
        Populates the local server database with data
        """
        db.create_all(app=create_app())
        self._post_to_uri("/api/users/", {"username": "testuser"})
        self._post_to_uri("/api/users/testuser/workouts/", {"name": "testworkout"})
        self._post_to_uri("/api/users/testuser/moves/", {"name": "testmove", "description": "A generic testmove"})
        self._post_to_uri("/api/users/testuser/workouts/testworkout/moves/", {"move_name": "testmove", "repetitions": 0})

    def api_suite_teardown(self):
        """
        Suite teardown for the Api tests.
        """

    def api_test_setup(self):
        """
        Test setup for each individual test
        """
        self._put_to_uri("/api/users/testuser/", {"username": "testuser"})
        self._put_to_uri("/api/users/testuser/workouts/testworkout/", {"name": "testworkout"})
        self._put_to_uri("/api/users/testuser/moves/testmove", {"name": "testmove", "description": "A generic testmove"})
        self._post_to_uri("/api/users/testuser/workouts/testworkout/moves/", {"move_name": "testmove", "repetitions": 0, "position": 0})
        
    def api_test_teardown(self):
        """
        Test teardown for each individual test
        """
        self._delete_from_uri("/api/users/testuser/workouts/testworkout/")
        self._delete_from_uri("/api/users/testuser/workouts/testworkout/moves/0")

    #  Utilities

    def _get_from_uri(self, uri: str) -> Response:
        full_uri = self.base_uri + uri
        result = get(full_uri)
        result.raise_for_status()
        return result

    def _post_to_uri(self, uri: str, data: dict) -> Response:
        full_uri = self.base_uri + uri
        result = post(full_uri, data=json.dumps(data), headers={"Content-Type": "application/json"})
        result.raise_for_status()
        return result

    def _put_to_uri(self, uri: str, data: dict) -> Response:
        full_uri = self.base_uri + uri
        result = put(full_uri, data=json.dumps(data), headers={"Content-Type": "application/json"})
        result.raise_for_status()
        return result

    def _delete_from_uri(self, uri: str) -> Response:
        full_uri = self.base_uri + uri
        result = delete(full_uri)
        result.raise_for_status()
        return result

    #  Test methods

    def test_succesful_get(self, uri: str) -> None:
        """Test get from uri
        Steps:
        GET from an URI

        PASS requirements:
        All requests receive a status code of 200
        """
        self.logger.info(f"Getting from {uri}")
        get_result = self._get_from_uri(uri)
        self.logger.debug(f"GET response: {get_result.content}")
        if not get_result.status_code == 200:
            raise Exception(
                f"Status code to get request was not 200, uri: {uri}"
            )

    def test_succesful_post(self, uri: str, data: dict) -> None:
        """Test post to uri
        Steps:
        POST to an URI
        Check status code of response

        PASS requirements:
        A correct request receives a status code of 200
        """
        #  POST event
        self.logger.info(f"Posting to {uri}")
        post_result = self._post_to_uri(uri, data)
        self.logger.debug(f"Posted: {data}, Post response: {post_result.content}")
        if not post_result.status_code == 200:
            raise Exception(
                f"Status code to post request was not 200, uri: {uri}"
            )

    def test_unsuccesful_post(self, uri: str, data: dict) -> None:
        """Test post to uri
        Steps:
        POST to an URI
        Check status code of response

        PASS requirements:
        An incorrect request receives a status code of not 200
        """
        self.logger.info(f"Posting to {uri}")
        post_result = self._post_to_uri(uri, data)
        self.logger.debug(f"Posted: {data}, Post response: {post_result.content}")
        if post_result.status_code == 200:
            raise Exception(
                f"Status code to post request should not be 200, uri: {uri}"
            )

    def test_succesful_put(self, uri: str, data: dict) -> None:
        """Test put to uri
        Steps:
        PUT to an URI
        Check status code of response

        PASS requirements:
        A correct request receives a status code of 200
        """
        #  POST event
        self.logger.info(f"Posting to {uri}")
        put_result = self._put_to_uri(uri, data)
        self.logger.debug(f"Put: {data}, Put response: {put_result.content}")
        if not put_result.status_code == 200:
            raise Exception(
                f"Status code to put request was not 200, uri: {uri}"
            )

    def test_unsuccesful_put(self, uri: str, data: dict) -> None:
        """Test put to uri
        Steps:
        PUT from an URI
        Check status code of response

        PASS requirements:
        An incorrect request should receive a status code of not 200
        """
        self.logger.info(f"Putting to {uri}")
        put_result = self._put_to_uri(uri, data)
        self.logger.debug(f"Put data: {data}, Put response: {put_result.content}")
        if put_result.status_code == 200:
            raise Exception(
                f"Status code to put request should not be 200, uri: {uri}"
            )

    def test_succesful_delete(self, uri:str, data: dict) -> None:
        """Test delete from uri
        Steps:
        PUT from an URI

        PASS requirements:
        All correct requests receive a status code of 200
        All incorrect requests receive a status code of 200
        """
        self.logger.info(f"Deleting from {uri}")
        delete_result = self._delete_from_uri(uri)
        self.logger.debug(f"DELETE response: {delete_result.content}")
        if not delete_result.status_code == 200:
            raise Exception(
                f"Status code to put request was not 200, uri: {uri}"
            )

    def test_unsuccesful_delete(self, uri:str, data: dict) -> None:
        """Test delete from uri
        Steps:
        PUT from an URI

        PASS requirements:
        All correct requests receive a status code of 200
        All incorrect requests receive a status code of 200
        """
        self.logger.info(f"Deleting from {uri}")
        delete_result = self._delete_from_uri(uri)
        self.logger.debug(f"DELETE response: {delete_result.content}")
        if delete_result.status_code == 200:
            raise Exception(
                f"Status code to put request should not be 200, uri: {uri}"
            )

    def test_resource_creation(self, uri: str, data: dict) -> None:
        """Test resource creation

        Steps:
        POST a new object to URI
        GET the respective object from the response URI

        PASS requirements:
        All requests receive a status code of 200
        """
        self.logger.debug(f"Posting {data} to {uri}")
        post_result = self._post_to_uri(uri, data)
        self.logger.debug(f"POST response: {post_result.text}")
        if not post_result.status_code == 200:
            raise Exception(
                f"Status code for POST was not 200, URI: {uri}, data: {data}"
            )
        self.logger.debug(f"Getting from URI: {uri}")
        get_result = self._get_from_uri(uri)
        self.logger.debug(f"GET result: {get_result.text}")
        if not get_result.status_code == 200:
            raise Exception(
                f"Status code for GET was not 200, URI: {uri}, data: {data}"
            )
        if not data in get_result.text: 
            raise Exception(
                f"Could not find the POSTed data from response, URI: {uri}, data: {data}"
            )



if __name__ == "__main__":
    pass