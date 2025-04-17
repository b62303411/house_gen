import math


def generate_directions_45():
    angles = [math.radians(a) for a in range(0, 360, 45)]
    return [(round(math.cos(a), 6), round(math.sin(a), 6)) for a in angles]

DIRECTIONS_8 = generate_directions_45()