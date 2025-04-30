# Graphical utility to create networks for the route finder app
# Load a map image

import pygame

from sqlite_File import save_sql, load_sql, VERSION_CODE
from UIWidgets import TextInputBox, Map
from Vector import v_add, v_sub, v_scale
from Network import Network

# File Input
SQL_FILENAME = "Database.db"
LOAD_FILE = True

# Default Inputs
DEFAULT_MAP = "2023_SS-Campus-Map.png"
DEFAULT_MAP_SCALE = 1
DEFAULT_UNITS = 'meters'
DEFAULT_SCREEN_HEIGHT = 800

# Initialise
if LOAD_FILE:
    version, map_filename, sql_scale, sql_units, network = load_sql(SQL_FILENAME)
else:
    version = VERSION_CODE
    map_filename = DEFAULT_MAP
    sql_scale = DEFAULT_MAP_SCALE
    sql_units = DEFAULT_UNITS
    network = Network([], [])
map_image = pygame.image.load(map_filename)

aspect_ratio = map_image.get_rect().width / map_image.get_rect().height
width, height = aspect_ratio * DEFAULT_SCREEN_HEIGHT, DEFAULT_SCREEN_HEIGHT

# Initialize the window
pygame.init()
window_size = (width * 2, height)
canvas = pygame.display.set_mode(window_size)
pygame.display.set_caption("Map Maker")

map_widget = Map(map_image, [0, 0, width, height], interactive=True)
image_scale = map_widget.rescale_to_height(height)
network_offset = (width, 0)
network.remap_locations(image_scale / sql_scale, network_offset)
map_widget.markers = [tuple(v_sub(location, network_offset)) for location in network.locations]

# MAIN
drag_start = None
dragging = False
shifting = False
cursor_position = None

loop_exit = False
while not loop_exit:

    # USER EVENTS
    action = None
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            loop_exit = True
        cursor_position = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONUP:
            if drag_start is None or map_widget.select_marker(cursor_position) == drag_start:
                action = {'action': 'select', 'location': cursor_position}
            elif pygame.key.get_mods() & pygame.KMOD_SHIFT:
                action = {'action': 's_connect', 'location': cursor_position}
            else:
                action = {'action': 'connect', 'location': cursor_position}
        if event.type == pygame.MOUSEBUTTONDOWN:
            action = {'action': 'drag', 'location': cursor_position}
        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
            shifting = True
        else:
            shifting = False

    # USER INTERACTIONS
    if action is not None:
        action_location = action['location']
        action_type = action['action']
        if map_widget.receive_click(action_location):
            action['current_node'] = map_widget.select_marker(action_location)
            if action_type == 'select' and action['current_node'] is not None:
                # Remove current_node
                remove_node = action['current_node']
                map_widget.remove_marker(remove_node)
                network.remove_node(remove_node)
                dragging = False
                drag_start = None
            elif action_type == 'select':
                # Add current_node
                network_location = v_add(action_location, network_offset)
                text_box = TextInputBox(network_location, font_size=16, length=60,
                                        background_color="White", text_color="Black", alignment='L',
                                        input_type='A')
                node_name = text_box.activate_modal(canvas)
                network.add_node(node_name, network_location)
                map_widget.add_marker(action_location)
                dragging = False
                drag_start = None
            elif action_type == 'connect' or action_type == 's_connect' and drag_start is not None:
                one_way = action_type == 's_connect'
                drag_end = action['current_node']
                if drag_end is not None:
                    start_location, end_location = network.locations[drag_start], network.locations[drag_end]
                    text_input_location = v_scale(v_add(start_location, end_location), 0.5)
                    text_box = TextInputBox(text_input_location, font_size=16, length=4,
                                            background_color="White", text_color="Black", alignment='C',
                                            input_type='D')
                    input_text = text_box.activate_modal(canvas)
                    weight = 0 if len(input_text) == 0 else int(input_text)
                    network.update_connection(drag_start, drag_end, weight, one_way=one_way)
                dragging = False
                drag_start = None
            elif action_type == 'drag':
                if action['current_node'] is not None:
                    dragging = True
                    drag_start = action['current_node']
                else:
                    dragging = False
                    drag_start = None
        else:
            dragging = False
            drag_start = None

    # RENDERING
    canvas.fill('Black')
    map_widget.draw(canvas)
    network.draw(canvas, [], names='A', weighted_edges=False)

    if dragging:
        pygame.draw.line(canvas, 'Orange' if shifting else 'Green', map_widget.markers[drag_start], cursor_position, 1)

    pygame.display.flip()

# On exit print out the required data structures to copy into the RouteFinder app
network.remap_locations(1.0, v_sub((0, 0), network_offset))
network.remap_locations(sql_scale / image_scale, (0, 0))
network.heuristics_reset()
save_sql(SQL_FILENAME, sql_scale, sql_units, network, map_filename)
pygame.quit()
