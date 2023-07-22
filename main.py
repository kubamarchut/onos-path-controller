import requests

from requests.exceptions import ConnectTimeout
from requests.auth import HTTPBasicAuth
from link_definitions import link_definitions
from dijkstra import Network
from rule_generator import generate_rule

API = {'url': "http://192.168.33.5:8181/onos/v1/", "user": HTTPBasicAuth('karaf', 'karaf')}

def printpath(path):
    string = f"h{path[0]} <-> "
    for node in path:
        string += f"s{node} <-> "
    else:
        string +=  f"h{node}"
    print("Na trasie:", string)


def clear_output_file():
    with open("./rules_output.json", "w") as out_file:
        out_file.write("")

connections_made = []

def generate_summary():
    print(f"\n\nSkonfigurowano {len(connections_made)} tras dla następujących strumieni:")
    for connection in connections_made:
        print(f"  •", "-".join(connection[:2]),f"{connection[-1]}Mbps")

def create_connection(hosts, bw):
    route = italy_network.plan_route(int(hosts[0][1:]), int(hosts[1][1:]), bw, "thickest")
    if not route:
        return False
    path = route[0]
    result = route[1]
    printpath(path)
    if len(path) < 2:
        print("Podano 2 razy ten sam host")
        return False

    for i, _ in enumerate(path):
        first = i == 0
        last = i == len(path)-1

        if not (first or last):
            nodes = (path[i-1], path[i], path[i+1])
        else:
            if last: i -= 1
            nodes = (path[i], path[i+1])
            if last:
                nodes = nodes[::-1]
                hosts = hosts[::-1]
        
        if not generate_rule(nodes, hosts, links, (first or last)):
            return False
    
    return True

#clearing output file
clear_output_file()
# creating object for the network
italy_network = Network()
italy_network.load_links_from_dict(link_definitions)

print("🔵 Wczytywanie szablonu reguły")

# get port numbers
print("🔵 Wysłanie żądania zwracającego informację o połączeniach w sieci")
try:
    res = requests.get(API['url']+"links", auth=API['user'])
except ConnectTimeout:
    print("❌ Brak połączenia z kontrolerem ONOS")
    exit()

links = res.json()
if res.ok: print("✔ Odebrano informację o łączach")
else: 
    print("❌ Nie wczytano poprawnych danych od kontorlera ONOS")
    exit()


print("Aby skonfigurować połączenie między hostami, podaj ich nazwy i żądaną przepustowość w [Mbps]")
print("np.: h1 h2 300")
print("Aby wyjść wpisz: stop lub wciśnij CRTL-C")

try:
    while True:
        res = input("\npodaj dane nowego połączenia: \n")

        if res.lower() == "stop":
            generate_summary()
            break

        elif len(res.split(" ")) == 3:
            print("🔵 Odczytywanie hostów, dla których tworzone jest łącze")
            hosts = []

            # reading hosts from command line
            res = res.split(" ")
            for ele in res:
                if ele.lower().startswith("h"):
                    hosts.append(ele.lower())

            if len(hosts) != 2 and not res[-1].isnumeric:
                print("Nie podano pary hostow i przepustowości")
                exit()

            else: 
                if create_connection(hosts, float(res[-1])):
                    connections_made.append(res)


except KeyboardInterrupt:
    generate_summary()
