import json
import requests

from requests.auth import HTTPBasicAuth
URL = "http://192.168.33.5:8181/onos/v1/"
user = HTTPBasicAuth('karaf', 'karaf')

# loading json template from file
flow_rule_json = {}
with open("./rule_template.json") as file:
    flow_rule_json = json.load(file)

def convert_to_id(n):
    n = int(n)
    return "of:"+(f"{n:x}".zfill(16))

def send_new_flow(flow, edited_switch):
    res = requests.post(URL + "flows/" + edited_switch, data=json.dumps(flow), auth=user)
    print(f"Wysłanie konfiguracji")
    if (res.ok): print("✔ Wysłano")
    else:
        print("❌ Wystąpił błąd")
        return False

    with open("./rules_output.json", "a") as out_file:
        json.dump(flow, out_file, indent=2)

    return True

def generate_rule(switches, hosts, links, edge=True):
    switch_ids = []
    for switch in switches:
        switch_ids.append(convert_to_id(switch))

    current_link = []
    for link in links["links"]:
        link_tuple = (link["src"]["device"], link["dst"]["device"])
        if sorted(link_tuple) == sorted(switch_ids[0:2]):
            current_link.append({link["src"]["device"]: link["src"]["port"], link["dst"]["device"]: link["dst"]["port"]})
            break
    port_numbers = [current_link[0].get(switch_ids[0]), "1"]
    edited_switch = switch_ids[0]
    
    if not edge:
        for link in links["links"]:
            link_tuple = (link["src"]["device"], link["dst"]["device"])
            if sorted(link_tuple) == sorted(switch_ids[1:3]):
                current_link.append({link["src"]["device"]: link["src"]["port"], link["dst"]["device"]: link["dst"]["port"]})
                break
        
        port_numbers = [current_link[1].get(switch_ids[1]),
                        current_link[0].get(switch_ids[1])]
        edited_switch = switch_ids[1]

    

    # modifying flow rules for each of switches
    flow = flow_rule_json
    flow["deviceId"] = edited_switch

    for host in hosts:
        flow["treatment"]["instructions"][0]["port"] = port_numbers[1]
        flow["selector"]["criteria"][0]["port"] = port_numbers[0]
        flow["selector"]["criteria"][2]["ip"] = f"10.0.0.{host[1:]}/32"
        
        if not send_new_flow(flow, edited_switch):
            return False
        
        port_numbers = port_numbers[::-1]

    return True
