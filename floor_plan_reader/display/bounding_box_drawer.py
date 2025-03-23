import pygame


class BoundingBoxDrawer:
    def __int__(self):
        pass

    def draw(self,bb,screen,vp, colour):
        if bb is None:
            return
        corners = bb.corners()
        corners_ = []

        for c in corners:
            cp = vp.convert(c[0], c[1])
            corners_.append(cp)
        pygame.draw.polygon(screen, colour, corners_, 1)