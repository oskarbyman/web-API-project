# Api tests for The Web API course project
# Author: Oskar Byman

***Settings***
Library         api_test.py
Test Timeout    120s
Suite Setup     Test Suite Setup
Suite Teardown  Test Suite Teardown
Test Setup      Test Setup
Test Teardown   Test Teardown

***Test Cases***
Test Users GET
    test succesful get  /api/users/

Test Correct User POST
    test succesful post  /api/users/  {"username":"testuser2"}

Test Incorrect User POST with user_id as key
    test unsuccesful post  /api/users/  {"user_id":"testuser2"}

Test Incorrect User POST with just a string
    test unsuccesful post  /api/users/  {"testuser2"}

Test Correct User PUT with username change
    test succesful put  /api/users/  {"username":"testuser_new"}

Test Incorrect User PUT with username change
    test succesful put  /api/users/  "testuser_new"


***Keywords***
Test Suite Setup
    Api Suite Setup

Test Suite Teardown
    Api Suite Teardown

Test Setup
    Api Test Setup

Test Teardown
    Api Test Teardown