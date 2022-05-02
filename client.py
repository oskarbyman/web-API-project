import requests

SERVER_URL = "http://localhost:5000"
JSON = "application/json"
MASON = "application/vnd.mason+json"

def check_response(resp):
    """
    Print reason for failed request

        Parameters:
            resp (requests response): Recieved response
        
    """

    if resp.ok:
        return True
    if resp.status_code == 400:
        print("Error: Bad request (Something went wrong, you shouldn't see this!)")
    if resp.status_code == 404:
        print("Error: Resource not found")
    if resp.status_code == 405:
        print("Error: Method not allowed (Something went wrong, you shouldn't see this!)")
    if resp.status_code == 409:
        print("Error: Resource already exists")
    if resp.status_code == 415:
        print("Error: Unsupported media type (Something went wrong, you shouldn't see this!)")
    return False


def get_body(s, href):
    """
    Request JSON / MASON from current href

        Parameters:
            s (requests session): Current session
            href (str): Selected href
        
        Returns:
            body (dict): Recieved JSON document
    """

    #with requests.Session() as s:
    resp = s.get(SERVER_URL + href)
    if not check_response(resp):
        return None
    body = resp.json()
    return body

def post_item(s, control):
    """
    Add item to collection

        Parameters:
            s (requests session): Current session
            control (dict): Selected hypermedia control
        
        Returns:
            href (str): Next href
    """

    href = control["href"]
    headers={
        'Content-type':'application/json', 
        'Accept':'application/json'
    }

    schema = control["schema"]
    properties = fill_schema(schema) 
    resp = s.post(SERVER_URL + href, json=properties, headers=headers)

    if not check_response(resp):
        return href

    if "Location" in resp.headers:
        href = resp.headers["Location"]

    return href

def put_item(s, control):
    """
    Update item with new data

        Parameters:
            s (requests session): Current session
            control (dict): Selected hypermedia control
        
        Returns:
            href (str): Next href
    """

    href = control["href"]
    headers={
        'Content-type':'application/json', 
        'Accept':'application/json'
    }

    schema = control["schema"]
    properties = fill_schema(schema)
    resp = s.put(SERVER_URL + href, json=properties, headers=headers)

    if not check_response(resp):
        return href

    if "Location" in resp.headers:
        href = resp.headers["Location"]

    return href

def delete_item(s, control, next_href):
    """
    Delete item

        Parameters:
            s (requests session): Current session
            control (dict): Selected hypermedia control
            next_href (str): Next href if deleting is succesful
        
        Returns:
            next_href (str): Next href
    """
    resp = s.delete(SERVER_URL + control["href"])

    if not check_response(resp):
        return control["href"]
    return next_href



def fill_schema(json):
    """
    Fill fields in inputed JSON schema

        Parameters:
            json (dict): recieved JSON schema
        
        Returns:
            filled_schema (dict): Schema filled with user inputed data
    """

    print(f"{json['description']}:")
    properties = json["properties"]
    filled_schema = {}
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
        input_property = get_input(f"{'*' if req else ''} {p} ({type.__name__}): ", type, req)
        if input_property:
            filled_schema.update({p: input_property})
            properties[p] = input_property

    return filled_schema

def get_input(prompt, valueType, required):
    """
    Prompt user for response

        Parameters:
            prompt (str): Text shown to user
            valueType (Type): Wanted input type
            required (Bool): Is the input mandatory
        
        Returns:
            user_input (valueType): Input from user
    """

    while True:
        try:
            user_input = input(prompt)
            if not required and user_input == "":
                return None
            elif required and user_input == "":
                pass
            else:
                return valueType(user_input) 
        except ValueError:
            print("Incorrect input!")

def get_object_info(body):
    """
    Parse info about current object/href if available

        Parameters:
            body (dict): recieved JSON/ MASON response
        
        Returns:
            info (str): Information from current href
    """
    
    info = ""
    for key in body.keys():
        if key[0] != "@" and key != "items":
            if info == "":
                info = key + ": " + str(body[key])
            else:
                info += ", " + key + ": " + str(body[key])
    return info

def get_controls(controls):
    """
    Parse menu items to display from recieved response

        Parameters:
            controls (dict): recieved JSON/ MASON response
        
        Returns:
            control_keys ([str]): Dict keys for recieved response
            control_labels ([str]): Labels for showing items in menu
    """

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
    """
    Parse items excluding hypermedia controls from inputed dict.

        Parameters:
            items (dict): Items from recieved JSON
        
        Returns:
            item_labels ([str]): Labels for foudn items
    """


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
    """
    Logic for simple hypermedia client
    """

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
    while True:
        body = get_body(s, current_href)
        print()
        print("----------------------------------")
        print(f"Current URI: {current_href}")

        ## Print info about object in current URI
        object_info = get_object_info(body)
        if object_info != "":
            print("Current item")
            print("", object_info)

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
                    current_href = delete_item(s, body["@controls"][control_keys[command]], body["@controls"]["up"]["href"])
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
