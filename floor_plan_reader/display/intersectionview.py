import pygame


class IntersectionView:
    def __init__(self, simulation=None):
        self.simulation = simulation

    def draw_intersections(self,screen,vp, intersections,color=(255, 255, 0)):
        for p in intersections:
            (ix, iy) = p.point

            # Transform/scale
            cx, cy = vp.convert(ix, iy)

            # Draw a yellow circle (radius=6 as an example)
            pygame.draw.circle(screen, color, (cx, cy), 6)

            # Draw a black cross inside the circle
            # Let's define a small "arm" size, say half the circle radius:
            arm = 4

            # Horizontal segment of the cross
            pygame.draw.line(screen, (0, 0, 0), (cx - arm, cy), (cx + arm, cy), 2)
            # Vertical segment of the cross
            pygame.draw.line(screen, (0, 0, 0), (cx, cy - arm), (cx, cy + arm), 2)
    def draw(self, screen, vp):
        self.draw_intersections(screen,vp,self.simulation.get_intersections())

