# Route Finder Mobile
# Network.py
# 29 January 2025 20:20

# Network object contains the following information:
#   names of nodes
#   locations of nodes
#   heuristic location of nodes
#   connection weights between nodes

# Important methods
#   draw - renders the network to a canvas using the node locations as pixel locations
#   find_best_route - identifies the least-cost path between two nodes

from AStar import astar
from FuzzyNameSearch import find_best_match
from Vector import Vector


class Network:

    def __init__(self, nodes, connection_matrix):
        self.names: list[str] = []
        self.locations: list[Vector] = []
        self.heuristics: list[Vector] = []
        self.connections: dict = {}
        if nodes is not None:
            sorted_nodes = sorted(nodes, key=lambda x: x['id'])
            self.names = [node['name'] for node in sorted_nodes]
            self.locations = [Vector(*node['location']) for node in sorted_nodes]
            self.heuristics = [Vector(*node['heuristic']) for node in sorted_nodes]
            self.connections = {(i, j): w
                                for i, row in enumerate(connection_matrix)
                                for j, w in enumerate(row) if w != 0}

    def select_by_location(self, location, tolerance=10):
        v_location = Vector(*location)
        for i, n_loc in enumerate(self.locations):
            if n_loc.distance(v_location) <= tolerance:
                return i
        else:
            return None

    def select_by_name(self, search_text):
        return find_best_match(search_text, self.names)

    def remap_locations(self, scaling_factor: float, offset: tuple[int, int]) -> None:
        self.locations = [loc * scaling_factor + Vector(*offset) for loc in self.locations]

    def heuristics_reset(self):
        self.heuristics = [x for x in self.locations]

    def add_node(self, name: str, location: tuple[float, float]):
        self.names.append(name)
        self.locations.append(Vector(*location))
        self.heuristics.append(Vector(*location))

    def remove_node(self, node_index):
        self.names = self.names[:node_index] + self.names[node_index + 1:]
        self.locations = self.locations[:node_index] + self.locations[node_index + 1:]
        self.heuristics = self.heuristics[:node_index] + self.heuristics[node_index + 1:]
        self.connections = {(i - (1 if i > node_index else 0), j - (1 if j > node_index else 0)): w
                            for ((i, j), w) in self.connections.items()
                            if i != node_index and j != node_index}

    def update_connection(self, start_index, end_index, weight, one_way=False):
        if weight == 0:
            if (start_index, end_index) in self.connections:
                self.connections.pop((start_index, end_index))
            if not one_way and (end_index, start_index) in self.connections:
                self.connections.pop((end_index, start_index))
        else:
            self.connections[(start_index, end_index)] = weight
            if not one_way:
                self.connections[(end_index, start_index)] = weight

    def matrix(self):
        new_matrix = [[0 for _ in range(len(self.locations))] for _ in range(len(self.locations))]
        for (i, j), weight in self.connections.items():
            new_matrix[i][j] = weight
        return new_matrix

    def find_best_route(self, start, end):
        return astar(number_of_nodes=len(self.heuristics),
                     heuristic_function=lambda x: self.heuristics[x].distance(self.heuristics[end]),
                     cost_function=lambda x: [(j, w) for ((i, j), w) in self.connections.items() if i == x],
                     start=start)

    def route_cost(self, route, start, end):
        if start not in route or end not in route or route.index(start) > route.index(end):
            return None
        segment = route[route.index(start):route.index(end)+1]
        cost = 0
        for i, j in zip(segment[:-1], segment[1:]):
            if (i, j) not in self.connections:
                return None
            cost += self.connections[(i, j)]
        return cost

    def turn(self, nodes):
        v1: Vector = self.locations[nodes[1]] - self.locations[nodes[0]]
        v2: Vector = self.locations[nodes[2]] - self.locations[nodes[1]]
        turn_cos, turn_sin = v1.turn_angle(v2)
        if turn_cos > 0.98:
            direction = 'ahead'
        elif turn_sin > 0:
            direction = 'right'
        else:
            direction = 'left'
        if turn_cos > 0.98:
            angle = 'straight'
        elif turn_cos > 0.78:
            angle = 'bear'
        elif turn_cos > -0.85:
            angle = 'turn'
        else:
            angle = 'cut back'
        return angle + ' ' + direction

    def recenter_locations(self, rect):
        if rect is None:
            return self.locations
        rect_center: Vector = Vector(rect[0], rect[1]) + Vector(rect[2], rect[3]) // 2
        center: Vector = sum([loc for loc in self.locations], start=Vector(0, 0)) * (-1.0 / len(self.locations))
        center = center + rect_center
        locations: list[Vector] = [location + center for location in self.locations]
        min_x, max_x, min_y, max_y = bounds([location.as_tuple() for location in locations])
        if (max_x - min_x) > rect[2] or (max_y - min_y) > rect[3]:
            scale_x, scale_y = rect[2] / (max_x - min_x), rect[3] / (max_y - min_y)
            scale = min(scale_x, scale_y)
            locations = [loc * scale for loc in locations]
            center = sum([loc for loc in locations], start=Vector(0, 0)) * (-1.0 / len(locations))
            center = center + rect_center
            locations = [location + center for location in locations]
            min_x, max_x, min_y, max_y = bounds([location.as_tuple() for location in locations])
        if min_x < rect[0]:
            locations = [loc + Vector(rect[0] - min_x, 0) for loc in locations]
        elif max_x > rect[0] + rect[2]:
            locations = [loc + Vector(rect[0] + rect[2] - max_x, 0) for loc in locations]
        if min_y < rect[1]:
            locations = [loc + Vector(0, rect[1] - min_y) for loc in locations]
        elif max_y > rect[1] + rect[3]:
            locations = [loc + Vector(0, rect[1] + rect[3] - max_y) for loc in locations]
        return locations
