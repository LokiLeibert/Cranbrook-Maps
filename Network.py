# Network object contains the following information:
#   names of nodes
#   locations of nodes
#   heuristic location of nodes
#   connection weights between nodes

# Important methods
#   draw - renders the network to a canvas using the node locations as pixel locations
#   find_best_route - identifies the least-cost path between two nodes

import pygame

from AStar import astar
from FuzzyNameSearch import find_best_match
from Vector import v_scale, v_turn, v_add, v_par, v_sub, v_rot, text_box_size, distance


class Network:

    def __init__(self, nodes, connection_matrix):
        if nodes is None:
            self.names = []
            self.locations = []
            self.heuristics = []
            self.connections = []
            self.draw_locations = []
        else:
            sorted_nodes = sorted(nodes, key=lambda x: x['id'])
            self.names = [node['name'] for node in sorted_nodes]
            self.locations = [node['location'] for node in sorted_nodes]
            self.heuristics = [node['heuristic'] for node in sorted_nodes]
            self.connections = {(i, j): w for i, row in enumerate(connection_matrix) for j, w in enumerate(row)}
            self.draw_locations = []

    def select_by_location(self, location, tolerance=10):
        for i, n_loc in enumerate(self.locations):
            if distance(location, n_loc) <= tolerance:
                return i
        else:
            return None

    def select_by_name(self, search_text):
        return find_best_match(search_text, self.names)

    def remap_locations(self, scaling_factor, offset):
        self.locations = [(x * scaling_factor + offset[0], y * scaling_factor + offset[1]) for x, y in self.locations]

    def heuristics_reset(self):
        self.heuristics = [x for x in self.locations]

    def add_node(self, name, location):
        self.names.append(name)
        self.locations.append(location)
        self.heuristics.append(location)
        self.draw_locations = []

    def remove_node(self, node_index):
        self.names = self.names[:node_index] + self.names[node_index + 1:]
        self.locations = self.locations[:node_index] + self.locations[node_index + 1:]
        self.heuristics = self.heuristics[:node_index] + self.heuristics[node_index + 1:]
        self.draw_locations = self.draw_locations[:node_index] + self.draw_locations[node_index + 1:]
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
                     heuristic_function=lambda x: distance(self.heuristics[x], self.heuristics[end]),
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
        v1 = v_sub(self.locations[nodes[1]], self.locations[nodes[0]])
        v2 = v_sub(self.locations[nodes[2]], self.locations[nodes[1]])
        turn_cos, turn_sin = v_turn(v1, v2)
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


    def draw_connections(self, canvas, route, segment, weighted_edges=False):
        for (i, j), weight in self.connections.items():
            if i != j and (j, i) in self.connections:
                if i > j:
                    continue
                combined_weight = weight + self.connections[(j, i)]
            else:
                combined_weight = weight
            if combined_weight == 0:
                continue
            line_width = min(4, int((90 / (weight ** 0.67)))) if weighted_edges else 2
            color = 'Gray'
            if segment is not None and i in segment and j in segment and abs(route.index(i) - route.index(j)) == 1:
                color = 'Orange'
            elif i in route and j in route and abs(route.index(i) - route.index(j)) == 1:
                color = 'Blue'
            elif len(route) > 1 and route[0] >= 0 and route[-1] >= 0:
                color = [50, 50, 50]
            pygame.draw.line(canvas, color,
                             self.draw_locations[i],
                             self.draw_locations[j],
                             line_width)

    def draw_connection_labels(self, canvas, names='N'):
        if names != 'A':
            return
        for (i, j), weight in self.connections.items():
            if i == j or weight == 0:
                continue
            start_location, end_location = self.draw_locations[i], self.draw_locations[j]
            center = ((start_location[0] + end_location[0]) // 2, (start_location[1] + end_location[1]) // 2)
            vector = v_par(v_sub(end_location, start_location), 15)
            r_vector = v_par(v_rot(vector, 0.25), 5)
            a_vector = v_par(v_rot(vector, 0.1), 5)
            b_vector = v_par(v_rot(vector, -0.1), 5)
            text_color = 'Pink'
            font_size = 12
            base_font = pygame.font.Font(None, font_size)
            arrow_position = v_add(center, r_vector)
            label = str(weight)
            label_size = text_box_size(label, font_size)
            label_position = v_add(v_add(center, v_scale(r_vector, 3)), v_scale(label_size, -0.5))
            text_surface = base_font.render(str(weight), True, text_color)
            canvas.blit(text_surface, label_position)
            arrow_line = v_sub(arrow_position, vector), v_add(arrow_position, vector)
            pygame.draw.line(canvas, text_color, arrow_line[0], arrow_line[1], 1)
            pygame.draw.line(canvas, text_color, arrow_line[1], v_sub(arrow_line[1], a_vector), 1)
            pygame.draw.line(canvas, text_color, arrow_line[1], v_sub(arrow_line[1], b_vector), 1)

    def draw_nodes(self, canvas, route, segment):
        for i, location in enumerate(self.draw_locations):
            color = 'White'
            if len(route) > 0 and route[0] == i:
                color = 'Green'
            elif len(route) > 1 and route[-1] == i:
                color = 'Red'
            elif segment is not None and i in segment:
                color = 'Orange'
            elif len(route) > 1 and i in route:
                color = 'Blue'
            elif len(route) > 1 and route[0] >= 0 and route[-1] >= 0:
                color = [50, 50, 50]
            pygame.draw.circle(canvas, color, location, 3)

    def draw_names(self, canvas, route, names='N'):
        if names is None or len(names) == 0 or names[0].lower() == 'n':
            return
        color = 'Light Blue'
        font_size = 16
        for i, (node_location, node_text) in enumerate(zip(self.draw_locations, self.names)):
            is_start_end = (len(route) > 0 and i == route[0]) or (len(route) > 1 and i == route[-1])
            is_on_route = (i in route)
            if names[0].lower() == 's' and not is_start_end:
                continue
            if names[0].lower() == 'r' and not is_on_route:
                continue
            est_length = font_size * len(node_text) * 0.67
            center = (node_location[0] - est_length // 2, node_location[1] - int(font_size))
            base_font = pygame.font.Font(None, font_size)
            text_surface = base_font.render(node_text, True, color)
            canvas.blit(text_surface, center)

    def recenter_locations(self, rect):
        if rect is None:
            return self.locations
        rect_center = [rect[0] + rect[2] // 2, rect[1] + rect[3 // 2]]
        center = v_scale(v_add(*[loc for loc in self.locations]), -1.0 / len(self.locations))
        center = v_add(center, rect_center)
        locations = [v_add(location, center) for location in self.locations]
        min_x, min_y = min([loc[0] for loc in locations]), min([loc[1] for loc in locations])
        max_x, max_y = max([loc[0] for loc in locations]), max([loc[1] for loc in locations])
        if (max_x - min_x) > rect[2] or (max_y - min_y) > rect[3]:
            scale_x, scale_y = rect[2] / (max_x - min_x), rect[3] / (max_y - min_y)
            scale = min(scale_x, scale_y)
            locations = [v_scale(loc, scale) for loc in locations]
            center = v_scale(v_add(*[loc for loc in locations]), -1.0 / len(locations))
            center = v_add(center, rect_center)
            locations = [v_add(location, center) for location in locations]
            min_x, min_y = min([loc[0] for loc in locations]), min([loc[1] for loc in locations])
            max_x, max_y = max([loc[0] for loc in locations]), max([loc[1] for loc in locations])
        if min_x < rect[0]:
            locations = [v_add(loc, [rect[0] - min_x, 0]) for loc in locations]
        elif max_x > rect[0] + rect[2]:
            locations = [v_add(loc, [rect[0] + rect[2] - max_x, 0]) for loc in locations]
        if min_y < rect[1]:
            locations = [v_add(loc, [0, rect[1] - min_y]) for loc in locations]
        elif max_y > rect[1] + rect[3]:
            locations = [v_add(loc, [0, rect[1] + rect[3] - max_y]) for loc in locations]
        return locations

    def draw(self, canvas, route=None, segment=None, names='N', weighted_edges=False, recenter_rect=None):
        if route is None:
            route = []
        self.draw_locations = self.recenter_locations(recenter_rect)
        self.draw_connections(canvas, route, segment, weighted_edges)
        self.draw_nodes(canvas, route, segment)
        self.draw_names(canvas, route, names)
        self.draw_connection_labels(canvas, names)
