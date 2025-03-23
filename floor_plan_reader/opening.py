import pygame


class Opening:
    def __init__(self, id,parent,cb):
        self.id= id
        self.parent = parent
        self.collision_box = cb

    def get_center(self):
        return self.collision_box.get_center()

    def get_world_center(self):
        x1, y1 = self.collision_box.get_center()
        x2, y2 =self.parent.collision_box.get_center()
        return (x1+x2,y1+y2)

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


