# PWP SPRING 2021
# Workout Planner
# Group information
* Student 1. Eemil Hyväri, Eemil.Hyvari@student.oulu.fi
* Student 2. Antti Luukkonen, Antti.A.Luukkonen@student.oulu.fi
* Student 3. Oskar Byman, Oskar.Byman@student.oulu.fi

Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client
---
#### Instructions for installing the server in a virtual enviroment:
1. Create a virtual enviroment and navigate to a copy of the project
2. Install the project:
    - `python setup.py install` or `pip install .`
3. Restart the enviroment and activate it again
4. Set enviromental variable:
    - Bash: `export FLASK_APP=workoutplanner`
    - CMD: `set FLASK_APP=workoutplanner`
    - Powershell: `$env:FLASK_APP = "workoutplanner"`
5. create a database:
    1. `flask init-db`
    2. `flask gen-testdata` //Optional
6. Run the server:
    - `flask run`
---
#### Instructions for running the server:
1. Create database:
    1. `ipython`
    2. `In [1]: from workoutplanner import db, create_app`
    3. `In [2]: db.create_all(app=create_app())`
2. Run the server:
    - `python run.py`
---
#### Instructions for testing:
1. Launch local dev server with above instructions
2. Change directory to the web-API-project\tests with: `cd tests`
3. Run tests with: `python api_test.py`
4. Results are printed to log.txt in the tests folder and the terminal window
