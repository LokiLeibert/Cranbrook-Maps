# ROUTE FINDER
# James Leibert 2025
# Code available under GPL3 License

# Vector.py
# Version 29 January 2025 20:20

# Simple vector class for vertex locations and vector maths


import numpy as np


class Vector:
    def __init__(self, x, y):
        self.array = np.array([x, y])

    @staticmethod
    def _check_vector_type(other):
        if not isinstance(other, Vector):
            raise TypeError('Operation is defined only for type Vector')

    def __add__(self, other):
        self._check_vector_type(other)
        return Vector(*(self.array + other.array))

    def __sub__(self, other):
        self._check_vector_type(other)
        return Vector(*(self.array - other.array))

    def __mul__(self, other):
        if isinstance(other, Vector):
            return Vector(*(self.array * other.array))
        elif isinstance(other, int) or isinstance(other, float):
            return Vector(*(self.array * other))
        else:
            self._check_vector_type(other)

    def __truediv__(self, other):
        if isinstance(other, Vector):
            return Vector(*(self.array / other.array))
        elif isinstance(other, int) or isinstance(other, float):
            return Vector(*(self.array / other))
        else:
            self._check_vector_type(other)

    def __floordiv__(self, other):
        if isinstance(other, Vector):
            return Vector(*(self.array // other.array))
        elif isinstance(other, int) or isinstance(other, float):
            return Vector(*(self.array // other))
        else:
            self._check_vector_type(other)

    def dot(self, other):
        self._check_vector_type(other)
        return np.dot(self.array, other.array)

    def s_cross(self, other):
        self._check_vector_type(other)
        return self.array[0] * other.array[1] - self.array[1] * other.array[0]

    def length(self):
        return np.sqrt(np.sum(self.array ** 2))

    def unit_vector(self):
        return Vector(*(self.array / self.length()))

    def rotate_by_angle(self, angle_in_radians):
        rotation_matrix = np.array([[np.cos(angle_in_radians), -np.sin(angle_in_radians)],
                                    [np.sin(angle_in_radians), np.cos(angle_in_radians)]])
        return Vector(*(rotation_matrix @ self.array))

    def rotate_by_turns(self, turns):
        return self.rotate_by_angle(turns * 2.0 * np.pi)

    def turn_angle(self, other):
        self._check_vector_type(other)
        magnitude = self.length() * other.length()
        turn_cos = self.dot(other) / magnitude
        turn_sin = self.s_cross(other) / magnitude
        return turn_cos, turn_sin

    def parallel(self, length):
        this_length = self.length()
        if this_length < .03:
            return Vector(length, 0)
        return Vector(*(self.array / this_length * length))

    def distance(self, other):
        self._check_vector_type(other)
        return (self - other).length()

    def in_rect(self, rect):
        return rect[0] <= self.array[0] <= rect[0] + rect[2] and \
            rect[1] <= self.array[1] <= rect[1] + rect[3]

    def as_tuple(self):
        return float(self.array[0]), float(self.array[1])

    def __str__(self):
        return f"Vector({self.array[0]}, {self.array[1]})"

    def __repr__(self):
        return str(self)
