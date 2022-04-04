import requests
import yaml
import os.path
import json

SERVER_ADDR = "http://localhost:5000/api"
DOC_ROOT = "./doc/"
DOC_TEMPLATE = {
    "responses": {
        "200": {
            "content": {
                "application/vnd.mason+json": {
                    "example": {}
                }
            }
        }
    }
}



def make_file(url, filepath):
    resp_json = requests.get(SERVER_ADDR + url).json()
    DOC_TEMPLATE["responses"]["200"]["content"]["application/vnd.mason+json"]["example"] = resp_json
    path = os.path.join(DOC_ROOT, filepath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as target:
        target.write(yaml.dump(DOC_TEMPLATE, default_flow_style=False))



def main():
    make_file("/users/", "users/get_collection.yml")
    make_file("/users/Noob/", "users/get_item.yml")
    make_file("/users/Noob/moves/", "moves/get_collection.yml")
    make_file("/users/Noob/moves/Plank/", "moves/get_item.yml")
    make_file("/users/Noob/workouts/", "workouts/get_collection.yml")
    make_file("/users/Noob/workouts/Max Suffering/", "workouts/get_item.yml")
    make_file("/users/Noob/workouts/Max Suffering/moves/", "movelistitems/get_collection.yml")
    make_file("/users/Noob/workouts/Max Suffering/moves/0", "movelistitems/get_item.yml")

if __name__ == "__main__":
    main()