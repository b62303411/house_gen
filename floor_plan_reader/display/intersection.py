import pygame


class Intersection:
    def __init__(self, simulation):
        self.simulation = simulation

    def draw(self, screen, vp):
        for p in self.simulation.get_intersections():
            (ix, iy) = p.point

            # Transform/scale
            cx, cy = vp.convert(ix, iy)

            # Draw a yellow circle (radius=6 as an example)
            pygame.draw.circle(screen, (255, 255, 0), (cx, cy), 6)

            # Draw a black cross inside the circle
            # Let's define a small "arm" size, say half the circle radius:
            arm = 4

            # Horizontal segment of the cross
            pygame.draw.line(screen, (0, 0, 0), (cx - arm, cy), (cx + arm, cy), 2)
            # Vertical segment of the cross
            pygame.draw.line(screen, (0, 0, 0), (cx, cy - arm), (cx, cy + arm), 2)
