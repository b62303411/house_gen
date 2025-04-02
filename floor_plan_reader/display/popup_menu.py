import pygame

from floor_plan_reader.display.button import Button
from floor_plan_reader.display.intersectionview import IntersectionView
from floor_plan_reader.display.point import Point
from floor_plan_reader.display.text_box import TextBox
from floor_plan_reader.display.view_point import ViewPoint
from floor_plan_reader.display.window import Window


class Converter:
    def __init__(self, bounding_box, snap_x, snap_y, convert):
        self.bounding_box = bounding_box
        self.snap_x = snap_x
        self.snap_y = snap_y
        self.zoom = 4
        self.convert = convert

    def convert_(self, x, y):
        return self.convert(self.bounding_box, x, y, self.zoom, self.snap_x, self.snap_y)

    def convert_tuple(self, point):
        return self.convert_(point[0], point[1])


class PopupMenu(Window):
    def __init__(self, view, x, y, width, height, title="Action Menu"):
        self.view = view
        super().__init__(x, y, width, height)

        self.title = title

        # Simple single button
        self.button_run_phase = Button(self, "Run Phase", Point(0, 65))
        self.button_run_blob = Button(self, "Blob Rerun", Point(0, 10))

        self.button_run_blob.on_button_click = self.run_blob
        self.text_box = TextBox(self, [], (0, 0))
        self.components.add(self.button_run_phase)
        self.components.add(self.button_run_blob)
        self.components.add(self.text_box)

        # Basic fonts for text
        self.tfont = pygame.font.SysFont(None, 14)
        self.font = pygame.font.SysFont(None, 24)
        self.big_font = pygame.font.SysFont(None, 32)

    def run_blob(self):
        self.view.run_blob()

    def draw(self, surface):
        """Draw the pop-up and its button if visible."""
        if not self.visible:
            return
        super().draw(surface)
        # Title
        selected = self.view.selected
        state = selected.get_state()
        text = []
        text.append(f"blob id:{selected.blob.id}")
        text.append(f"{selected.id}:{state}")
        if selected.wall_segment is not None:
            text.append(f"state seg:{selected.wall_segment.state}")
        self.text_box.set_text(text)
        title_text = self.big_font.render(self.title, True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.rect.centerx, self.rect.y + 30))
        surface.blit(title_text, title_rect)

        # --- Zoom/Scale the surface ---
        blob = selected.blob
        blob.calculate_bounding_box()
        snapshot = blob.get_snapshot()
        position = (50, 100)
        snap_x = self.rect.x + position[0]
        snap_y = self.rect.y + position[1]
        self.draw_snapshot(surface, snapshot, position)

        snapshot = blob.get_occupied_snapshot()
        self.draw_snapshot(surface, snapshot, position)

        intersections = blob.get_intersections()
        center = blob.get_center()
        blob.calculate_bounding_box()

        bounding_box = blob.get_corners()
        walls = blob.get_walls()
        segments = set()
        for w in walls:
            if w.wall_segment is not None:
                segments.add(w.wall_segment)

        self.draw_segments(surface, segments, bounding_box, snap_x, snap_y)

        self.draw_intersections(surface, intersections, bounding_box, snap_x, snap_y)

    def convert(self, bounding_box, x, y, zoom, p_x, p_y):
        dx, dy = x - bounding_box.min_x, y - bounding_box.min_y
        sx, sy = dx * zoom, dy * zoom
        return sx + p_x, sy + p_y

    def draw_segments(self, surface, segments, bounding_box, snap_x, snap_y):
        conv = Converter(bounding_box, snap_x, snap_y, self.convert)
        for s in segments:
            if s.collision_box_extended is not None:
                cb = s.collision_box_extended
                line = cb.get_center_line_string()
                x1, y1, x2, y2 = line.bounds
                sx1, sy1 = conv.convert_(x1, y1)
                sx2, sy2 = conv.convert_(x2, y2)
                pygame.draw.line(surface, (255, 255, 0), (sx1, sy1), (sx2, sy2), 3)

    def draw_intersections(self, surface, intersections, bounding_box, snap_x, snap_y):

        conv = Converter(bounding_box, snap_x, snap_y, self.convert)
        v = IntersectionView()
        # w, h = blob.get_shape()
        vp = ViewPoint()
        vp.zoom_factor = 4

        for i in intersections:
            (ix, iy) = i.point
            ex, ey = conv.convert_(ix, iy)
            pygame.draw.circle(surface, (0, 255, 255), (ex, ey), 6)
            # Define a font
            font = pygame.font.SysFont("Arial", 16)  # (font_name, size)
            text_surface = font.render(f"{i.id}", True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(ex, ey))
            half_width = text_rect.width // 2
            # Add some padding around the text
            padding = 8
            background_rect = pygame.Rect(
                text_rect.left - padding,
                text_rect.top - padding,
                text_rect.width + 2 * padding,
                text_rect.height + 2 * padding
            )

            # Draw the background rect (optional rounded corners)
            pygame.draw.rect(surface, (0, 0, 0), background_rect, border_radius=4)  # Black background

            surface.blit(text_surface, (ex-half_width, ey-half_width))
            for l in i.lines:
                if l in self.view.simulation._line_dic:
                    line = self.view.simulation._line_dic[l]
                    start = conv.convert_tuple(line.start_point)
                    end = conv.convert_tuple(line.end_point)
                    pygame.draw.line(surface, (255, 0, 0), start, end)
                    text_surface = font.render(f"{l}", True, (255, 255, 255))
                    surface.blit(text_surface, ((start[0]+end[0])/2, (start[1]+end[1])/2))

        center = (snap_x, snap_y)
        # center = (-center[0] + position[0] + self.rect.x, -center[1] + position[1] + self.rect.y)
        vp.set_position(center)
        v.draw_intersections(surface, vp, intersections, (0, 255, 0))

    def draw_snapshot(self, surface, snapshot, position):
        surface_blob = pygame.surfarray.make_surface(snapshot.swapaxes(0, 1))
        zoom_factor = 4  # magnify by 4x
        scaled_width = surface_blob.get_width() * zoom_factor
        scaled_height = surface_blob.get_height() * zoom_factor

        zoomed_surface = pygame.transform.scale(surface_blob, (scaled_width, scaled_height))

        surface.blit(zoomed_surface, (self.rect.x + position[0], self.rect.y + position[1]))

    def handle_event(self, event, on_button_click=None):
        for c in self.components:
            c.handle_event(event, on_button_click)
        """
        Handle Pygame events.
        If the pop-up is visible and the user clicks the button, call on_button_click (if provided).

        Args:
            event (pygame.event.Event): The event to handle.
            on_button_click (Callable): Function to call when the button is clicked.
        """
        if not self.visible:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Check if user clicked the button

            # If user clicks outside the pop-up, optionally hide it
            if not self.rect.collidepoint(mx, my):
                self.hide()
                self.view.selected = None
