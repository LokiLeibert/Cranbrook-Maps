# Route Finder Mobile
# ResourceManager.py
# 13 July 2025

from PIL import Image, ImageTk

class ContextManager:
    """Class that manages the lifetime of UI assets"""
    def __init__(self):
        self.context_assets = dict()

    def manage_context(self, tag, asset, contexts, destructor, priority=99):
        """Manages the lifetime of UI assets across mode changes and other context changes."""
        if tag in self.context_assets or tag == 'all':
            old_asset = self.context_assets[tag]['asset']
            self.context_assets[tag]['destructor'](old_asset)
        self.context_assets[tag] = {
            'asset': asset,
            'destructor': destructor,
            'contexts': contexts,
            'priority': priority
        }

    def switch_context(self, context):
        """Switches the current context and deletes assets no longer required."""
        for tag, info in self.context_assets.items():
            if context in info['contexts'] or context == 'all':
                self.context_assets[tag]['destructor'](info['asset'])
                self.context_assets[tag] = {
                    'asset': None,
                    'destructor': lambda x: None,
                    'contexts': [],
                    'priority': 99
                }

    def get_asset(self, tag):
        """Returns a managed asset if it is still valid, otherwise returns None."""
        if tag in self.context_assets:
            return self.context_assets[tag]['asset']
        else:
            return None

    def reorder_assets(self, reorder_fn):
        """Allows the assets to be ordered based on their priority level."""
        prioritised = sorted(self.context_assets.items(), key=lambda x: x[1]['priority'], reverse=True)
        self.context_assets = dict(prioritised)
        for tag, info in prioritised:
            reorder_fn(info['asset'])


class ResourceManager:
    """Class that manages resources and UI assets. It handles:
    - lazy loading of image assets at different sizes,
    - manages the current zoom level of the map image,
    - manages the context and lifetime of UI assets."""
    def __init__(self, path, default_size=None):
        self.resources = dict()
        self.asset_path = path
        self.default_size = default_size

    def load(self, name, size=None, width=None):
        """Loads an image asset and returns a PhotoImage object"""
        if size is None and self.default_size is not None:
            size = self.default_size
        if width is None:
            width = size
        if (name, size, width) not in self.resources:
            image = Image.open(f"{self.asset_path}/{name}.png")
            if size is not None:
                image = image.resize((size if width is None else width, size), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.resources[(name, size, width)] = photo
        else:
            photo = self.resources[(name, size, width)]
        return photo

class MapImageManager:
    def __init__(self):
        self.original_map = None
        self.current_map = None
        self.map_zoom = 1.0

    def load_map(self, map_name, dimensions):
        """Loads an image asset and returns a PhotoImage object"""
        map_image = Image.open(map_name)
        original_width, original_height = map_image.size
        aspect_ratio = original_width / original_height
        target_width, target_height = dimensions
        if not target_width / target_height > aspect_ratio:
            new_height = target_height
            new_width = int(target_height * aspect_ratio)
        else:
            new_width = target_width
            new_height = int(target_width / aspect_ratio)
        self.original_map = map_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        map_image = ImageTk.PhotoImage(map_image)
        map_scale = new_height / original_height
        self.map_zoom = 1.0
        self.current_map = map_image
        return map_image, map_scale

    def map_update(self, zoom, position, size):
        """Updates the map image when moved or zoomed and returns a PhotoImage object."""
        self.map_zoom = zoom
        new_width = int(self.original_map.width * zoom)
        new_height = int(self.original_map.height * zoom)
        new_map_image = self.original_map.resize((new_width, new_height), Image.Resampling.LANCZOS)
        width, height = size
        x0, y0 = position
        if x0 > new_map_image.width - 30:
            x0 = new_map_image.width - 30
        if y0 > new_map_image.height - 30:
            y0 = new_map_image.height - 30
        position = [x0, y0]
        x1 = x0 + width
        y1 = y0 + height
        cropped_image = new_map_image.crop((x0, y0, x1, y1))
        map_image = ImageTk.PhotoImage(cropped_image)
        self.current_map = map_image
        return map_image, position

