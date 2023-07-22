from collections import defaultdict

class Network():
    def __init__(self):
        self.links = defaultdict(list)
        self.latencies = {}
        self.bandwidths = {}

    def reduce_bw(self, nodes, bw):
        self.bandwidths[nodes] = self.bandwidths.get(nodes) - bw

    def add_link(self, from_node, to_node, latency, bandwidth):
        # Note: assumes edges are bi-directional
        self.links[from_node].append(to_node)
        self.links[to_node].append(from_node)
        self.latencies[(from_node, to_node)] = float(latency.replace("ms", ""))
        self.latencies[(to_node, from_node)] = float(latency.replace("ms", ""))
        self.bandwidths[(from_node, to_node)] = bandwidth
        self.bandwidths[(to_node, from_node)] = bandwidth

    def load_links(self, links):
        for link in links:
            self.add_link(*link)

    def load_links_from_dict(self, links):
        for link in links:
            # converting indexes to match naming scheme
            params = list(link.values())
            params[0] += 1
            params[1] += 1
            self.add_link(*params)

    def plan_route(self, initial, end, desiredBw, mode="shortest"):
        best_path = self.find_path(initial, end, mode)
        if best_path[1] >= desiredBw:
            print("Przydzielono pełną przepustowość")
            for i, _ in enumerate(best_path[0][:-1]):
                self.reduce_bw((best_path[0][i], best_path[0][i+1]), desiredBw)
                self.reduce_bw((best_path[0][i+1], best_path[0][i]), desiredBw)
        elif best_path[1] >= desiredBw * 0.75:
            print(f"Przydzielono niepełną przepustowość {best_path[1]}Mbps ({best_path[1]/desiredBw*100}%)")
            for i, _ in enumerate(best_path[0][:-1]):
                self.reduce_bw((best_path[0][i], best_path[0][i+1]), desiredBw)
                self.reduce_bw((best_path[0][i+1], best_path[0][i]), desiredBw)
        else:
            print(f"Brak połączenia umożliwiającego przesłania 75% takiego strumienia")
            return False

        return best_path


    def find_path(self, initial, end, mode="shortest"):
        default_value = 0
        weight = self.latencies
        current_weight = lambda a, b : a + b
        choose_path = lambda a, b: a > b
        choose_best = lambda a: min(a, key=lambda k: a[k][1])
        if mode == "thickest":
            default_value = float('inf')
            weight = self.bandwidths
            current_weight = lambda a, b : min(a, b)
            choose_path = lambda a, b: a < b
            choose_best = lambda a: max(a, key=(lambda k: a[k][1]))
        elif mode != "shortest":
            return "There is not a mode like that"

        weight_paths = {initial: (None, default_value)}
        current_node = initial
        visited = set()


        while current_node != end:
            visited.add(current_node)
            destinations = self.links[current_node]
            weight_to_current_node = weight_paths[current_node][1]

            for next_node in destinations:
                cweight = current_weight(weight[(current_node, next_node)], weight_to_current_node)
                if next_node not in weight_paths:
                    weight_paths[next_node] = (current_node, cweight)
                else:
                    current_best_weight = weight_paths[next_node][1]
                    if choose_path(current_best_weight, cweight):
                        weight_paths[next_node] = (current_node, cweight)

            next_destinations = {node: weight_paths[node] for node in weight_paths if node not in visited}
            if not next_destinations:
                return "Route Not Possible"
            # next node is the destination with the lowest weight
            current_node = choose_best(next_destinations)

        # Work back through destinations in thickest path
        path = []
        while current_node is not None:
            path.append(current_node)
            next_node = weight_paths[current_node][0]
            current_node = next_node
        # Reverse path
        path = path[::-1]
        return path, weight_paths[end][1]


if __name__ == '__main__':
    links = [
        ('X', 'A', "1", 400),
        ('X', 'B', "1", 10),
        ('Y', 'A', "7", 400),
        ('Y', 'B', "5", 4)
    ]

    test_network = Network()
    test_network.load_links(links)


    print(test_network.find_path('A', 'B'),
     "\n", test_network.find_path('A', 'B', "thickest"))
