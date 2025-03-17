import pygame

# Initialize Pygame
pygame.init()

WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Interactive Floor Plan Viewer")

# Fonts
font = pygame.font.Font(None, 24)
info_font = pygame.font.Font(None, 18)

class GameObject:
    """Base class for all objects (Walls, Doors, Windows)."""
    def __init__(self, x, y, width, height, obj_id, color=BLACK):
        self.id = obj_id
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.selected = False
        self.rotation = 0  # 0, 90, 180, 270

    def draw(self, screen):
        color = YELLOW if self.selected else self.color
        pygame.draw.rect(screen, color, self.rect)

    def is_hovered(self, mx, my):
        return self.rect.collidepoint(mx, my)

    def snap_to_grid(self):
        self.rect.x = round(self.rect.x / GRID_SIZE) * GRID_SIZE
        self.rect.y = round(self.rect.y / GRID_SIZE) * GRID_SIZE

    def rotate(self):
        """Rotates the object 90 degrees around its center."""
        self.rect.width, self.rect.height = self.rect.height, self.rect.width
        self.rotation = (self.rotation + 90) % 360
class Wall:

    def __init__(self, x, y, width, height, wall_id):
        self.id = wall_id
        self.rect = pygame.Rect(x, y, width, height)  # Defines the rectangle
        self.color = (0, 0, 100)  # Default: Black
        self.selected = False

    def draw(self, screen):
        color = (255, 255, 0) if self.selected else self.color  # Yellow if selected
        pygame.draw.rect(screen, color, self.rect)

    def is_hovered(self, mx, my):
        return self.rect.collidepoint(mx, my)


class FloorDisplay:
    # Game Loop
    running = True
    floorplan_surface = None
    dragging = None
    selected = None
    hovered = None
    walls_collection = []

    def get_rect(self, wall):
        start = wall["start"]
        end = wall["end"]
        x1 = start[0]
        y1 = start[1]
        x2 = end[0]
        y2 = end[1]
        width = abs(x1 - x2)
        height = abs(y1 - y2)
        rect = pygame.Rect(x1, y1, width, height)
        return rect

    def make_wall(self, w):
        start = w["start"]
        end = w["end"]
        id_str = w["id"]
        x1 = start[0]
        y1 = start[1]
        x2 = end[0]
        y2 = end[1]
        largeur = w["width"]
        width = max(largeur, abs(x1 - x2))
        height = max(largeur, abs(y1 - y2))
        e = Wall(min(x1, x2), min(y1, y2), width, height, id_str)
        return e

    def display(self, walls_a, wall_b, floorplan_img):
        self.floorplan_surface = pygame.image.frombuffer(floorplan_img.tobytes(), floorplan_img.shape[1::-1], "BGR")
        for w in walls_a:
            w_o = self.make_wall(w)
            w_o.color = (244, 0, 0)
            self.walls_collection.append(w_o)
        for w in wall_b:
            w_o = self.make_wall(w)
            w_o.color = (123, 123, 0)
            self.walls_collection.append(w_o)
        while self.running:
            screen.fill((255, 255, 255))  # White background
            screen.blit(self.floorplan_surface, (0, 0))  # Draw floor plan image

            mx, my = pygame.mouse.get_pos()
            hovered = None

            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for wall in self.walls_collection:
                        rect = wall.rect

                        if rect.collidepoint(mx, my):
                            self.dragging = wall
                            self.selected = wall
                            offset_x = mx - rect.x
                            offset_y = my - rect.y

                elif event.type == pygame.MOUSEBUTTONUP:
                    self.dragging = None

                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        self.dragging.rect.x = mx - offset_x
                        self.dragging.rect.y = my - offset_y

            # Detect hovered walls
            for wall in self.walls_collection:

                rect = wall.rect

                if rect.collidepoint(mx, my):
                    self.hovered = wall
                    # Draw wall ID
                    text_surface = font.render(str(wall.id), True, (0, 0, 0))
                    screen.blit(text_surface, (wall.rect.x + 10, wall.rect.y - 10))

            # Draw Walls
            for wall in self.walls_collection:
                color = wall.color
                if wall == self.hovered:
                    color = (255, 255, 0)  # Yellow highlight
                elif wall == self.selected:
                    color = (0, 255, 0)  # Green for selected

                pygame.draw.rect(screen, color, wall.rect, 2)  # Outline only



            # Show popup on hover
            if hovered:
                info_text = f"Wall {hovered.id} at {hovered.rect.x}, {hovered.rect.y}"
                info_surface = info_font.render(info_text, True, (0, 0, 0), (255, 255, 255))
                screen.blit(info_surface, (mx + 10, my + 10))

            pygame.display.flip()

        pygame.quit()
