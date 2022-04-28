# PWP SPRING 2021
# Workout Planner
# Group information
* Student 1. Eemil Hyväri, Eemil.Hyvari@student.oulu.fi
* Student 2. Antti Luukkonen, Antti.A.Luukkonen@student.oulu.fi
* Student 3. Oskar Byman, Oskar.Byman@student.oulu.fi

---
### Instructions for installing the server in a virtual enviroment:
1. Create a virtual enviroment and navigate to a copy of the project
1. Install the project:
    - `python setup.py install` or `pip install .`
1. Restart the enviroment and activate it again
1. Set enviromental variable:
    - Bash: `export FLASK_APP=workoutplanner`
    - CMD: `set FLASK_APP=workoutplanner`
    - Powershell: `$env:FLASK_APP = "workoutplanner"`
1. create a database:
    1. `flask init-db`
    1. `flask gen-testdata` //Optional
1. Run the server:
    - `flask run`
---
### Api entry point: `/api/`
---
### Instructions for testing:
1. Launch local dev server with above instructions
1. Install python requests with: `pip install --upgrade pytest`
1. Run tests with: `python -m pytest`
1. Results are shown in the terminal window
