# Route Finder Mobile
# 29 January 2025 20:20

# Implementation of the A-Star heuristic route-finding algorithm
# A-star is a prioritized depth-first search following the path of least-expected cost
# For appropriate heuristics, the graph is 'optimal' in its search efficiency
# https://en.wikipedia.org/wiki/A*_search_algorithm

from typing import Callable


def astar(number_of_nodes: int,
          heuristic_function: Callable[[int], float],
          cost_function: Callable[[int], list[tuple[int, float]]],
          start: int) -> list:
    # number_of_nodes - the total number of nodes in the network
    # heuristic_function - function that takes a node index and returns the expected cost to goal (0 for a goal node)
    # cost_function - function that takes a node index and returns a list of (node, traversal cost) pairs
    #   for each node that can be reached directly in the network
    # start - the index of the start point

    # Create and initialize the all_nodes and goal_nodes lists
    all_nodes: list[dict] = []
    goal_nodes: list[int] = []
    for i in range(number_of_nodes):
        initial_cost = 1000000000
        heuristic_cost = heuristic_function(i)
        if heuristic_cost == 0:
            goal_nodes.append(i)
        all_nodes.append({
            'index': i,
            'parent': None,
            'cost': initial_cost,
            'heuristic': heuristic_cost,
            'total': initial_cost + heuristic_cost,
        })
    if len(goal_nodes) == 0:
        return []
    start_node = all_nodes[start]
    start_node['cost'] = 0
    start_node['total'] = start_node['heuristic']

    # Initialize the open current_node list with the start current_node
    open_nodes: list[int] = [start]

    # Main Algorithm
    # Find the open current_node with the best expected total cost and explore
    # all connections leading from it, adding new all_nodes (or old all_nodes with improved cost)
    # to the open current_node list
    while len(open_nodes) > 0:
        open_nodes.sort(key=lambda node_index: all_nodes[node_index]['total'], reverse=True)
        current_index, open_nodes = open_nodes[0], open_nodes[1:]
        for i, weight in cost_function(current_index):
            if weight == 0 or i == current_index:
                continue
            current_node = all_nodes[current_index]
            next_node = all_nodes[i]
            new_cost = current_node['cost'] + weight
            if new_cost < next_node['cost']:
                next_node['cost'] = new_cost
                next_node['total'] = next_node['heuristic'] + new_cost
                next_node['parent'] = current_index
                if i not in open_nodes and i not in goal_nodes:
                    open_nodes.append(i)

    # Return the optimal route
    end = sorted([(i, all_nodes[i]['total']) for i in goal_nodes], key=lambda x: x[1])[0][0]
    route = [end]
    current = all_nodes[end]
    while current['parent'] is not None:
        route.append(current['parent'])
        current = all_nodes[current['parent']]
    route = route[::-1]
    if route[0] != start:
        return []
    else:
        return route
