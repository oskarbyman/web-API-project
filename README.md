# PWP SPRING 2021
# Workout Planner
# Group information
* Student 1. Eemil Hyväri, Eemil.Hyvari@student.oulu.fi
* Student 2. Antti Luukkonen, Antti.A.Luukkonen@student.oulu.fi
* Student 3. Oskar Byman, Oskar.Byman@student.oulu.fi

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__

Instructions for running the server:
1. Create database:
    ipython
    In [1]: from workoutplanner import db, create_app
    In [2]: db.create_all(app=create_app())
2. Run the server:
    python run.py