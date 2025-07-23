# ROUTE FINDER
# Loki Leibert 2025
# Code available under GPL3 License

# SpringPhysics.py
# Version 29 January 2025 20:20

# Simple model of a set of nodes, which repel each other connected by springs

from Vector import Vector


# Spring Map Physics
repulsion_strength = 2
spring_strength = 2
motion_resistance = 0.2


def update(locations: list[Vector], velocities: list[Vector] | None, connections, time_step):
    if velocities is None:
        velocities = [Vector(0, 0) for _ in range(len(locations))]
    new_locations, new_velocities = [x for x in locations], [x for x in velocities]
    for update_node in range(len(locations)):
        acceleration = Vector(0, 0)
        loc = locations[update_node]
        v = velocities[update_node]
        for other_node in range(len(locations)):
            r = locations[other_node] - loc
            d = r.length()
            if d < 0.3:
                continue
            # Repulsion force
            strength = -100 / (d * d) * repulsion_strength
            # Spring force
            if (update_node, other_node) in connections:
                weight = connections[(update_node, other_node)]
                if weight > 0:
                    strength += (d - weight) * spring_strength
            acceleration = acceleration + r.parallel(strength)
        # Air resistance
        acceleration = acceleration + v.parallel(- (v.length() ** 2) * motion_resistance)
        # Update node
        new_locations[update_node] = (loc + (v * time_step))
        new_velocities[update_node] = (v + (acceleration * time_step))
    return new_locations, new_velocities


