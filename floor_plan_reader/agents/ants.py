import numpy as np
import pygame
import random

from floor_plan_reader.agents.agent import Agent


class Ant(Agent):
    def __init__(self, x, y, ant_id, world):
        super().__init__(ant_id)
        self.world = world
        self.x = x
        self.y = y
        self.state = "idle"  # just a placeholder
        self.path = [(x, y)]
        self.alive = True
    def convert_coord(self,x,y):
            return self.world.convert_coordinates(x,y)

    def draw_path(self,screen, zoom_factor,offset_x, offset_y):
        if self.alive:
            for x,y in self.path:
                size=1
                scaled_x = int((x + offset_x) * zoom_factor)
                scaled_y = int((y + offset_y) * zoom_factor)
                color = (255, 255, 0)
                pygame.draw.circle(screen, color, (scaled_x, scaled_y), size)

    def draw(self, screen, vp):
        scaled_x ,scaled_y= vp.convert(self.x,self.y)

        # Color the ant based on ID or a fixed color
        if self.alive:
            color = (0, 0, 255)  # red
            size = 5
        else:
            color = (0, 0, 255)
            size = 2
        pygame.draw.circle(screen, color, (scaled_x, scaled_y), size)

    def run(self):
        if self.world.is_food(self.x, self.y):
            self.alive = False
            self.world.create_blob(self.x, self.y)
        else:
            valid = self.find_valid_neighbors()
            if valid:
                nx, ny = random.choice(valid)
                self.move(nx, ny)

    def sigmoid(self,x):
        """Helper function for smooth probability scaling."""
        return 1 / (1 + np.exp(-x))

    def fuzzy_membership(self,value, low, high):
        """Returns fuzzy membership between 0 (low) to 1 (high)"""
        return (value - low) / (high - low) if high != low else 0.001

    def fuzzy_choice(self,probabilities):
        """Select an index based on weighted probabilities."""
        return random.choices(range(len(probabilities)), weights=probabilities, k=1)[0]

    def find_valid_neighbors(self):
        """
        Uses fuzzy logic to determine the best movement direction.
        """
        grid = self.world.grid
        visited = self.world.visited

        neighbors = self.world.get_neighbors_8(self.x, self.y)
        scores = []

        for nx, ny in neighbors:
            # Food presence
            food_score = 1.0 if self.world.is_food(nx, ny) and not self.world.is_occupied(nx, ny) else 0.0

            # Occupancy score (lower is better)
            occupancy_score = 0.0 if not self.world.is_occupied(nx, ny) else 1.0
            collide_score = 0 if not self.world.collide_with_any(self,nx,ny) else 1.0
            # Exploration score (less visited is better)
            visit_count = visited[ny, nx]
            exploration_score = self.sigmoid(-visit_count)  # More visits = lower score

            # Fuzzy combination
            final_score = (
                    0.6 * food_score +  # Strong preference for food
                    0.3 * exploration_score -  # Prefer less-visited areas
                    (0.8 * occupancy_score  # Avoid occupied areas
                    +0.9 * collide_score)
            )

            scores.append((max(final_score,0.0001), (nx, ny)))

        # If no good options, return a random neighbor
        if not scores:
            return random.choice(neighbors)

        # Normalize scores into probabilities
        min_score, max_score = min(scores)[0], max(scores)[0]
        probabilities = [self.fuzzy_membership(score[0], min_score, max_score) for score in scores]

        # Select move based on fuzzy probabilities
        best_index = self.fuzzy_choice(probabilities)
        return [scores[best_index][1]]  # Return selected neighbor


    def move(self, nx, ny):
        visited = self.world.visited
        self.x = nx
        self.y = ny
        self.path.append((nx, ny))
        visited[ny, nx] = self.id


