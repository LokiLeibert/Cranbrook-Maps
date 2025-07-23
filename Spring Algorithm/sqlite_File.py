# ROUTE FINDER
# Loki Leibert 2025
# Code available under GPL3 License

# sqlite_File.py
# Version 29 January 2025 20:20

# Read and write a data file for the route finder
# Data is stored in a sqlite database in 3 tables
# Info contains a single record with:
#   mapfilename VARCHAR,
#   version VARCHAR,
#   rfo_units VARCHAR,
#   rfo_scale FLOAT
# Nodes contains records with columns:
#   id INTEGER PRIMARY KEY,
#   name VARCHAR,
#   loc_x FLOAT, loc_y FLOAT,
#   heu_x FLOAT, heu_y FLOAT
# Connections contains records with cokumns
#   start_id, end_id, weight

import sqlite3

from Network import Network
from RFO_File import load_rfo

VERSION_CODE = "2025a"
SQLITE_EXTENSION = '.sqlite'
RFO_EXTENSION = '.rfo'


def save_sql(filename, scale, units, network, map_filename):
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS Info')
    cur.execute('DROP TABLE IF EXISTS Nodes')
    cur.execute('DROP TABLE IF EXISTS Connections')
    conn.commit()

    cur.execute('CREATE TABLE Info (mapfilename VARCHAR, version VARCHAR, rfo_units VARCHAR, rfo_scale FLOAT)')
    cur.execute(
        'CREATE TABLE Nodes (id INTEGER PRIMARY KEY, name VARCHAR, loc_x FLOAT, loc_y FLOAT, heu_x FLOAT, heu_y FLOAT)')
    cur.execute('CREATE TABLE Connections (start_id INTEGER, end_id INTEGER, weight FLOAT)')
    conn.commit()

    cur.execute('INSERT INTO Info (mapfilename, version, rfo_units, rfo_scale) values (?, ?, ?, ?)',
                (map_filename, VERSION_CODE, units, scale))

    for i, (name, location, heuristic) in enumerate(zip(network.names, network.locations, network.heuristics)):
        location = location.as_tuple()
        heuristic = heuristic.as_tuple()
        cur.execute('INSERT INTO Nodes (id, name, loc_x, loc_y, heu_x, heu_y) values (?, ?, ?, ?, ?, ?)',
                    (i, name, location[0], location[1], heuristic[0], heuristic[1]))

    for (start_id, end_id), weight in network.connections.items():
        cur.execute('INSERT INTO Connections (start_id, end_id, weight) values (?, ?, ?)',
                    (start_id, end_id, weight))

    conn.commit()
    conn.close()


def load_sql(filename):
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    conn.commit()

    cur.execute('SELECT * FROM Info')
    data = cur.fetchall()
    filename, version, units, scale = data[0]

    cur.execute('SELECT * FROM Nodes')
    data = cur.fetchall()
    nodes = [{'id': i, 'name': n, 'location': (lx, ly), 'heuristic': (hx, hy)}
             for (i, n, lx, ly, hx, hy) in data]

    connections = [[0 for _ in range(len(nodes))] for _ in range(len(nodes))]
    cur.execute('SELECT * FROM Connections')
    data = cur.fetchall()
    for s, e, w in data:
        connections[s][e] = w

    conn.close()
    return version, filename, float(scale), units, Network(nodes, connections)


def rfo_to_sql(filename):
    version, map_filename, scale, units, network = load_rfo(filename + RFO_EXTENSION)
    save_sql(filename + SQLITE_EXTENSION, scale, units, network, map_filename)


def print_sql_contents(filename):
    version, filename, scale, units, network = load_sql(filename)
    print(version, filename, scale, units)
    for n, l, h in zip(network.names, network.locations, network.heuristics):
        print({'name': n, 'location': l, 'heuristic': h})
    for c in network.connections:
        print(c)
