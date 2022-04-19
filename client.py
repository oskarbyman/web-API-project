import requests

SERVER_URL = "http://localhost:5000"
JSON = "application/json"
MASON = "application/vnd.mason+json"

def get_body(href):
    with requests.Session() as s:
        resp = s.get(SERVER_URL + href)
    body = resp.json()
    return body

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
    
    command = 1
    while command != -1:
        #print(current_href)
        body = get_body(current_href)

        controls = list(body["@controls"])
        
        #for control in controls[:]:        ## Show only controls that have "title"
        #    if not "title" in body["@controls"][control]:
        #        controls.remove(control)

        print(0, "Exit the program")
        for i in range(len(controls)):
            #print(i + 1,  body["@controls"][controls[command]]["title"]) #Get title from hypermedia when available
            print(i + 1, controls[i])
        
        command = int(input("Next command: ")) - 1
        if command == -1:
            return 0
        current_href = body["@controls"][controls[command]]["href"]

if __name__ == "__main__":
   main()
