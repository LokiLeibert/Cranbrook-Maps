# RFO_File.py
# Version 29 January 2025 20:20

# Read and write a data file for the route finder
# Defines the '.rfo' file format for Route Finder Object files
# A sample file is below
"""
# Route Finder Map File
# Version 2025a

map_filename = 'sample map 1.png'
scale = 4.0
units = 'meters'
nodes = [
    {'id': 0, 'name': 'Thomas House', 'location': (50.0, 80.0), 'heuristic': (101.2, 32.0)},
    {'id': 1, 'name': 'Reception', 'location': (10.0, 33.3), 'heuristic': (-72.0, 23.0)},
]
connections = [
    [0, 100],
    [100, 0],
]
"""

import re

from Network import Network

VERSION_CODE = "2025a"
valid_versions = ["2025a"]


def save_rfo(filename, scale, units, network, map_filename):
    with open(filename, 'w') as file:
        file.write("# Route Finder Map File\n")
        file.write(f"# Version {VERSION_CODE}\n")
        file.write("\n")
        file.write(f"map_filename = '{map_filename}'\n")
        file.write(f"scale = {scale}\n")
        file.write(f"units = '{units}'\n")
        file.write("nodes = [\n")
        for i, (name, location, heuristic) in enumerate(zip(network.names, network.locations, network.heuristics)):
            file.write(f"    {{'id': {i}, 'name': '{name}', 'location': {tuple([round(x, 1) for x in location])}"
                       f", 'heuristic': {tuple([round(x, 1) for x in heuristic])}}},\n")
        file.write("]\n")
        file.write("connections = [\n")
        for connection_row in network.matrix():
            file.write(f"    {connection_row},\n")
        file.write("]")


def load_rfo(filename):
    with open(filename, 'r') as file:
        data = ''.join([line.strip() for line in file.readlines()])
        p = re.compile(
            r"# Route Finder Map File"
            r"# Version (.*)"
            r"map_filename = '(.*)'"
            r"scale = ([\d.]+)"
            r"units = '(.*)'"
            r"nodes = \[(.*)]"
            r"connections = (.*)"
        )
        match = p.match(data)
        if match is not None:
            version, filename, scale, units, node_text, connections_text = match.groups()
            if version not in valid_versions:
                return None
            nodes = []
            p_node = re.compile(r"'id': (.*), 'name': '(.*)', 'location': \(([^,]*), ([^)]*)\), "
                                r"'heuristic': \(([^,]*), ([^)]*)\)")
            for node_line in node_text.strip('{}').split('},{'):
                node_match = p_node.match(node_line)
                n_id, n_name, n_location_x, n_location_y, n_heuristic_x, n_heuristic_y = node_match.groups()
                nodes.append({
                    'id': int(n_id),
                    'name': n_name,
                    'location': (float(n_location_x), float(n_location_y)),
                    'heuristic': (float(n_heuristic_x), float(n_heuristic_y))
                })
            node_count = len(nodes)
            p_connections = re.compile(r"[\d.]+")
            connections_match = p_connections.findall(connections_text)
            if len(connections_match) != node_count ** 2:
                return None
            connections = [[0 for _ in range(node_count)] for _ in range(node_count)]
            for i in range(node_count):
                for j in range(node_count):
                    connections[i][j] = int(float(connections_match[i * node_count + j]))
            return version, filename, float(scale), units, Network(nodes, connections)
    return None
