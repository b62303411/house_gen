import os
import sys
import cv2
import numpy as np
import networkx as nx
import pygame
from pathlib import Path


###############################################################################
# PART 1: FLOORPLAN ANALYZER
###############################################################################

def keep_dark_tones(image_path, dark_threshold=80):
    """
    Filters out mid-to-light gray tones and keeps only the darkest tones.

    Args:
        image_path (str): Path to the input image (floorplan).
        dark_threshold (int): Upper limit for pixel intensity to keep.
                              Lower values == darker pixels.
                              Defaults to 80, tweak as needed.

    Returns:
        (original_image, binary_mask):
            original_image: The BGR image loaded from the disk.
            binary_mask:    A binary (0 or 255) image where darkest tones are white (255),
                           and everything else is black (0).
    """
    # 1) Load the image
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not load image from {image_path}")

    # 2) Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 3) Create a binary mask by keeping only the darkest tones
    #    Anything below dark_threshold becomes white (255), above becomes black (0).
    mask = cv2.inRange(gray, 0, dark_threshold)

    # 4) Optional morphological cleaning to remove noise and make lines more solid
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    # (You could also do an opening operation if you want to remove small specks):
    # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    return image, mask


class FloorplanAnalyzer:
    def __init__(self, door_template_path=None, window_template_path=None):
        """
        Initialize the floorplan analyzer with optional templates for doors and windows.

        Args:
            door_template_path: Path to door template image
            window_template_path: Path to window template image
        """
        self.door_template = None
        self.window_template = None

        # Load templates if provided
        if door_template_path and os.path.exists(door_template_path):
            self.door_template = cv2.imread(door_template_path, 0)

        if window_template_path and os.path.exists(window_template_path):
            self.window_template = cv2.imread(window_template_path, 0)

    def preprocess_floorplan(self, image_path):
        """
        Preprocess the floorplan image to prepare for analysis.

        Args:
            image_path: Path to the floorplan image

        Returns:
            Tuple of (original image, binary image)
        """
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Could not load image from {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

        # Remove noise
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return image, binary

    def detect_walls(self, binary):
        """
        Detect walls from binary image using Hough Line Transform.

        Args:
            binary: Binary image of the floorplan

        Returns:
            List of wall segments as ((x1, y1), (x2, y2)) tuples
        """
        # Edge detection
        edges = cv2.Canny(binary, 50, 150)

        # Hough Line Transform to detect lines
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180,
                                threshold=50,
                                minLineLength=50,
                                maxLineGap=10)

        # Extract line segments
        wall_segments = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                wall_segments.append(((x1, y1), (x2, y2)))

        return wall_segments

    def segment_rooms(self, binary):
        """
        Segment individual rooms in the floorplan.

        Args:
            binary: Binary image of the floorplan

        Returns:
            List of room contours
        """
        # Find contours (closed shapes)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        rooms = []
        for contour in contours:
            # Filter out small contours (noise)
            if cv2.contourArea(contour) > 1000:
                # Approximate the contour to simplify
                epsilon = 0.01 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                rooms.append(approx)

        return rooms

    def detect_doors_windows(self, image, binary):
        """
        Detect doors and windows using template matching.

        Args:
            image: Original floorplan image
            binary: Binary image of the floorplan

        Returns:
            Tuple of (door_locations, window_locations)
        """
        doors = []
        windows = []

        # Check if templates are available
        if self.door_template is not None:
            # Match door template
            door_result = cv2.matchTemplate(binary, self.door_template, cv2.TM_CCOEFF_NORMED)
            door_threshold = 0.7
            door_locations = np.where(door_result >= door_threshold)
            doors = list(zip(*door_locations[::-1]))

        if self.window_template is not None:
            # Match window template
            window_result = cv2.matchTemplate(binary, self.window_template, cv2.TM_CCOEFF_NORMED)
            window_threshold = 0.7
            window_locations = np.where(window_result >= window_threshold)
            windows = list(zip(*window_locations[::-1]))

        return doors, windows

    def detect_furniture(self, image):
        """
        Detect furniture in the floorplan (simplified placeholder).

        Args:
            image: Original floorplan image

        Returns:
            List of detected furniture with positions
        """
        # Placeholder for furniture detection
        # In a real implementation, this would use a pre-trained model
        print("Furniture detection would require a specialized model.")
        return []

    def generate_mesh(self, wall_segments, rooms, doors, windows, furniture):
        """
        Generate a mesh representation from the detected elements.

        Args:
            wall_segments: List of wall segments
            rooms: List of room contours
            doors: List of door positions
            windows: List of window positions
            furniture: List of furniture with positions

        Returns:
            NetworkX graph representing the floorplan mesh
        """
        # Create a graph structure
        G = nx.Graph()

        # Add nodes for all corners/intersections
        points = set()
        for start, end in wall_segments:
            points.add(start)
            points.add(end)

        # Convert set to list for indexing
        points = list(points)

        # Add nodes to graph
        for i, point in enumerate(points):
            G.add_node(i, pos=point, type='corner')

        # Add edges for wall segments
        point_to_idx = {point: i for i, point in enumerate(points)}
        for start, end in wall_segments:
            if start in point_to_idx and end in point_to_idx:
                G.add_edge(point_to_idx[start], point_to_idx[end], type='wall')

        # Add nodes for doors
        for i, door_pos in enumerate(doors):
            node_id = len(points) + i
            G.add_node(node_id, pos=door_pos, type='door')

            # Find closest wall points and connect
            self._connect_to_closest_walls(G, node_id, door_pos, points, point_to_idx)

        # Add nodes for windows
        for i, window_pos in enumerate(windows):
            node_id = len(points) + len(doors) + i
            G.add_node(node_id, pos=window_pos, type='window')

            # Find closest wall points and connect
            self._connect_to_closest_walls(G, node_id, window_pos, points, point_to_idx)

        # Add room information
        for i, room in enumerate(rooms):
            # Calculate room center
            center_x = int(np.mean([p[0][0] for p in room]))
            center_y = int(np.mean([p[0][1] for p in room]))

            node_id = len(points) + len(doors) + len(windows) + i
            G.add_node(node_id, pos=(center_x, center_y), type='room', contour=room)

        return G

    def _connect_to_closest_walls(self, G, node_id, pos, points, point_to_idx, k=2):
        """Helper to connect elements to closest walls"""
        # Calculate distances to all wall points
        distances = [np.sqrt((pos[0] - p[0]) ** 2 + (pos[1] - p[1]) ** 2) for p in points]

        # Find k closest points
        closest_indices = np.argsort(distances)[:k]

        # Connect to closest points
        for idx in closest_indices:
            wall_node_id = point_to_idx[points[idx]]
            G.add_edge(node_id, wall_node_id, type='connection')

    def process_floorplan(self, image_path):
        """
        Process a floorplan image and generate a vectorized mesh.

        Args:
            image_path: Path to the floorplan image

        Returns:
            NetworkX graph representing the floorplan mesh and
            a tuple of (image, binary, wall_segments, rooms, doors, windows)
        """
        print(f"Processing floorplan: {image_path}")

        # Preprocess image
        image, binary = self.preprocess_floorplan(image_path)

        # Detect walls
        wall_segments = self.detect_walls(binary)
        print(f"Detected {len(wall_segments)} wall segments")

        # Segment rooms
        rooms = self.segment_rooms(binary)
        print(f"Detected {len(rooms)} rooms")

        # Detect doors and windows
        doors, windows = self.detect_doors_windows(image, binary)
        print(f"Detected {len(doors)} doors and {len(windows)} windows")

        # Detect furniture (placeholder)
        furniture = self.detect_furniture(image)

        # Generate mesh
        mesh = self.generate_mesh(wall_segments, rooms, doors, windows, furniture)
        print(f"Generated mesh with {mesh.number_of_nodes()} nodes and {mesh.number_of_edges()} edges")

        return mesh, (image, binary, wall_segments, rooms, doors, windows)


###############################################################################
# PART 2: FLOORPLAN PYGAME VISUALIZER
###############################################################################

class FloorplanVisualizer:
    def __init__(self, width=1024, height=768):
        """
        Initialize the Pygame visualizer.

        Args:
            width: Window width
            height: Window height
        """
        # Initialize Pygame
        pygame.init()
        pygame.display.set_caption("Floorplan Visualizer")

        # Setup display
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()

        # Colors
        self.colors = {
            'background': (240, 240, 240),
            'wall': (50, 50, 50),
            'door': (200, 100, 100),
            'window': (100, 200, 200),
            'room': (200, 200, 100, 120),  # RGBA: use alpha for partial transparency
            'corner': (100, 100, 200),
            'furniture': (150, 150, 150),
            'text': (0, 0, 0)
        }

        # Initialize fonts
        self.font = pygame.font.SysFont('Arial', 14)

        # Visualization parameters
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False
        self.drag_start = None
        self.start_offset = (0, 0)

    def transform_point(self, point):
        """Transform a point from graph coordinates to screen coordinates."""
        x, y = point
        return (int(x * self.scale + self.offset_x),
                int(y * self.scale + self.offset_y))

    def inverse_transform_point(self, point):
        """Transform a point from screen coordinates to graph coordinates."""
        x, y = point
        return ((x - self.offset_x) / self.scale,
                (y - self.offset_y) / self.scale)

    def auto_fit_view(self, G):
        """Automatically adjust scale and offset to fit the graph in the view."""
        if len(G.nodes) == 0:
            return

        # Get bounding box of all nodes
        xs = []
        ys = []
        for node in G.nodes:
            pos = G.nodes[node]['pos']
            xs.append(pos[0])
            ys.append(pos[1])

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        width_range = max_x - min_x
        height_range = max_y - min_y

        if width_range == 0 or height_range == 0:
            return

        # Add some margin
        margin = 50
        available_width = self.width - 2 * margin
        available_height = self.height - 2 * margin

        scale_x = available_width / width_range
        scale_y = available_height / height_range

        # Take the minimum scale to fit both width and height
        self.scale = min(scale_x, scale_y)

        # Center the bounding box on screen
        # We'll compute a middle point in the data coords:
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0

        # Transform that to screen coords
        tx, ty = (center_x * self.scale, center_y * self.scale)

        # Now we want that to be the center of our screen
        self.offset_x = self.width // 2 - tx
        self.offset_y = self.height // 2 - ty

    def draw_floorplan(self, G):
        """Draw the floorplan (walls, rooms, doors, windows, etc.)."""
        # Fill background
        self.screen.fill(self.colors['background'])

        # Draw edges (walls, possibly connections)
        for u, v, data in G.edges(data=True):
            edge_type = data.get('type', 'wall')
            u_pos = G.nodes[u]['pos']
            v_pos = G.nodes[v]['pos']
            start = self.transform_point(u_pos)
            end = self.transform_point(v_pos)

            if edge_type == 'wall':
                pygame.draw.line(self.screen, self.colors['wall'], start, end, 3)
            else:
                # For example, a different style for connections
                pygame.draw.line(self.screen, (150, 150, 150), start, end, 1)

        # Draw rooms (filled polygons) before we draw other nodes
        for node_id, data in G.nodes(data=True):
            if data.get('type') == 'room':
                contour = data.get('contour', None)
                if contour is not None:
                    # Convert each point in the contour to screen coords
                    polygon_points = [
                        self.transform_point((pt[0][0], pt[0][1])) for pt in contour
                    ]
                    # Use pygame.gfxdraw or polygon with alpha
                    # Pygame doesn't have built-in alpha with draw.polygon.
                    # One workaround is to create a surface with per-pixel alpha.
                    room_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    pygame.draw.polygon(room_surface, self.colors['room'], polygon_points)
                    self.screen.blit(room_surface, (0, 0))

        # Draw nodes (corners, doors, windows, etc.)
        for node_id, data in G.nodes(data=True):
            node_type = data.get('type', 'corner')
            pos = self.transform_point(data['pos'])

            if node_type == 'corner':
                pygame.draw.circle(self.screen, self.colors['corner'], pos, 4)
            elif node_type == 'door':
                pygame.draw.circle(self.screen, self.colors['door'], pos, 6)
            elif node_type == 'window':
                pygame.draw.circle(self.screen, self.colors['window'], pos, 6)
            elif node_type == 'room':
                # Already drawn the polygon, but we can place a label or center marker
                pygame.draw.circle(self.screen, (0, 0, 0), pos, 3)  # black dot for room center

    def handle_events(self):
        """Handle user input events (panning, zooming, quitting)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # left click
                    self.dragging = True
                    self.drag_start = event.pos
                    self.start_offset = (self.offset_x, self.offset_y)
                elif event.button == 4:  # scroll up
                    self.scale *= 1.1
                elif event.button == 5:  # scroll down
                    self.scale *= 0.9

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    dx = event.pos[0] - self.drag_start[0]
                    dy = event.pos[1] - self.drag_start[1]
                    self.offset_x = self.start_offset[0] + dx
                    self.offset_y = self.start_offset[1] + dy

        return True

    def run(self, G):
        """Main loop to visualize the floorplan graph."""
        self.auto_fit_view(G)

        running = True
        while running:
            self.clock.tick(60)  # Limit to 60 FPS
            running = self.handle_events()

            self.draw_floorplan(G)
            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    fa = FloorplanAnalyzer(door_template_path="../floor_plans/door.png", window_template_path="../floor_plans/window.png")
    img, dark_mask = keep_dark_tones("../floor_plans/fp2.png", dark_threshold=80)

    # 2) Save or visualize the result (for debugging)
    cv2.imwrite("dark_tones_only.png", dark_mask)

    mesh, (image, binary, wall_segments, rooms, doors, windows) =fa.process_floorplan("dark_tones_only.png")
    # 3) Visualize the resulting mesh with Pygame
    visualizer = FloorplanVisualizer(width=1200, height=800)
    visualizer.run(mesh)