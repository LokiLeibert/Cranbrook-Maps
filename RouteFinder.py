# Interactive application for finding the optimal route
# between all_nodes in a graph with weighted / directional edges

# KEY (NON UI) MODULES TO DISCUSS
# * AStar route finding algorithm
# * FuzzyNameSearch for matching typed locations
# * SpringMapPhysics for creating a network distance heuristic
# * Network class internal data structure for a route network
# * SQL_FILE permanent data format

# KEY UI MODULES TO DISCUSS
# * UIWidgets - MapWidget, TextInputBox, Button (Widget super class)
# * Vector - manipulation of locations and vectors
# * RouteFinder - main application

import pygame
from sqlite_File import load_sql
from UIWidgets import Button, TextInputBox, Map

# File Input
SQL_FILENAME = "Database.db"

# DEFAULT SETTINGS
DEFAULT_MAP_HEIGHT = 800
DEFAULT_BUTTON_HEIGHT = 18
DEFAULT_BUTTON_FONT_SIZE = 16
START_COLOR_BACKGROUND = (230, 255, 230)
END_COLOR_BACKGROUND = (255, 230, 255)

# Initialize UI, Widgets and Network
version, filename, sql_scale, sql_units, network = load_sql(SQL_FILENAME)
map_image = pygame.image.load(filename)

aspect_ratio = map_image.get_rect().width / map_image.get_rect().height
width, height, button_height = DEFAULT_MAP_HEIGHT * aspect_ratio, DEFAULT_MAP_HEIGHT, DEFAULT_BUTTON_HEIGHT

# Initialize the window
pygame.init()
window_size = width, height + button_height * 2
canvas = pygame.display.set_mode(window_size)
pygame.display.set_caption("Route Finder")

map_widget = Map(map_image, [0, 0, height * aspect_ratio, height])
image_scale = map_widget.rescale_to_height(height)
network.remap_locations(image_scale / sql_scale, (0, 0))

buttons = [
    Button([0, height, width // 2, button_height],
           "", default_text="s=", selected_color=START_COLOR_BACKGROUND, background_color='Gray'),
    Button([width // 2, height, width // 2, button_height],
           "", default_text="e=", selected_color=END_COLOR_BACKGROUND, background_color='Gray'),
    Button([0, height + button_height, width, button_height],
           "", default_text="", selected_color='Orange', background_color='Gray'),
]

# Loop variables
loop_exit: bool = False
clicked_spot: tuple[int, int] | None = None
route_start: int | None = None
route_end: int | None = None
route: list = []
segment: int | None = None
draw_route: list = []
action: str | None = None
update_route: bool = False
update_segment: bool = False
update_buttons: bool = False
navigate_segment: list = []

while not loop_exit:

    # USER INTERACTIONS
    action = None
    clicked_spot = None
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            loop_exit = True
        if event.type == pygame.MOUSEBUTTONUP:
            clicked_spot = pygame.mouse.get_pos()
            if buttons[0].receive_click(clicked_spot):
                action = 'start'
            elif buttons[1].receive_click(clicked_spot):
                action = 'end'
            elif buttons[2].receive_click(clicked_spot):
                if len(route) > 1:
                    if segment is None:
                        action = 'navigate'
                    else:
                        action = 'end navigation'
            else:
                action = 'select'
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                action = 'start'
            elif event.key == pygame.K_e:
                action = 'end'
            elif event.key == pygame.K_g and len(route) > 1:
                action = 'navigate'
            elif (event.key == pygame.K_ESCAPE or event.key == pygame.K_x) and segment is not None:
                action = 'end navigation'
            elif (event.key == pygame.K_RETURN or event.key == pygame.K_RIGHT) and segment is not None:
                action = 'navigate next'
            elif (event.key == pygame.K_BACKSPACE or event.key == pygame.K_LEFT) and segment is not None:
                action = 'navigate prev'

    # INTERACTION UPDATES
    update_route = False
    update_buttons = False
    update_segment = False
    if action == 'select':
        selected = network.select_by_location(clicked_spot)
        clicked_spot = None
        if selected is not None and route_start is not None and route_end is None:
            route_end = selected
            update_route = True
        elif selected is not None:
            route_start, route_end, route = selected, None, []
        else:
            route_start, route_end, route = None, None, []
        update_buttons = True
    elif action == 'start' or action == 'end':
        button_index = 0 if action == 'start' else 1
        location = [buttons[button_index].rect[0], buttons[button_index].rect[1]]
        color = START_COLOR_BACKGROUND if action == 'start' else END_COLOR_BACKGROUND
        text_box = TextInputBox(location, 16, 60, color, 'Black', 'L', 'A')
        input_name = text_box.activate_modal(canvas)
        get_node_index = network.select_by_name(input_name)
        if get_node_index is not None:
            if action == 'start':
                route_start = get_node_index
                update_buttons = True
            else:
                route_end = get_node_index
                update_buttons = True
        if route_start is not None and route_end is not None:
            update_route = True

    if update_route:
        route = network.find_best_route(route_start, route_end)
    if update_buttons:
        for button in buttons:
            button.text, button.selected = "", False
        if route_start is not None:
            buttons[0].text, buttons[0].selected = network.names[route_start], True
        if route_end is not None:
            buttons[1].text, buttons[1].selected = network.names[route_end], True

    if action == 'navigate':
        segment = 0
        update_segment = True
    elif action == 'end navigation' or len(route) == 0:
        segment = None
        update_segment = True
    elif action == 'navigate next' and segment is not None and segment < len(route) - 1:
        segment += 1
        update_segment = True
    elif action == 'navigate prev' and segment is not None and segment > 0:
        segment -= 1
        update_segment = True

    if update_segment or update_route:
        if segment is not None and len(route) > 0 and segment != route[-1] and 0 < segment < len(route) - 1:
            p_turn = network.turn([route[segment - 1], route[segment], route[segment + 1]])
        else:
            p_turn = None
        if segment is not None and 0 <= segment < len(route) - 1 and len(network.names[route[segment]]) > 0:
            p_name = "from " + network.names[route[segment]]
        elif segment is None and len(route) > 1 and len(network.names[route[0]]) > 0:
            p_name = "from " + network.names[route[0]]
        elif segment is not None and segment == len(route) - 1:
            p_name = network.names[route[-1]]
        else:
            p_name = None
        if segment is not None and 0 <= segment < len(route) - 2 and len(network.names[route[segment + 1]]) > 0:
            n_name = "to " + network.names[route[segment + 1]]
        elif segment is None and len(route) > 1 and len(network.names[route[-1]]) > 0:
            n_name = "head towards " + network.names[route[-1]]
        else:
            n_name = None
        if segment is not None and segment < len(route) - 2:
            n_turn = "then " + network.turn([route[segment], route[segment + 1], route[segment + 2]])
        elif segment is not None and segment == len(route) - 2:
            n_turn = "to reach your destination"
        elif segment is not None and segment == len(route) - 1:
            n_turn = "is your destination"
        else:
            n_turn = None
        if segment is not None and segment != len(route) - 1:
            cost_text = ": " + str(network.route_cost(route, route[segment], route[segment+1])) + " " + sql_units
        elif segment is None and len(route) > 1:
            cost_text = ": " + str(network.route_cost(route, route[0], route[-1])) + " " + sql_units
        else:
            cost_text = None
        navigation_text = ' '.join([x for x in [p_turn, p_name, n_name, n_turn, cost_text] if x is not None])
        buttons[2].text = navigation_text
        buttons[2].selected = len(navigation_text) > 0

    if segment is not None and 0 <= segment < len(route) - 1:
        navigate_segment = [route[segment], route[segment+1]]
    else:
        navigate_segment = None

    if route_start is None and route_end is not None:
        draw_route = [-1, route_end]
    elif route_start is not None and route_end is None:
        draw_route = [route_start, -1]
    else:
        draw_route = route

    # RENDER
    canvas.fill('Black')
    map_widget.dark = (route_start is not None and route_end is not None)
    map_widget.draw(canvas)
    network.draw(canvas, route=draw_route, segment=navigate_segment, names='R')
    for button in buttons:
        button.draw(canvas)

    pygame.display.flip()
