import requests

SERVER_URL = "http://localhost:5000"
JSON = "application/json"
MASON = "application/vnd.mason+json"

def get_body(href):
    with requests.Session() as s:
        resp = s.get(SERVER_URL + href)
    body = resp.json()
    return body

def post_item(control):
    pass

def put_item(control):
    pass

def delete_item(control):
    pass

def get_controls(controls):
    b_only_controls_with_title=True

    keys = list(controls.keys())
    control_keys = []
    control_labels = []

    for key in keys:
        if b_only_controls_with_title:
            if "title" in controls[key]:
                control_keys.append(key)
                control_labels.append(controls[key]["title"])
        else:
            control_keys.append(key)
            control_labels.append(key)

    return control_keys, control_labels

def get_items(items):

    item_description = ""

    item_labels = []
    for item in items:
        item_description = ""
        for key in item:
            if key[0] != "@":
                if item_description != "":
                    item_description += ", "
                item_description += key + ": " + str(item[key])
        
        item_labels.append(item_description)


    return item_labels

def main():
    with requests.Session() as s:
        s.headers.update({"Accept": "application/vnd.mason+json"})
    resp = s.get(SERVER_URL + "/api/")
    if resp.status_code != 200:
        print("Unable to access API.")
        return 0
    else:
        body = resp.json()
        current_href = "/api/"
    
    command = 0
    while command != -1:
        #print(current_href)
        body = get_body(current_href)

        print("Options available")
        print(0, "Exit the program")

        ## Get controls for current href
        controls_count = 0
        control_keys = []
        if "@controls" in body:
            control_keys, control_names = get_controls(body["@controls"])
            controls_count = len(control_names)
            for i in range(controls_count):
                print(i + 1, control_names[i])
        
        ## Get items for current href
        items_count = 0
        if "items" in body:
            item_names = get_items(body["items"])
            items_count = len(item_names)
            for i in range(items_count):
                print(i + controls_count + 1, item_names[i])

        while True:
            try:
                command = int(input("Next command: ")) - 1
                if command >= 0 and command < controls_count + items_count:
                    break
            except ValueError:
                command = 0

        command = int(input("Next command: ")) - 1
        
        if command == -1:
            return 0
        if command < controls_count:
            if "method" in body["@controls"][control_keys[command]]:
                method = body["@controls"][control_keys[command]]
                if method == "POST":
                    post_item(body["@controls"][control_keys[command]])
                if method == "PUT":
                    put_item(body["@controls"][control_keys[command]])
                if method == "DELETE":
                    delete_item(body["@controls"][control_keys[command]])
                if method == "GET":
                    current_href = body["@controls"][control_keys[command]]["href"]
            else:
                current_href = body["@controls"][control_keys[command]]["href"]
        else:
            index = command - controls_count
            current_href = body["items"][index]["@controls"]["self"]["href"]


if __name__ == "__main__":
   main()
