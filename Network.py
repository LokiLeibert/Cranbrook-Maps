# Route Finder Mobile
# Network.py
# 29 January 2025

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
