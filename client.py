import requests

SERVER_URL = "http://localhost:5000"
JSON = "application/json"
MASON = "application/vnd.mason+json"

def get_body(s, href):
    #with requests.Session() as s:
    resp = s.get(SERVER_URL + href)
    body = resp.json()
    return body

def post_item(s, control):
    #print(control)
    href = control["href"]
    headers={
        'Content-type':'application/json', 
        'Accept':'application/json'
    }

    schema = control["schema"]
    #print(control["schema"])
    properties = fill_schema(schema)   #control["schema"]["properties"]
    print(properties)
    resp = s.post(SERVER_URL + href, json=properties, headers=headers)
    print(f"response: {resp.reason}")
    print(resp.headers["Location"])
    print("#########")
    return resp.headers["Location"]


def put_item(s, control):
    return control["href"]

def delete_item(s, control):
    return control["href"]


def fill_schema(json):
    print(f"{json['description']}:")
    properties = json["properties"]
    for p in json["properties"]:
        req = False
        if p in json["required"]:
            req = True
        type = str
        if json["properties"][p]["type"] == "integer":
            type = int
        #if json["properties"][p]["type"] == "object":
        #    properties[p] = fill_schema(json["properties"][p])
        #    continue
        properties[p] = get_input(f"{'*' if req else ''} {p} ({type.__name__}): ", type)
    return properties

def get_input(prompt, valueType):
    while True:
        try:
            return valueType(input(prompt)) 
        except ValueError:
            print("Incorrect input!")


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
    s = requests.Session()

    #with requests.Session() as s:
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
        body = get_body(s, current_href)
        print("----------------------------------")
        print(f"Current URI: {current_href}")
        print("Options available:")
        print("", 0, "Exit the program")

        ## Get controls for current href
        controls_count = 0
        control_keys = []
        if "@controls" in body:
            control_keys, control_names = get_controls(body["@controls"])
            controls_count = len(control_names)
            for i in range(controls_count):
                print("",i + 1, control_names[i])
        
        ## Get items for current href
        items_count = 0
        if "items" in body:
            print("Items:")
            item_names = get_items(body["items"])
            items_count = len(item_names)
            for i in range(items_count):
                print("",i + controls_count + 1, item_names[i])

        while True:
            try:
                command = int(input("Next command: ")) - 1
                if command >= -1 and command < controls_count + items_count:
                    break
                else:
                    print("Incorrect command!")
            except ValueError:
                print("Incorrect command!")
                command = 0


        if command == -1:
            s.close()
            return 0    
        if command < controls_count:
            if "method" in body["@controls"][control_keys[command]]:
                method = body["@controls"][control_keys[command]]["method"]

                if method == "POST":
                    current_href = post_item(s, body["@controls"][control_keys[command]])
                if method == "PUT":
                    current_href = put_item(s, body["@controls"][control_keys[command]])
                if method == "DELETE":
                    current_href = delete_item(s, body["@controls"][control_keys[command]])
                if method == "GET":
                    current_href = body["@controls"][control_keys[command]]["href"]
            else:
                current_href = body["@controls"][control_keys[command]]["href"]
        else:
            index = command - controls_count
            current_href = body["items"][index]["@controls"]["self"]["href"]
    s.close()


if __name__ == "__main__":
   main()
