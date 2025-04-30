# Vector.py
# Version 29 January 2025 20:20

# Simple vector math utilities

import math


def v_fn(fn, vectors):
    return [fn(*vals) for vals in zip(*vectors)]


def v_add(*vectors):
    return v_fn(lambda *v: sum(v), vectors)


def v_sub(v1, v2):
    return v_fn(lambda i, j: i-j, [v1, v2])


def v_mul(*vectors):
    return v_fn(lambda *v: math.prod(v), vectors)


def v_scale(v, magnitude):
    return [i * magnitude for i in v]


def v_len(v):
    return math.sqrt(sum([i * i for i in v]))


def v_par(v, magnitude):
    length = v_len(v)
    if length < 3:
        return [magnitude, 0]
    return [magnitude * i / length for i in v]


def v_turn(v1, v2):
    magnitude = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1]) * math.sqrt(v2[0] * v2[0] + v2[1] * v2[1])
    turn_cos = (v1[0] * v2[0] + v1[1] * v2[1]) / magnitude
    turn_sin = (v1[0] * v2[1] - v1[1] * v2[0]) / magnitude
    return turn_cos, turn_sin


def v_rot(v, turns):
    angle = 2.0 * math.pi * turns
    return [v[0] * math.cos(angle) - v[1] * math.sin(angle), v[0] * math.sin(angle) + v[1] * math.cos(angle)]


def distance(loc1, loc2):
    return math.sqrt((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2)


def fit_rect(image_rect, target_rect, expand=False):
    if image_rect[2] <= target_rect[2] and image_rect[3] <= target_rect[3] and not expand:
        scale = 1
    else:
        scale = min(target_rect[2] / image_rect[2], target_rect[3] / image_rect[3])
    offset = (target_rect[0] + target_rect[2] // 2 - image_rect[0] - image_rect[2] // 2,
              target_rect[1] + target_rect[3] // 2 - image_rect[1] - image_rect[3] // 2)
    return offset, scale


def text_box_size(text, font_size):
    return [len(text) * 0.6 * font_size, font_size]


def point_in_rect(point, rect):
    return rect[0] <= point[0] <= rect[0] + rect[2] and \
        rect[1] <= point[1] <= rect[1] + rect[3]


def select_location(point,  list_of_locations, tolerance=7):
    for i, location in enumerate(list_of_locations):
        if distance(point, location) < tolerance:
            return i
    return None
