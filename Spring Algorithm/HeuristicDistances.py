# ROUTE FINDER
# Loki Leibert 2025
# Code available under GPL3 License

# HeuristicDistances.py
# Version 29 January 2025 20:20

# Creates a 2D map of all_nodes using the network weights and spring-physics
# It represents a best-effort to match distances and connection costs
# It can be used as a heuristic distance for route-finding algorithms
# https://en.wikipedia.org/wiki/Force-directed_graph_drawing

import time

import pygame

from sqlite_File import load_sql, save_sql
from SpringPhysics import update

FILE_NAME = "2023-SS-Campus-Map.sqlite"

# Load the network file and add velocities
version, map_filename, scale, units, network = load_sql(FILE_NAME)
nodes: int = len(network.heuristics)
original_locations = network.locations
network.locations = [x for x in network.heuristics]
network.velocities = None

# How long before we stop updating the physics
spring_adjust_time = 20

# Initialize window
pygame.init()
canvas = pygame.display.set_mode([500, 500])
pygame.display.set_caption(title="Spring Map")

loop_exit = False
cycle_timer = time.time()
elapsed_timer = time.time()
while not loop_exit:

    # USER INTERACTIONS
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            loop_exit = True

    # PHYSICS UPDATE FOR HEURISTIC SPRING MAP
    if time.time() - elapsed_timer < spring_adjust_time:
        time_step = time.time() - cycle_timer
        cycle_timer = time.time()

        network.locations, network.velocities = update(network.locations,
                                                       network.velocities,
                                                       network.connections,
                                                       time_step)

    # RENDER
    canvas.fill('Black')
    network.draw(canvas, weighted_edges=True, recenter_rect=[0, 0, 500, 500])
    pygame.display.flip()

# On Exit Save back to the RFO file
network.heuristics = [x for x in network.locations]
network.locations = original_locations
save_sql(FILE_NAME, scale, units, network, map_filename)
