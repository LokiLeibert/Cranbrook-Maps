# UI Widget classes
# TextInputBox
# Button
# Map


import pygame

from Vector import point_in_rect, text_box_size, distance


class Widget:
    """Abstract Base Class for all Widgets"""

    def __init__(self, rect, active=False):
        self.rect = rect
        self.active = active

    def receive_click(self, location):
        if point_in_rect(location, self.rect) and self.active:
            return True
        return False

    def draw(self, surface):
        pass


class TextInputBox(Widget):

    digit = "0123456789"
    lower = "abcdefghijklmnopqrstuvwxyz"
    upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    spaces = " _"
    punctuation = ".,'`!-?"
    other = "<>+=~@#$%^&*()[]{}|/"
    foreign = "çṉéèïöüåæ"
    text_any = digit + lower + upper + spaces + punctuation + other + foreign

    input_text_type_codes = {
        'D': digit,
        'T': lower + upper + foreign + spaces,
        'P': punctuation + other,
        'O': other,
        'A': text_any,
    }

    def __init__(self, location, font_size=16, length=40,
                 background_color='White', text_color='Black',
                 alignment='left', input_type='A'):
        self.location = location
        self.font_size = font_size
        self.max_text_length = length
        self.background_color = background_color
        self.text_color = text_color
        self.alignment = alignment
        self.allowed_characters = TextInputBox.input_text_type_codes[input_type]
        box_size = text_box_size('m' * length, font_size)
        horizontal_offset = box_size[0] // 2 if self.alignment == 'C' else 0
        vertical_offset = font_size // 2 if self.alignment == 'C' else 2
        bounding_rect = pygame.Rect(location[0] - horizontal_offset, location[1] - vertical_offset,
                                    box_size[0], box_size[1])
        self.base_font = pygame.font.Font(None, self.font_size)
        self.offset = [font_size // 2, font_size // 8]
        super().__init__(bounding_rect)

    def activate_modal(self, surface):
        input_text = ''
        input_exit = False
        while not input_exit:
            # USER INPUT
            for input_event in pygame.event.get():
                if input_event.type == pygame.QUIT:
                    input_exit = True
                if input_event.type == pygame.MOUSEBUTTONUP:
                    input_exit = True
                if input_event.type == pygame.KEYDOWN:
                    if input_event.unicode in self.allowed_characters and len(input_text) < self.max_text_length:
                        input_text += input_event.unicode
                    elif input_event.key == pygame.K_BACKSPACE and len(input_text) > 0:
                        input_text = input_text[:-1]
                    elif input_event.key == pygame.K_ESCAPE:
                        input_text = ''
                        input_exit = True
                    elif input_event.key == pygame.K_RETURN:
                        input_exit = True

            # RENDER
            pygame.draw.rect(surface, self.background_color, self.rect)
            text_surface = self.base_font.render(input_text, True, 'Black')
            surface.blit(text_surface, (self.rect.x + self.offset[0], self.rect.y + self.offset[1]))
            pygame.display.flip()
        return input_text


class Button(Widget):

    def __init__(self, rect, button_text, font_size=16, default_text='',
                 background_color='White', text_color="Black", selected_color='Light Blue'):
        self.text = button_text
        self.background_color = background_color
        self.font_size = font_size
        self.text_color = text_color
        self.selected_color = selected_color
        self.selected = False
        self.default_text = default_text
        self.base_font = pygame.font.Font(None, font_size)
        super().__init__(rect, True)

    def draw(self, surface):
        text = self.text if len(self.text) > 0 else self.default_text
        background_color = self.background_color if not self.selected else self.selected_color
        pygame.draw.rect(surface, background_color, self.rect)
        text_surface = self.base_font.render(text, True, self.text_color)
        surface.blit(text_surface, [self.rect[0], self.rect[1]])


class Map(Widget):

    def __init__(self, image, map_rect, interactive=False):
        self.image = image
        self.dark = False
        self.markers = []
        super().__init__(map_rect, interactive)

    def rescale_to_height(self, height):
        image_rect = self.image.get_rect()
        scale = height / image_rect.height
        self.image = pygame.transform.scale(self.image, (image_rect.width * scale, image_rect.height * scale))
        return scale

    def select_marker(self, location, tolerance=10):
        for i, marker_location in enumerate(self.markers):
            if distance(location, marker_location) <= tolerance:
                return i
        return None

    def add_marker(self, location):
        self.markers.append(location)

    def remove_marker(self, remove_index):
        self.markers = self.markers[:remove_index] + self.markers[remove_index+1:]

    def draw(self, surface):
        surface.blit(self.image, (0, 0))
        if self.dark:
            transparent_surface = pygame.Surface([self.rect[2], self.rect[3]], pygame.SRCALPHA)
            alpha_value = 185
            color = (0, 0, 10, alpha_value)
            transparent_surface.fill(color)
            surface.blit(transparent_surface, (0, 0))
        for marker in self.markers:
            pygame.draw.rect(surface, 'Red', [marker[0] - 4, marker[1] - 4, 8, 8])
