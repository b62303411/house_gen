import cv2
import numpy as np
import pygame

from world_factory import WorldFactory
from pygame import font
font.init()
f = font.Font(None, 36)  # Use default font with size 36
class ViewPoint:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.zoom_factor=1
        self.min_zoom = 0.1  # Don’t let it go below 10%
        self.max_zoom = 5.0  # Don’t let it exceed 500%
        self.zoom_speed = 1.1
    def zoom_in(self):
        self.zoom_factor *= self.zoom_speed
        if self.zoom_factor > self.max_zoom:
            self.zoom_factor = self.max_zoom
    def zoom_out(self):
        self.zoom_factor /= self.zoom_speed
        if self.zoom_factor < self.min_zoom:
            zoom_factor = self.min_zoom

    def move_left(self,move_speed):
        self.offset_x -= move_speed
    def move_right(self,move_speed):
        self.offset_x += move_speed
    def convert(self,x,y):
        x =int((x + self.offset_x) * self.zoom_factor)
        y= int((y + self.offset_y) * self.zoom_factor)
        return x,y
    def get_center(self):
        return self.offset_x * self.zoom_factor, self.offset_y * self.zoom_factor
class Simulation:
    def run_ant_simulation(
            image_path,
            threshold=200,  # if pixel >= threshold => empty, else wall
            num_ants=20,
            allow_revisit=False
    ):
        # 1) Load grayscale
        img_gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img_gray is None:
            raise FileNotFoundError(f"Cannot load image: {image_path}")
        wf = WorldFactory()

        # 2) Create grid: 1=empty, 0=wall
        g = (img_gray >= threshold).astype(np.uint8)
        wf.set_grid(g)
        wf.set_num_ants(num_ants)
        world = wf.create_World()
        height, width = world.grid.shape

        # 3) Init Pygame with the *exact* dimensions as the image
        pygame.init()
        # We make a window exactly the size of the image
        screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Ant Demo (Native Resolution + Zoom)")

        clock = pygame.time.Clock()

        # 4) Create a floorplan surface (the base image showing white/black)
        #    Then we won't re-scale it right away; we'll do that each frame based on zoom.
        floorplan_surf = pygame.Surface((width, height))
        for y in range(height):
            for x in range(width):
                if world.grid[y, x] == 1:
                    floorplan_surf.set_at((x, y), (255, 255, 255))  # white => empty
                else:
                    floorplan_surf.set_at((x, y), (0, 0, 0))  # black => wall

        # 7) Zoom parameters
        vp = ViewPoint()


        move_speed = 10

        running = True
        while running:
            clock.tick(120)  # up to 30 FPS

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_LEFT:  # Move left
                        vp.move_left(move_speed)
                    elif event.key == pygame.K_RIGHT:  # Move right
                        vp.move_right(move_speed)
                    elif event.key == pygame.K_UP:  # Move up
                        vp.offset_y -= move_speed
                    elif event.key == pygame.K_DOWN:  # Move down
                        vp.offset_y += move_speed
                elif event.type == pygame.VIDEORESIZE:
                    # If the user resizes the window, we can catch the new size here if needed.
                    # screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    pass
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Mouse wheel up => event.button = 4
                    # Mouse wheel down => event.button = 5
                    if event.button == 4:  # scroll up => zoom in
                        vp.zoom_in()
                    elif event.button == 5:  # scroll down => zoom out
                        vp.zoom_out()

            # --- Update ants (simple example) ---

            for ant in world.agents:
                if ant.alive:
                    ant.run()

                # else: no moves => ant stays put
            if not len(world.candidates) == 0:
                agent = world.candidates.popleft()
                world.agents.append(agent)

            # --- Draw ---
            screen.fill((50, 50, 50))

            # Scale the floorplan based on zoom_factor
            new_w = int(width * vp.zoom_factor)
            new_h = int(height * vp.zoom_factor)
            floorplan_scaled = pygame.transform.smoothscale(floorplan_surf, (new_w, new_h))

            # Blit the scaled floorplan at (0,0)
            screen.blit(floorplan_scaled, vp.get_center())

            # Draw ants (scaled)
            for ant in world.agents:
                if ant.alive:
                    ant.draw(screen, vp)
            # Render the number of agents in the top-left corner
            text_surface = f.render(f"Agents: {len(world.agents)}", True, (255, 255, 0))
            screen.blit(text_surface, (10, 10))  # Position (x=10, y=10)
            pygame.display.flip()

        pygame.quit()
        print("All done!")

    # ------------------------------------------------------------------------------
    # Example usage
    # ------------------------------------------------------------------------------
    if __name__ == "__main__":
        # Provide a path to your image
        run_ant_simulation(
            image_path="dark_tones_only.png",
            threshold=200,
            num_ants=100,
            allow_revisit=True
        )
