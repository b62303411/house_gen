import math

import pygame


class Arrow:
    def __init__(self, cx, cy, nx, ny, length, width, color):
        self.width = int(width)
        self.length = int(length)
        self.color = color
        self.cx = int(cx)
        self.cy = int(cy)
        self.nx = int(nx)
        self.ny = int(ny)

    def draw(self, screen, vp):
        cx, cy = self.cx, self.cy
        nx, ny = self.nx, self.ny
        length, width = self.length, self.width
        color = self.color
        # 3) Calculate the end of the arrow line
        end_x = cx + nx * vp.zoom_factor * length
        end_y = cy + ny * vp.zoom_factor * length

        # 4) Draw the main arrow line
        pygame.draw.line(screen, self.color, (cx, cy), (end_x, end_y), width)

        # 5) Draw an arrowhead (small lines angled ~30° off the main direction)
        arrow_size = 10  # length of each arrowhead side
        arrow_angle_deg = 30  # how wide the arrowhead angle is
        arrow_angle_rad = math.radians(arrow_angle_deg)

        # We'll rotate the normalized vector +/- arrow_angle_rad
        # to get two lines forming the arrowhead
        # Vector rotation formula: (x*cosθ - y*sinθ, x*sinθ + y*cosθ)

        # Left arrowhead direction
        left_dx = nx * math.cos(arrow_angle_rad) - ny * math.sin(arrow_angle_rad)
        left_dy = nx * math.sin(arrow_angle_rad) + ny * math.cos(arrow_angle_rad)

        # Right arrowhead direction (negative angle)
        right_dx = nx * math.cos(-arrow_angle_rad) - ny * math.sin(-arrow_angle_rad)
        right_dy = nx * math.sin(-arrow_angle_rad) + ny * math.cos(-arrow_angle_rad)

        # Convert those directions into the tip coordinates
        left_x = end_x - left_dx * arrow_size
        left_y = end_y - left_dy * arrow_size
        right_x = end_x - right_dx * arrow_size
        right_y = end_y - right_dy * arrow_size

        # Draw lines for the arrowhead
        pygame.draw.line(screen, color, (end_x, end_y), (left_x, left_y), width)
        pygame.draw.line(screen, color, (end_x, end_y), (right_x, right_y), width)
