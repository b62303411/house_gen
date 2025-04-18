import pygame


class Opening:
    def __init__(self, center_x, width):
        self.type = "window"
        self.center_x = center_x
        self.bottom_z = 1
        self.width = width
        self.height = 1.3

    def copy(self):
        o = Opening(self.center_x, self.width)
        return o

    def convert_to_scale(self, meter_per_pixel):
        o = self.copy()
        o.center_x = o.center_x*meter_per_pixel
        o.width = o.width * meter_per_pixel
        return o

    def __hash__(self):
        return hash(int(self.center_x))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def to_json(self):
        json_str = {
            'type': self.type,
            'center_x': self.center_x,
            'bottom_z': self.bottom_z,
            'width': self.width,
            'height': self.height
        }
        return json_str

    def corners(self):
        return self.collision_box.calculate_corners()

    def draw(self, screen, vp):
        corners = self.corners()
        corners_ = []
        colour = (55, 255, 0)
        for c in corners:
            cp = vp.convert(c[0], c[1])
            corners_.append(cp)
        size = 2

        pygame.draw.polygon(screen, colour, corners_, size)


