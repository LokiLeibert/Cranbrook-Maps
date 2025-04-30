# Read and write a data file for the route finder
# Data is stored in a sqlite database in 3 tables
# Info contains a single record with:
#   mapfilename VARCHAR,
#   version VARCHAR,
#   sql_units VARCHAR,
#   sql_scale FLOAT
# Nodes contains records with columns:
#   id INTEGER PRIMARY KEY,
#   name VARCHAR,
#   loc_x FLOAT, loc_y FLOAT,
#   heu_x FLOAT, heu_y FLOAT
# Connections contains records with cokumns
#   start_id, end_id, weight

import sqlite3
import os

from Network import Network

VERSION_CODE = "2025a"


def save_sql(filename, scale, units, network, map_filename):

    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS Info')
    cur.execute('DROP TABLE IF EXISTS Nodes')
    cur.execute('DROP TABLE IF EXISTS Connections')
    conn.commit()

    cur.execute('CREATE TABLE Info (mapfilename VARCHAR, version VARCHAR, sql_units VARCHAR, sql_scale FLOAT)')
    cur.execute('CREATE TABLE Nodes (id INTEGER PRIMARY KEY, name VARCHAR, loc_x FLOAT, loc_y FLOAT, heu_x FLOAT, heu_y FLOAT)')
    cur.execute('CREATE TABLE Connections (id INTEGER PRIMARY KEY, start_id INTEGER, end_id INTEGER, weight FLOAT)')
    conn.commit()

    cur.execute(f'INSERT INTO Info (mapfilename, version, sql_units, sql_scale) VALUES ("{map_filename}", "{VERSION_CODE}", "{units}", {scale})')

    query = "INSERT INTO Nodes (id, name, loc_x, loc_y, heu_x, heu_y) VALUES "
    firstitem = True
    for id, (name, location, heuristic) in enumerate(zip(network.names, network.locations, network.heuristics)): 
        if not firstitem:
            query += ", "
        firstitem = False
        query += f'({id}, "{name}", {location[0]}, {location[1]}, {heuristic[0]}, {heuristic[1]})'
    query += ";"
    cur.execute(query)

    query = 'INSERT INTO Connections (id, start_id, end_id, weight) VALUES '
    firstitem = True
    for id, ((start_id, end_id), weight) in enumerate(network.connections.items()): 
        if not firstitem:
            query += ', '
        firstitem = False
        query += f'({id}, {start_id}, {end_id}, {weight})'
    query += ';'
    cur.execute(query)

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
    for i, s, e, w in data:
        connections[s][e] = w

    conn.close()
    return version, filename, float(scale), units, Network(nodes, connections)
