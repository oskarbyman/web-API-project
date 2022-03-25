# PWP SPRING 2021
# Workout Planner
# Group information
* Student 1. Eemil Hyväri, Eemil.Hyvari@student.oulu.fi
* Student 2. Antti Luukkonen, Antti.A.Luukkonen@student.oulu.fi
* Student 3. Oskar Byman, Oskar.Byman@student.oulu.fi

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__

#### Instructions for installing the server in a virtual enviroment:
1. Create a virtual enviroment and navigate to a copy of the project
2. Install the project:
    python setup.py install
3. Set enviromental variable and create a database:
    Bash:
        export FLASK_APP=workoutplanner
    CMD:
        set FLASK_APP=workoutplanner
    Powershell:
        $env:FLASK_APP = "workoutplanner"

    flask init-db
    flask gen-testdata
4. Run the server:
    flask run

#### Instructions for running the server:
1. Create database:
    ipython
    In [1]: from workoutplanner import db, create_app
    In [2]: db.create_all(app=create_app())
2. Run the server:
    python run.py

#### Instructions for testing:
1. Launch local dev server with above instructions
2. Change directory to the web-API-project\tests with: `cd tests`
3. Run tests with: `python api_test.py`
4. Results are printed to log.txt in the tests folder and the terminal window
