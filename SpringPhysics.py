# Simple model of a set of nodes, which repel each other connected by springs

from Vector import *


# Spring Map Physics
repulsion_strength = 20
spring_strength = 20
motion_resistance = 0.2


def update(locations, velocities, connections, time_step):
    new_locations, new_velocities = [x for x in locations], [x for x in velocities]
    for update_node in range(len(locations)):
        acceleration = (0, 0)
        loc = locations[update_node]
        v = velocities[update_node]
        for other_node in range(len(locations)):
            r = v_sub(locations[other_node], loc)
            d = v_len(r)
            if d < 3:
                continue
            # Repulsion force
            strength = -100 / (d * d) * repulsion_strength
            # Spring force
            if (update_node, other_node) in connections:
                weight = connections[(update_node, other_node)]
                if weight > 0:
                    strength += (d - weight) * spring_strength
            acceleration = v_add(acceleration, v_par(r, strength))
        # Air resistance
        acceleration = tuple(v_add(acceleration, v_par(v, - (v_len(v) ** 2) * motion_resistance)))
        # Update node
        new_locations[update_node] = tuple(v_add(loc, v_scale(v, time_step)))
        new_velocities[update_node] = tuple(v_add(v, v_scale(acceleration, time_step)))
    return new_locations, new_velocities
