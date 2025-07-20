# Route Finder Mobile
# RouteFinder.py
# 13 July 2025

# Uses TkInter UI to demo a proper native mobile interface

import tkinter as tk
from tkinter import ttk

from FuzzyNameSearch import find_best_match
# from sqlite_File import load_sql
from RFO_File import load_rfo
from ResourceManager import ResourceManager

# TODO Priority list of improvements / feature additions / fixes etc.
# Move maps to /maps and ensure can still run
# fix sqlite db or continue with rfo files?
# fix map manager to not destroy the sql database
# Refactor and improve login and map management plus history!
# Further code cleanup and refactoring
# Login (keep recents)
# Clip the route to the inner canvas!
# Rotate a map on the screen?
# Double click to select location in start or locate mode?

class RouteFinder:
    """Mobile Interface for Route Finder"""

    def __init__(self, root, rfo_filename):

        # Load data from sql file
        version, map_filename, self.rfo_scale, self.rfo_units, self.network = load_rfo("maps/" + rfo_filename)

        # Resource Manager
        self.resources = ResourceManager(path="assets", default_size=50)

        # Window Geometry
        self.frame = 450, 800
        self.map_size = 410, 760
        self.map_offset = 20, 20

        # Configure main window and canvas
        self.root = root
        self.root.title("Route Finder Mobile")
        self.root.geometry(f"{self.frame[0]}x{self.frame[1]}")
        self.canvas = tk.Canvas(root, width=self.frame[0], height=self.frame[1], bg="gray")
        self.canvas.place(x=0, y=0, anchor=tk.NW)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self.update_display)

        # Create a zoomable map and add it to the view
        self.current_map_image, self.map_scale = self.resources.load_map(
            map_name="maps/" + map_filename,
            dimensions=self.map_size)
        self.map_canvas = self.canvas.create_image(
            self.map_offset[0], self.map_offset[1],
            image=self.current_map_image,
            anchor=tk.NW)
        self.map_zoom = 1.0
        self.map_position = [0, 0]

        # Frame overlay
        self.frame_image = self.resources.load("foreground_image", self.frame[1], self.frame[0])
        self.fg_canvas = self.canvas.create_image(
            0, 0,
            image=self.frame_image,
            anchor="nw")

        # Key bindings and controls
        self.map_drag_start = None
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_map)
        self.root.bind("<KeyPress-+>", self.zoom_in_map)
        self.root.bind("<KeyPress-minus>", self.zoom_out_map)
        self.root.bind("<KeyPress-s>", self.start_mode)
        self.canvas.bind("<Configure>", self.update_display)

        # List of recently selected locations
        self.recent = []

        # Route navigation
        self.node_size = 20
        self.path_size = 6
        self.route = []
        self.route_coordinates = []
        self.route_visible = False
        self.current_route_leg = -1

        # Navigation arrow resource lookup
        self.direction_images = {
            "straight ahead": "arr_f",
            "bear left": "arr_l1",
            "turn left": "arr_l2",
            "cut back left": "arr_l3",
            "bear right": "arr_r1",
            "turn right": "arr_r2",
            "cut back right": "arr_r3",
        }

        #Set initial mode
        self.mode = None
        self.map_mode()

    def add_button(self, tag, image, location, command):
        """Add a clickable image to the canvas."""
        button = self.canvas.create_image(
            location[0], location[1],
            image=image,
            anchor=tk.NW)
        self.canvas.tag_bind(button, "<Button-1>", command, True)
        self.resources.manage_context(
            tag=tag,
            asset=button,
            contexts=['mode'],
            destructor=lambda x: self.canvas.delete(x),
            priority=2)

    def input_location(self):
        """User selection of a location using a drop-down menu of best matches using fuzzy-find."""
        entry = ttk.Entry(self.root, font=("Helvetica", 18))
        self.resources.manage_context(
            tag="entry",
            asset=entry,
            contexts=['mode'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        entry.bind("<KeyRelease>", self.on_text_change)
        entry_window = self.canvas.create_window(
            25, 600,
            anchor="nw",
            window=entry,
            width=400,
            height=36)
        self.resources.manage_context(
            tag="entry_window",
            asset=entry_window,
            contexts=['mode'],
            destructor=lambda x: self.canvas.delete(x),
            priority=1
        )
        result_listbox = tk.Listbox(
            self.root,
            font=("Helvetica", 18),
            height=5)
        self.resources.manage_context(
            tag="listbox",
            asset=result_listbox,
            contexts=['mode'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        result_listbox.bind(
            "<<ListboxSelect>>",
            self.on_item_selected)
        listbox_window = self.canvas.create_window(
            25, 636,
            anchor="nw",
            window=result_listbox,
            width=400)
        self.resources.manage_context(
            tag="listbox_window",
            asset=listbox_window,
            contexts=['mode'],
            destructor=lambda x: self.canvas.delete(x),
            priority=1
        )
        result_listbox.delete(0, tk.END)
        for match in self.recent:
            result_listbox.insert(tk.END, match)
        entry.place(x=25, y=600)
        entry.config(width=35)
        result_listbox.place(x=25, y=636)
        result_listbox.config(width=36)
        entry.focus()

    def route_on(self):
        """Create the route UI elements when navigating a new route."""
        route_ovals = [self.canvas.create_oval(x, y, x + 20, y + 20, fill="orange", outline="black", width=1)
                            for x, y in self.route_coordinates]
        route_lines = [self.canvas.create_line(x, y, x + 20, y + 20, fill="blue", width=6)
                            for x, y in self.route_coordinates]
        self.resources.manage_context(
            tag='route_ovals',
            asset=route_ovals,
            contexts=['mode', 'route_off'],
            destructor=lambda x: [self.canvas.delete(a) for a in x],
            priority=4
        )
        self.resources.manage_context(
            tag='route_lines',
            asset=route_lines,
            contexts=['route_off'],
            destructor=lambda x: [self.canvas.delete(a) for a in x],
            priority=4
        )
        if len(self.route) > 1:
            instruction_background = self.canvas.create_image(
                112, 32,
                image=self.resources.load("dir_rec", 80, 226),
                anchor=tk.NW)
            self.resources.manage_context(
                tag='instruction_background',
                asset=instruction_background,
                contexts=['route_off'],
                destructor=lambda x: self.canvas.delete(x),
                priority=2
            )
            instruction_text_object = self.canvas.create_text(
                123, 37,
                width=207,
                fill='#404040',
                font=('Helvetica Bold', 17),
                text="",
                anchor=tk.NW
            )
            self.resources.manage_context(
                tag='instruction_text_object',
                asset=instruction_text_object,
                contexts=['mode', 'route_off'],
                destructor=lambda x: self.canvas.delete(x),
                priority=1
            )
        self.route_visible = True

    def route_off(self):
        """Clean up the route UI elements."""
        self.current_route_leg = -1
        self.route_visible = False
        self.resources.swtich_context('route_off')
        self.route = []
        self.route_coordinates = []

    def map_mode(self, _event=None):
        """Plain map view mode."""
        self.mode = "map"
        self.resources.swtich_context('mode')
        self.route_off()
        self.add_button(
            tag="flag_sta",
            image=self.resources.load("flag_sta", 50),
            location=(35,710),
            command=self.start_mode)
        self.root.unbind("<KeyPress-period>")
        self.root.unbind("<KeyPress-comma>")
        self.root.bind("<KeyPress-s>", self.start_mode)

    def start_mode(self, _event=None):
        """Enter a location to start navigating from."""
        self.mode = "start"
        self.resources.swtich_context('mode')
        self.route_off()
        self.root.unbind("<KeyPress-s>")
        self.input_location()

    def location_mode(self, location_name, _event=None):
        """Display the selected location in the centre of the map."""
        self.mode = "location"
        self.resources.swtich_context('mode')
        self.add_button(
            tag="flag_sto",
            image=self.resources.load("flag_sto", 50),
            location=(360, 710),
            command=self.map_mode)
        self.add_button(
            tag="flag_fin",
            image=self.resources.load("flag_fin", 50),
            location=(35, 710),
            command=self.destination_mode)
        self.route = [self.network.names.index(location_name)]
        self.route_coordinates = [(self.network.locations[r] * self.map_scale).as_tuple() for r in self.route]
        self.route_on()
        self.move_to(self.route_coordinates[0])
        self.root.bind("<KeyPress-s>", self.destination_mode)
        self.update_display()

    def destination_mode(self, _event=None):
        """Enter a destination location to navigate to."""
        self.mode = "destination"
        self.resources.swtich_context('mode')
        self.root.unbind("<KeyPress-s>")
        self.input_location()

    def navigate_mode(self, location_name, _event=None):
        """Navigate the best route from start to destination."""
        self.mode = "navigate"
        self.resources.swtich_context('mode')
        start = self.route[0]
        self.route_off()
        self.route = self.network.find_best_route(start, self.network.names.index(location_name))
        self.route_coordinates = [(self.network.locations[r] * self.map_scale).as_tuple() for r in self.route]
        self.route_on()
        self.current_route_leg = -1
        self.add_button(
            tag="nav_p",
            image=self.resources.load("nav_p", 50),
            location=(35,710),
            command=self.prev_leg)
        self.add_button(
            tag="nav_n",
            image=self.resources.load("nav_n", 50),
            location=(360, 710),
            command=self.next_leg)
        self.add_button(
            tag="nav_s",
            image=self.resources.load("flag_sto", 50),
            location=(200, 710),
            command=self.map_mode)
        self.move_to(self.route_coordinates[-1])
        self.root.bind("<KeyPress-period>", self.next_leg)
        self.root.bind("<KeyPress-comma>", self.prev_leg)
        self.root.bind("<KeyPress-s>", self.map_mode)
        self.update_display()

    def start_drag(self, event):
        """Record the starting point of dragging."""
        self.map_drag_start = (event.x, event.y)

    def drag_map(self, event):
        """Drag the image around by updating the view position."""
        if self.map_drag_start:
            dx = event.x - self.map_drag_start[0]
            dy = event.y - self.map_drag_start[1]
            self.map_drag_start = (event.x, event.y)

            # Update the view position
            self.map_position[0] = self.map_position[0] - dx
            self.map_position[1] = self.map_position[1] - dy

            self.update_display()

    def zoom_in_map(self, _event=None):
        """Zoom in by increasing the zoom level and updating the display."""
        self.map_zoom *= 1.2  # Increase zoom level by 20%
        self.update_display()

    def zoom_out_map(self, _event=None):
        """Zoom out by decreasing the zoom level and updating the display."""
        self.map_zoom /= 1.2  # Decrease zoom level by 20%
        self.update_display()

    def next_leg(self, _event=None):
        """Move to the next leg of the route"""
        if self.route_visible:
            if self.current_route_leg < len(self.route) - 1:
                self.current_route_leg += 1
            self.move_to(self.route_coordinates[self.current_route_leg])
            self.update_display()

    def prev_leg(self, _event=None):
        """Move to the previous leg of the route"""
        if self.route_visible:
            if self.current_route_leg > -1:
                self.current_route_leg -= 1
            self.move_to(self.route_coordinates[self.current_route_leg])
            self.update_display()

    def move_to(self, location):
        """Move the given location to the centre of the screen."""
        self.map_position = [x * self.map_zoom - o // 2 for x, o in zip(location, self.map_size)]


    def update_display(self, _event=None):
        """Update all active UI elements."""
        # Update the visible section of the map
        map_image, self.map_position = self.resources.map_update(self.map_zoom, self.map_position, self.map_size)
        self.canvas.itemconfig(self.map_canvas, image=map_image)
        self.canvas.coords(self.map_canvas, self.map_offset[0], self.map_offset[1])

        # If the route is visible, draw the route
        if self.route_visible:
            route_ovals = self.resources.get_asset('route_ovals')
            for node_index, node in enumerate(self.route_coordinates):
                highlight = (node_index == self.current_route_leg) or len(self.route) == 1
                start = [x - self.node_size // 2 for x in self.map_point_to_screen_point(node)]
                end = [x + self.node_size // 2 for x in self.map_point_to_screen_point(node)]
                self.canvas.coords(route_ovals[node_index], start + end)
                node_color = "orange"
                if highlight:
                    node_color = "red"
                if node_index == len(self.route) - 1:
                    node_color = "blue"
                self.canvas.itemconfig(route_ovals[node_index], fill=node_color)
            route_lines = self.resources.get_asset('route_lines')
            for route_index, route_leg in enumerate(self.route_coordinates):
                start_point = self.map_point_to_screen_point(route_leg)
                if route_index == len(self.route) - 1:
                    end_point = [start_point[0], start_point[1]]
                    leg_color = "black"
                else:
                    end_point = self.map_point_to_screen_point(self.route_coordinates[route_index + 1])
                    if route_index == self.current_route_leg:
                        leg_color = "red"
                    else:
                        leg_color = "blue"
                self.canvas.coords(route_lines[route_index], start_point[0], start_point[1], end_point[0], end_point[1])
                self.canvas.itemconfig(route_lines[route_index], fill=leg_color)

            # Give directions
            if self.route_visible and len(self.route) > 1:
                self.resources.swtich_context('navigate')
                dir_prev, instr, dist, to_loc, dir_next = self.get_directions()
                prev_arrow = None
                if dir_prev:
                    prev_arrow = self.canvas.create_image(
                        28, 32,
                        image=self.resources.load(self.direction_images[dir_prev], 80),
                        anchor=tk.NW)
                elif self.current_route_leg == 0:
                    prev_arrow = self.canvas.create_image(
                        28, 40,
                        image=self.resources.load("flag_sta", 50),
                        anchor=tk.NW)
                if prev_arrow is not None:
                    self.resources.manage_context(
                        tag='prev_arrow',
                        asset=prev_arrow,
                        contexts=['mode', 'navigate'],
                        destructor=lambda x: self.canvas.delete(x),
                        priority=2
                    )
                next_arrow = None
                if dir_next:
                    next_arrow = self.canvas.create_image(
                        342, 32,
                        image=self.resources.load(self.direction_images[dir_next], 80),
                        anchor=tk.NW)
                elif self.current_route_leg == len(self.route) - 2:
                    next_arrow = self.canvas.create_image(
                        342, 40,
                        image=self.resources.load("flag_fin", 50),
                        anchor=tk.NW)
                if next_arrow is not None:
                    self.resources.manage_context(
                        tag='next_arrow',
                        asset=next_arrow,
                        contexts=['mode', 'navigate'],
                        destructor=lambda x: self.canvas.delete(x),
                        priority=2
                    )
                instruction_text = "\n".join([x for x in [instr, dist, to_loc] if x])
                instruction_text_object = self.resources.get_asset('instruction_text_object')
                self.canvas.itemconfig(instruction_text_object, text=instruction_text)

        # Reorder the active control elements
        self.canvas.lift(self.fg_canvas)
        self.resources.reorder_assets(lambda x: self.canvas.lift(x) if type(x) is int else None)

    def get_directions(self):
        """Get the navigation directions for the current route leg."""
        previous_turn = None
        if len(self.route) > 2 and 0 < self.current_route_leg < len(self.route) - 1:
            nodes = [self.route[self.current_route_leg - 1],
                     self.route[self.current_route_leg],
                     self.route[self.current_route_leg + 1]]
            previous_turn = self.network.turn(nodes)
        next_turn = None
        if len(self.route) > 2 and -1 < self.current_route_leg < len(self.route) - 2:
            nodes = [self.route[self.current_route_leg],
                     self.route[self.current_route_leg + 1],
                     self.route[self.current_route_leg + 2]]
            next_turn = self.network.turn(nodes)
        distance = None
        if 0 <= self.current_route_leg < len(self.route) - 1:
            connection = (self.route[self.current_route_leg], self.route[self.current_route_leg + 1])
            if connection[0] == connection[1]:
                distance = 0
            elif connection in self.network.connections:
                distance = self.network.connections[connection]
        elif self.current_route_leg == -1:
            distance = sum([self.network.connections[(self.route[i], self.route[i+1])]
                            for i in range(len(self.route)-1)])
        distance_text = "" if distance is None else str(int(distance)) + " " + self.rfo_units
        instruction = None
        if self.current_route_leg > len(self.route) - 2:
            instruction = "Arrived"
        place_text = None
        if self.current_route_leg == -1:
            place_text = self.network.names[self.route[-1]]
        elif self.current_route_leg < len(self.route) - 1:
            place_text = self.network.names[self.route[self.current_route_leg + 1]]
        return previous_turn, instruction, distance_text, place_text, next_turn

    def map_point_to_screen_point(self, map_point):
        """Convert a map point to a screen point."""
        x, y = map_point
        nx = x * self.map_zoom - self.map_position[0] + self.map_offset[0]
        ny = y * self.map_zoom - self.map_position[1] + self.map_offset[1]
        return [nx, ny]

    def screen_point_to_map_point(self, screen_point):
        """Convert a screen point to a map point."""
        nx, ny = screen_point
        x = (nx - self.map_offset[0] + self.map_position[0]) / self.map_zoom
        y = (ny - self.map_offset[1] + self.map_position[1]) / self.map_zoom
        return [x, y]

    def on_text_change(self, _event=None):
        """Update the listbox dynamically based on entry text."""
        entry = self.resources.get_asset('entry')
        text = entry.get().lower()
        matches = find_best_match(text, self.network.names, 5)
        list_box = self.resources.get_asset('listbox')
        list_box.delete(0, tk.END)
        for match in matches[:5]:
            list_box.insert(tk.END, match)

    def on_item_selected(self, _event=None):
        """Handle the selection event from the listbox."""
        list_box = self.resources.get_asset('listbox')
        selected_indices = list_box.curselection()
        if selected_indices:
            selected_item = list_box.get(selected_indices[0])
            if selected_item in self.recent:
                i = self.recent.index(selected_item)
                self.recent = self.recent[:i] + self.recent[i + 1:]
            self.recent = ([selected_item] + self.recent)[:5]
            if self.mode == "start":
                self.location_mode(selected_item)
            elif self.mode == "destination":
                self.navigate_mode(selected_item)


if __name__ == "__main__":
    ui = tk.Tk()
    app = RouteFinder(ui, "maps/2023-SS-Campus-Map.rfo")
    ui.mainloop()
