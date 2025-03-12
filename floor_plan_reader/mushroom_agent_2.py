from random import random

import pygame

from floor_plan_reader.agent import Agent
from floor_plan_reader.cell import Cell


class Mushroom(Agent):

    def __init__(self, start_x, start_y, world, mush_id=1):
        super().__init__(mush_id)
        self.world = world
        self.branch_complete = False
        # We'll keep a set of root cells
        self.root_cells = set()
        self.core_cells = set()
        self.root_cells.add(Cell(start_x, start_y))

        # For rendering and bounding box
        self.center_x = float(start_x)
        self.center_y = float(start_y)
        self.min_x = start_x
        self.max_x = start_x
        self.min_y = start_y
        self.max_y = start_y
        self.x = start_x
        self.y = start_y
        self.alive = True
        self.braches = []

    def ray_trace(self):
        min_x = self.center_x - self.scan_for_blockage(-1, 0)
        max_x = self.center_x + self.scan_for_blockage(1, 0)
        min_y = self.center_y - self.scan_for_blockage(0, -1)
        max_y = self.center_y + self.scan_for_blockage(0, 1)
        return min_x, max_x, min_y, max_y

    def find_cell(self,cell_):
        return next((obj for obj in self.root_cells if isinstance(obj, Cell) and obj == cell_), None)

    def find_cell_in_core(self,cell_):
        return next((obj for obj in self.core_cells if isinstance(obj, Cell) and obj == cell_), None)
    def detect_if_all_visited(self):
        for c in self.core_cells:
            if not c.is_visited:
                return

        self.branch_complete = True
    def scan_bounding_box(self):
        cell_to_move = []
        for y in range(int(self.max_y), int(self.min_y) - 1, -1):  # Scanning from top (max_y) to bottom (min_y)
            for x in range(int(self.min_x), int(self.max_x) + 1):  # Scanning from left (min_x) to right (max_x)
                cell = Cell(x, y)
                if cell not in self.core_cells:
                    #print ("test")
                    cell.is_root = True
                    self.core_cells.add(cell)
                    collide = self.collidepoint(x,y)
                    #print(collide)

                if cell in self.root_cells:
                    cell_to_move.append(cell)
                    #self.root_cells.remove(cell)
                    #self.core_cells.add(cell)

                actual_cell = self.find_cell_in_core(cell)
                if not actual_cell.is_visited:
                    actual_cell.is_visited=True
                    # detect stem
                    neighbors = self.get_neighbors_8(cell.x, cell.y)
                    for (nx, ny) in neighbors:
                        collide = self.collidepoint(nx,ny)
                        if not collide:
                            stem = self.find_cell(Cell(nx,ny))
                            if stem is not None:
                                if not stem.is_stem:
                                    stem.is_stem = True
                                    if self.world.collide_with_any(self,nx,ny):
                                        stem.is_visited= True
                                        stem.sprouted = True
                                        print("found stem dead")
                                    else:
                                        print("found stem")
        if cell in cell_to_move:
            self.root_cells.remove(cell)
            # self.root_cells.remove(cell)

    def create_branche(self, x, y):
        branche = Mushroom(x, y, self.world, random.randint(1, 2**31 - 1))
        self.braches.append(branche)
        self.world.candidates.append(branche)
        # self.world.agents.append(branche)

    def grow_branch(self):
        for cell in self.root_cells:
            rx = cell.x
            ry = cell.y
            if cell.is_stem:
                if not cell.sprouted:
                    cell.sprouted = True
                    if not self.world.collide_with_any(self, rx, ry):
                        self.create_branche(rx, ry)
                        return
                    else:
                        cell.collided = True
            else:
                pass

            #if self.collidepoint(rx, ry):
            #    cell.is_root = True
            #    pass
            #else:
            #    if not self.world.collide_with_any(self, rx, ry):
            #        neighbors = self.get_neighbors_8(rx, ry)
            #        for (nx, ny) in neighbors:
            #            if self.collidepoint(nx, ny):
            #                if (len(self.braches) < 10):
            #                    cell.is_stem = True
            #                    self.create_branche(rx, ry)
            #                return
            #        return

    def run(self):
        if self.branch_complete:
            return
        """
        Each frame, grow 'roots' outward and re-calc bounding box + center.
        """
        root_growth = self.grow_roots()
        # Ray-scan in 4 directions
        min_x, max_x, min_y, max_y = self.ray_trace()
        self.update_bounding_box_and_center(min_x, max_x, min_y, max_y)
        if not root_growth:
            if not self.branch_complete:
                self.scan_bounding_box()
                self.grow_branch()
                self.detect_if_all_visited()
            else:
                print("")
        # for b in self.braches:
        #    b.run()

    def scan_for_blockage(self, dx, dy):
        grid = self.world.grid
        """
        Scan from (cx, cy) outward in the direction (dx, dy)
        until we find a blocked cell (grid==0) or go out of bounds.

        Returns the number of valid 'food' cells we can move through.
        """
        steps = 0
        height, width = grid.shape

        # Start at the center cell
        x_curr, y_curr = self.center_x, self.center_y

        while True:
            # Candidate for next step
            x_next = x_curr + dx
            y_next = y_curr + dy

            # Check out-of-bounds
            if x_next < 0 or x_next >= width or y_next < 0 or y_next >= height:
                break

            # Check if blocked
            if y_next is None or x_next is None:
                break
            if grid[int(y_next), int(x_next)] is None or grid[int(y_next), int(x_next)] == 0:
                break

            # We can take a step
            steps += 1
            x_curr, y_curr = x_next, y_next

        return steps

    def grow_roots(self):
        """
        Look for cells adjacent to existing root cells that are still 'food'
        and add them to the mushroom root set.
        """
        frontier = []
        root_growth = False
        for cell in self.root_cells:
            rx = cell.x
            ry = cell.y
            for nx, ny in self.get_neighbors_8(rx, ry):
                candidate = Cell(nx, ny)
                if self.world.collide_with_any(self,nx,ny) or self.world.is_occupied(nx,ny):
                    pass
                elif candidate not in self.root_cells:
                    if self.is_food(nx, ny):
                        frontier.append(Cell(nx, ny))
                        self.world.occupy( nx,ny,self)
                        root_growth = True

        # For a slower or random growth, you might pick a subset:
        # new_roots = random.sample(frontier, k=min(len(frontier), 5))
        # or just add them all:
        new_roots = frontier

        for cell in new_roots:
            self.root_cells.add(cell)
        return root_growth

    def update_bounding_box_and_center(self, min_x, max_x, min_y, max_y):
        if not self.root_cells:
            return
        xs = [p.x for p in self.root_cells]
        ys = [p.y for p in self.root_cells]
        root_min_x = min(xs)
        root_max_x = max(xs)
        root_min_y = min(ys)
        root_max_y = max(ys)
        self.min_x = min_x
        self.min_y = min_y
        self.max_y = max_y
        self.max_x = max_x
        self.center_x = (self.min_x + self.max_x) / 2.0
        self.center_y = (self.min_y + self.max_y) / 2.0

    def get_neighbors_8(self, x, y):
        coords = []
        h, w = self.world.grid.shape
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    coords.append((nx, ny))
        return coords

    def is_food(self, x, y):
        return (self.world.grid[y, x] == 1)

    def draw(self, screen, zoom_factor,offset_x,offset_y):
        # 2) Draw each root cell in BLUE
        if not self.branch_complete:
            self.draw_cells(screen, zoom_factor,offset_x,offset_y)
            self.draw_list(screen,zoom_factor,offset_x,offset_y,self.core_cells)
        # 3) (Optional) Draw center in red
        cx_screen = int((self.center_x+offset_x) * zoom_factor)
        cy_screen = int((self.center_y+offset_y) * zoom_factor)

        #pygame.draw.circle(screen, (255, 0, 0), (cx_screen, cy_screen), 3)
        # 1) Draw bounding box in green
        self.draw_bounding_rect(screen, zoom_factor,offset_x,offset_y)

        # for b in self.braches:
        #    b.draw(screen,zoom_factor)

    def draw_list(self, screen, zoom_factor, offset_x,offest_y, list ):
        for cell in list:
            rx = cell.x + offset_x
            ry = cell.y + offest_y
            sx = int(rx * zoom_factor)
            sy = int(ry * zoom_factor)
            if cell.is_root:
                if(cell.is_visited):
                    colour = (100, 200, 250)
                else:
                    colour = (100, 200, 160)
                #print("root")
                r =pygame.Rect(sx, sy, 1, 1)
                pygame.draw.rect(screen,colour,r)
            elif cell.is_stem:
                #print("stem")
                colour = (200, 0, 0)
                r = pygame.Rect(sx, sy, 1, 1)
                pygame.draw.rect(screen, colour, r)
                #pygame.draw.circle(screen, colour, (sx, sy), 2)
            else:
                colour = (0, 0, 255)
                pygame.draw.circle(screen, colour, (sx, sy), 2)

    def draw_cells(self, screen, zoom_factor, offset_x,offest_y):
        self.draw_list(screen,zoom_factor,offset_x,offest_y,self.root_cells)

    def draw_bounding_rect(self,screen, zoom_factor,offset_x,offset_y):
        rect = self.get_rect(zoom_factor,offset_x,offset_y)
        pygame.draw.rect(screen, (0, 255, 0), rect, width=2)

    def grow_test_tentacles(self):
        """Grow tentacles in multiple directions for testing"""
        directions = [
            (1, 0), (0, 1), (-1, 0), (0, -1),  # Cardinal
            (1, 1), (-1, 1), (-1, -1), (1, -1)  # Diagonal
        ]

        results = []
        for direction in directions:
            success = self.grow_tentacle(direction)
            results.append((direction, success))

        return results

    def get_world_rect(self):
        width = self.get_width()+2
        height = self.get_height()+2
        half_w = (width / 2.0)
        half_h = (height/ 2.0)
        left = self.center_x - half_w
        top = self.center_y - half_h

        return pygame.Rect(left, top, width, height)

    def get_width(self):
        return (self.max_x - self.min_x)

    def get_height(self):
        return (self.max_y - self.min_y)

    def get_rect(self, zoom_factor=1.0,offset_x=0, offset_y=0):
        """
        Return a pygame.Rect for the axis-aligned bounding box.
        We'll treat (self.x, self.y) as the center of the rectangle.
        """
        width = self.get_width()
        height = self.get_height()
        half_w = (width / 2.0) * zoom_factor
        half_h = (height / 2.0) * zoom_factor

        left = ((self.center_x+offset_x) * zoom_factor) - half_w
        top = ((self.center_y+offset_y) * zoom_factor) - half_h
        disp_width = width * zoom_factor
        disp_height = height * zoom_factor

        return pygame.Rect(left, top, disp_width, disp_height)