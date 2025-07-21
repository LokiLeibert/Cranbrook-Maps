# Route Finder Mobile
# RouteFinder.py
# 13 July 2025

# Uses TkInter UI to demo a proper native mobile interface

import tkinter as tk

from FuzzyNameSearch import find_best_match
from RFO_File import load_rfo
from ResourceManager import ResourceManager, ContextManager, MapImageManager


class RouteFinder:
    """Mobile Interface for Route Finder"""

    def __init__(self,
                 root,
                 rfo_filename,
                 recents=None,
                 callback=None,
                 username=None,
                 geometry=None):

        # Save the callback function for exit
        self.callback = callback
        if username is None:
            self.username = "?"
        else:
            self.username = username

        # Load data from sql file
        version, map_filename, self.rfo_scale, self.rfo_units, self.network = load_rfo("maps/" + rfo_filename)

        # Resource Manager
        self.resources = ResourceManager(path="ui_components", default_size=50)
        self.components = ContextManager()
        self.scalemap = MapImageManager()

        # Window Geometry
        self.frame = 400, 785
        self.map_size = 360, 745
        self.map_offset = 20, 20

        # Configure main window and canvas
        self.root = root
        self.root.title("Route Finder Mobile")
        if geometry is None:
            self.root.geometry(f"{self.frame[0]}x{self.frame[1]}+0+0")
        else:
            self.root.geometry(geometry)
        self.canvas = tk.Canvas(root, width=self.frame[0], height=self.frame[1], bg="gray")
        self.canvas.place(x=0, y=0, anchor=tk.NW)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self.update_display)

        # Ensure we close cleanly
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create a zoomable map and add it to the view
        self.current_map_image, self.map_scale = self.scalemap.load_map(
            map_name="maps/" + map_filename,
            dimensions=self.map_size)
        self.map_canvas = self.canvas.create_image(
            self.map_offset[0], self.map_offset[1],
            image=self.current_map_image,
            anchor=tk.NW)
        self.map_zoom = 1.0
        self.map_position = [0, 0]

        # Frame overlay
        self.frame_image = self.resources.load("frame", self.frame[1], self.frame[0])
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
        if recents is None:
            self.recent = []
        else:
            self.recent = list(recents)

        # Route navigation
        self.node_size = 20
        self.path_size = 6
        self.route_start_name = None
        self.route_end_name = None
        self.route = []
        self.route_coordinates = []
        self.route_visible = False
        self.current_route_leg = -1

        # Navigation arrow resource lookup
        self.direction_images = {
            "straight ahead": "Screen 4/Straight",
            "bear left": "Screen 4/Slight Left",
            "turn left": "Screen 4/Perp Left",
            "cut back left": "Screen 4/Sharp Left",
            "bear right": "Screen 4/Slight Right",
            "turn right": "Screen 4/Perp Right",
            "cut back right": "Screen 4/Sharp Right",
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
        self.components.manage_context(
            tag=tag,
            asset=button,
            contexts=['mode'],
            destructor=lambda x: self.canvas.delete(x),
            priority=2)

    def route_on(self):
        """Create the route UI elements when navigating a new route."""
        route_lines = [self.canvas.create_line(
            x, y, x + 20, y + 20,
            fill="blue",
            width=6,
        )
            for x, y in self.route_coordinates]
        route_ovals = [self.canvas.create_oval(
            x, y, x + 20, y + 20,
            fill="orange",
            outline="",
            width=1)
                            for x, y in self.route_coordinates]
        self.components.manage_context(
            tag='route_lines',
            asset=route_lines,
            contexts=['route_off'],
            destructor=lambda x: [self.canvas.delete(a) for a in x],
            priority=5
        )
        self.components.manage_context(
            tag='route_ovals',
            asset=route_ovals,
            contexts=['route_off'],
            destructor=lambda x: [self.canvas.delete(a) for a in x],
            priority=4
        )
        if len(self.route) > 1:
            instruction_text_object = self.canvas.create_text(
                110, 90,
                width=250,
                fill='white',
                font=('Helvetica Bold', 22),
                text="",
                anchor=tk.W
            )
            self.components.manage_context(
                tag='instruction_text_object',
                asset=instruction_text_object,
                contexts=['mode', 'route_off'],
                destructor=lambda x: self.canvas.delete(x),
                priority=1
            )
            distance_text_object = self.canvas.create_text(
                110, 690,
                width=207,
                fill='#4375b9',
                font=('Helvetica Bold', 22),
                text="",
                anchor=tk.NW
            )
            self.components.manage_context(
                tag='distance_text_object',
                asset=distance_text_object,
                contexts=['mode', 'route_off'],
                destructor=lambda x: self.canvas.delete(x),
                priority=1
            )
        self.route_visible = True

    def route_off(self):
        """Clean up the route UI elements."""
        self.current_route_leg = -1
        self.route_visible = False
        self.components.switch_context('route_off')
        self.route = []
        self.route_coordinates = []

    def map_mode(self, _event=None):
        """Plain map view mode."""
        self.mode = "map"
        self.components.switch_context('mode')
        self.route_off()
        self.add_button(
            tag="Screen 1/Foreground",
            image=self.resources.load("Screen 1/Foreground", 142, 408),
            location=(-4,642),
            command=self.start_mode)
        if self.username is not None and len(self.username) > 0:
            user_label = self.canvas.create_text(
                347, 703,
                width=250,
                fill='white',
                font=('Helvetica Bold', 22),
                text=self.username[0],
                anchor=tk.W,
                justify=tk.CENTER,
            )
            self.canvas.tag_bind(user_label, "<Button-1>", self.logout, True)
            self.components.manage_context(
                tag="user_label",
                asset=user_label,
                contexts=['mode'],
                destructor=lambda x: self.canvas.delete(x),
                priority=1
            )
        self.root.unbind("<KeyPress-period>")
        self.root.unbind("<KeyPress-comma>")
        self.root.bind("<KeyPress-s>", self.start_mode)

    def start_mode(self, _event=None):
        """Enter a location to start navigating from."""
        self.mode = "start"
        self.components.switch_context('mode')
        self.route_off()
        self.root.unbind("<KeyPress-s>")
        self.add_button(
            tag="Screen 2/Foreground",
            image=self.resources.load("Screen 2/Foreground", 310, 408),
            location=(-4, 475),
            command=lambda e: None)
        if self.username is not None and len(self.username) > 0:
            user_label = self.canvas.create_text(
                339, 533,
                width=250,
                fill='white',
                font=('Helvetica Bold', 22),
                text=self.username[0],
                anchor=tk.W,
                justify=tk.CENTER,
            )
            self.canvas.tag_bind(user_label, "<Button-1>", self.logout, True)
            self.components.manage_context(
                tag="user_label",
                asset=user_label,
                contexts=['mode'],
                destructor=lambda x: self.canvas.delete(x),
                priority=1
            )
        entry = tk.Entry(
            self.root,
            font=("Helvetica", 18),
            background='#e9e9e8',
            borderwidth=0,
            foreground='#404040',
            highlightthickness=0,
        )
        self.components.manage_context(
            tag="entry",
            asset=entry,
            contexts=['mode'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        entry.bind("<KeyRelease>", self.on_text_change)
        result_listbox = tk.Listbox(
            self.root,
            font=("Helvetica", 18),
            foreground='#848a85',
            background='#f7f8f7',
            borderwidth=0,
            height=5)
        self.components.manage_context(
            tag="listbox",
            asset=result_listbox,
            contexts=['mode'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        result_listbox.bind(
            "<<ListboxSelect>>",
            self.on_item_selected)
        result_listbox.delete(0, tk.END)
        for match in self.recent:
            result_listbox.insert(tk.END, match)
        recent_label = tk.Label(
            self.root,
            font=("Helvetica Bold", 14),
            background='#f7f8f7',
            foreground='#848a85',
            borderwidth=0,
            width=22,
            anchor=tk.W,
            text="Recent"
        )
        recent_label.place(x=35, y=560)
        self.components.manage_context(
            tag="recent_label",
            asset=recent_label,
            contexts=['mode', 'typing'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        entry.place(x=65, y=520)
        entry.config(width=22)
        result_listbox.place(x=35, y=618)
        result_listbox.config(width=30)
        entry.focus()

    def location_mode(self, _event=None):
        """Display the selected location in the centre of the map."""
        self.mode = "location"
        self.components.switch_context('mode')
        self.add_button(
            tag="Screen 5/Foreground",
            image=self.resources.load("Screen 5/Foreground", 203, 408),
            location=(-5, 582),
            command=self.destination_mode)
        self.add_button(
            tag="Screen 5/Cancel",
            image=self.resources.load("Cross", 70),
            location=(317, 603),
            command=self.map_mode
        )
        destination_label = tk.Label(
            self.root,
            font=("Helvetica Bold", 22),
            background='#f7f8f7',
            foreground='#4375b9',
            borderwidth=0,
            width=22,
            anchor=tk.W,
            text=self.route_start_name,
        )
        destination_label.place(x=40, y=649)
        self.components.manage_context(
            tag="destination_label",
            asset=destination_label,
            contexts=['mode'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        self.route = [self.network.names.index(self.route_start_name)]
        self.route_coordinates = [(self.network.locations[r] * self.map_scale).as_tuple() for r in self.route]
        self.route_on()
        self.move_to(self.route_coordinates[0])
        self.root.bind("<KeyPress-s>", self.destination_mode)
        self.update_display()

    def start_change_mode(self, _event=None):
        """Change the start location for navigation."""
        self.mode = "start_change"
        self.components.switch_context('mode')
        self.root.unbind("<KeyPress-s>")
        self.add_button(
            tag="Screen 2/Foreground",
            image=self.resources.load("Screen 2/ForegroundStart", 358, 408),
            location=(-4, 427),
            command=lambda e: None)
        if self.username is not None and len(self.username) > 0:
            user_label = self.canvas.create_text(
                339, 533,
                width=250,
                fill='white',
                font=('Helvetica Bold', 22),
                text=self.username[0],
                anchor=tk.W,
                justify=tk.CENTER,
            )
            self.canvas.tag_bind(user_label, "<Button-1>", self.logout, True)
            self.components.manage_context(
                tag="user_label",
                asset=user_label,
                contexts=['mode'],
                destructor=lambda x: self.canvas.delete(x),
                priority=1
            )
        entry = tk.Entry(
            self.root,
            font=("Helvetica", 18),
            background='#e9e9e8',
            borderwidth=0,
            foreground='#404040',
            highlightthickness=0,
        )
        self.components.manage_context(
            tag="entry",
            asset=entry,
            contexts=['mode'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        entry.bind("<KeyRelease>", self.on_text_change)
        result_listbox = tk.Listbox(
            self.root,
            font=("Helvetica", 18),
            foreground='#848a85',
            background='#f7f8f7',
            borderwidth=0,
            height=5)
        self.components.manage_context(
            tag="listbox",
            asset=result_listbox,
            contexts=['mode'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        result_listbox.bind(
            "<<ListboxSelect>>",
            self.on_item_selected)
        result_listbox.delete(0, tk.END)
        for match in self.recent:
            result_listbox.insert(tk.END, match)
        recent_label = tk.Label(
            self.root,
            font=("Helvetica Bold", 14),
            background='#f7f8f7',
            foreground='#848a85',
            borderwidth=0,
            width=22,
            anchor=tk.W,
            text="Recent"
        )
        recent_label.place(x=35, y=560)
        self.components.manage_context(
            tag="recent_label",
            asset=recent_label,
            contexts=['mode', 'typing'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        entry.place(x=65, y=520)
        entry.config(width=22)
        result_listbox.place(x=35, y=618)
        result_listbox.config(width=30)
        entry.focus()

    def destination_mode(self, _event=None):
        """Enter a destination location to navigate to."""
        self.mode = "destination"
        self.components.switch_context('mode')
        self.root.unbind("<KeyPress-s>")
        self.add_button(
            tag="Screen 2/Foreground",
            image=self.resources.load("Screen 2/ForegroundEnd", 358, 408),
            location=(-4, 427),
            command=lambda e: None)
        if self.username is not None and len(self.username) > 0:
            user_label = self.canvas.create_text(
                339, 533,
                width=250,
                fill='white',
                font=('Helvetica Bold', 22),
                text=self.username[0],
                anchor=tk.W,
                justify=tk.CENTER,
            )
            self.canvas.tag_bind(user_label, "<Button-1>", self.logout, True)
            self.components.manage_context(
                tag="user_label",
                asset=user_label,
                contexts=['mode'],
                destructor=lambda x: self.canvas.delete(x),
                priority=1
            )
        entry = tk.Entry(
            self.root,
            font=("Helvetica", 18),
            background='#e9e9e8',
            borderwidth=0,
            foreground='#404040',
            highlightthickness=0,
        )
        self.components.manage_context(
            tag="entry",
            asset=entry,
            contexts=['mode'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        entry.bind("<KeyRelease>", self.on_text_change)
        result_listbox = tk.Listbox(
            self.root,
            font=("Helvetica", 18),
            foreground='#848a85',
            background='#f7f8f7',
            borderwidth=0,
            height=5)
        self.components.manage_context(
            tag="listbox",
            asset=result_listbox,
            contexts=['mode'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        result_listbox.bind(
            "<<ListboxSelect>>",
            self.on_item_selected)
        result_listbox.delete(0, tk.END)
        for match in self.recent:
            result_listbox.insert(tk.END, match)
        recent_label = tk.Label(
            self.root,
            font=("Helvetica Bold", 14),
            background='#f7f8f7',
            foreground='#848a85',
            borderwidth=0,
            width=22,
            anchor=tk.W,
            text="Recent"
        )
        recent_label.place(x=35, y=560)
        self.components.manage_context(
            tag="recent_label",
            asset=recent_label,
            contexts=['mode', 'typing'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        entry.place(x=65, y=520)
        entry.config(width=22)
        result_listbox.place(x=35, y=618)
        result_listbox.config(width=30)
        entry.focus()

    def route_summary_mode(self, _event=None):
        """Summarize the route"""
        self.mode = "route_summary"
        self.components.switch_context('mode')
        self.add_button(
            tag="Screen 3/Foreground",
            image=self.resources.load("Screen 3/Foreground", 394, 408),
            location=(-5, 391),
            command=self.destination_mode)
        self.add_button(
            tag="Screen 3/Cancel",
            image=self.resources.load("Cross", 65),
            location=(318, 414),
            command=self.map_mode,
        )
        self.add_button(
            tag="Screen 3/Blue button",
            image=self.resources.load("Screen 3/Blue button", 80),
            location=(290, 628),
            command=self.navigate_mode
        )
        route = self.network.find_best_route(
            self.network.names.index(self.route_start_name),
            self.network.names.index(self.route_end_name))
        distance = sum([self.network.connections[(route[i], route[i + 1])]
                        for i in range(len(route) - 1)])
        start_label = tk.Label(
            self.root,
            font=("Helvetica Bold", 16),
            background='#e9e9e8',
            foreground='#848a85',
            borderwidth=0,
            width=28,
            anchor=tk.W,
            text=self.route_start_name,
        )
        start_label.bind("<Button-1>",
                         lambda e: self.start_change_mode(e))
        self.components.manage_context(
            tag="start_label",
            asset=start_label,
            contexts=['mode'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        start_label.place(x=75, y=500)
        end_label = tk.Label(
            self.root,
            font=("Helvetica Bold", 16),
            background='#e9e9e8',
            foreground='#848a85',
            borderwidth=0,
            width=28,
            anchor=tk.W,
            text=self.route_end_name,
        )
        end_label.bind("<Button-1>",
                       lambda e: self.destination_mode(e))
        self.components.manage_context(
            tag="end_label",
            asset=end_label,
            contexts=['mode'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        end_label.place(x=75, y=542)
        total_label = tk.Label(
            self.root,
            font=("Helvetica Bold", 22),
            background='white',
            foreground='#4375b9',
            borderwidth=0,
            width=22,
            anchor=tk.W,
            text=str(distance) + " " + self.rfo_units)
        self.components.manage_context(
            tag="total_label",
            asset=total_label,
            contexts=['mode'],
            destructor=lambda x: x.destroy(),
            priority=1
        )
        total_label.config(width=18, height=2)
        total_label.place(x=50, y=645)

    def navigate_mode(self, _event=None):
        """Navigate the best route from start to destination."""
        self.mode = "navigate"
        self.components.switch_context('mode')
        self.route_off()
        self.route = self.network.find_best_route(
            self.network.names.index(self.route_start_name),
            self.network.names.index(self.route_end_name))
        self.route_coordinates = [(self.network.locations[r] * self.map_scale).as_tuple() for r in self.route]
        self.route_on()
        self.current_route_leg = -1
        to_panel = self.canvas.create_image(
            -4, 19,
            image=self.resources.load("Screen 4/Foreground", 765, 408),
            anchor=tk.NW)
        self.components.manage_context(
            tag="to_panel",
            asset=to_panel,
            contexts=['mode'],
            destructor=lambda x: self.canvas.delete(x),
            priority=4
        )
        self.add_button(
            tag="nav_p",
            image=self.resources.load("Screen 4/Prev Button", 80),
            location=(25,663),
            command=self.prev_leg)
        self.add_button(
            tag="nav_n",
            image=self.resources.load("Screen 4/Next button", 80),
            location=(295, 663),
            command=self.next_leg)
        self.add_button(
            tag="nav_s",
            image=self.resources.load("Cross", 65),
            location=(17, 612),
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
        map_image, self.map_position = self.scalemap.map_update(self.map_zoom, self.map_position, self.map_size)
        self.canvas.itemconfig(self.map_canvas, image=map_image)
        self.canvas.coords(self.map_canvas, self.map_offset[0], self.map_offset[1])

        # If the route is visible, draw the route
        if self.route_visible:
            route_ovals = self.components.get_asset('route_ovals')
            for node_index, node in enumerate(self.route_coordinates):
                highlight = (node_index == self.current_route_leg) or len(self.route) == 1
                start = [x - self.node_size // 2 for x in self.map_point_to_screen_point(node)]
                end = [x + self.node_size // 2 for x in self.map_point_to_screen_point(node)]
                self.canvas.coords(route_ovals[node_index], start + end)
                node_color = "#4274ba"
                if highlight:
                    node_color = "#e04040"
                if node_index == len(self.route) - 1:
                    node_color = "#ffe040"
                self.canvas.itemconfig(route_ovals[node_index], fill=node_color)
            route_lines = self.components.get_asset('route_lines')
            for route_index, route_leg in enumerate(self.route_coordinates):
                start_point = self.map_point_to_screen_point(route_leg)
                if route_index == len(self.route) - 1:
                    end_point = [start_point[0], start_point[1]]
                    leg_color = "#404040"
                else:
                    end_point = self.map_point_to_screen_point(self.route_coordinates[route_index + 1])
                    if route_index == self.current_route_leg:
                        leg_color = "#e04040"
                    else:
                        leg_color = "#4274ba"
                self.canvas.coords(route_lines[route_index], start_point[0], start_point[1], end_point[0], end_point[1])
                self.canvas.itemconfig(route_lines[route_index], fill=leg_color)

            # Give directions
            if self.route_visible and len(self.route) > 1:
                self.components.switch_context('navigate')
                dir_prev, instr, dist, to_loc, dir_next = self.get_directions()
                prev_arrow = None
                if dir_prev:
                    prev_arrow = self.canvas.create_image(
                        50, 70,
                        image=self.resources.load(self.direction_images[dir_prev], 50, 35),
                        anchor=tk.NW)
                if prev_arrow is not None:
                    self.components.manage_context(
                        tag='prev_arrow',
                        asset=prev_arrow,
                        contexts=['mode', 'navigate'],
                        destructor=lambda x: self.canvas.delete(x),
                        priority=2
                    )
                next_arrow = None
                if dir_next:
                    next_arrow = self.canvas.create_image(
                        111, 150,
                        image=self.resources.load(self.direction_images[dir_next], 30, 21),
                        anchor=tk.NW)
                if next_arrow is not None:
                    then_image = self.canvas.create_image(
                        7, 116,
                        image=self.resources.load("Screen 4/Then", 105, 163),
                        anchor=tk.NW
                    )
                    self.components.manage_context(
                        tag='then_image',
                        asset=then_image,
                        contexts=['mode', 'navigate'],
                        destructor=lambda x: self.canvas.delete(x),
                        priority=3
                    )
                    self.components.manage_context(
                        tag='next_arrow',
                        asset=next_arrow,
                        contexts=['mode', 'navigate'],
                        destructor=lambda x: self.canvas.delete(x),
                        priority=2
                    )
                instruction_text_object = self.components.get_asset('instruction_text_object')
                self.canvas.itemconfig(instruction_text_object, text=to_loc)
                distance_text_object = self.components.get_asset('distance_text_object')
                self.canvas.itemconfig(distance_text_object, text=dist)

        # Reorder the active control elements
        self.canvas.lift(self.fg_canvas)
        self.components.reorder_assets(lambda x: self.canvas.lift(x) if type(x) is int else None)

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
        self.components.switch_context('typing')
        entry = self.components.get_asset('entry')
        text = entry.get().lower()
        matches = find_best_match(text, self.network.names, 5)
        list_box = self.components.get_asset('listbox')
        list_box.delete(0, tk.END)
        for match in matches[:5]:
            list_box.insert(tk.END, match)

    def on_item_selected(self, _event=None):
        """Handle the selection event from the listbox."""
        list_box = self.components.get_asset('listbox')
        selected_indices = list_box.curselection()
        if selected_indices:
            selected_item = list_box.get(selected_indices[0])
            if selected_item in self.recent:
                i = self.recent.index(selected_item)
                self.recent = self.recent[:i] + self.recent[i + 1:]
            self.recent = ([selected_item] + self.recent)[:5]
            if self.mode == "start":
                self.route_start_name = selected_item
                self.route_end_name = None
                self.location_mode()
            elif self.mode == "start_change":
                self.route_start_name = selected_item
                self.route_summary_mode()
            elif self.mode == "destination":
                self.route_end_name = selected_item
                self.route_summary_mode()

    def logout(self, event=None):
        self.components.switch_context('all')
        self.save_history()
        geometry = self.root.geometry()
        self.root.destroy()
        self.root = None
        from Login import LoginApp
        login_root = tk.Tk()
        LoginApp(login_root, geometry=geometry)
        login_root.mainloop()

    def on_closing(self):
        """Handle the window closing event."""
        self.save_history()
        self.root.destroy()
        self.root = None

    def save_history(self):
        if self.callback and self.username is not None and self.username != "?":
            self.callback([x for x in self.recent])




if __name__ == "__main__":
    ui = tk.Tk()
    app = RouteFinder(ui, "2023-SS-Campus-Map.rfo")
    ui.mainloop()
