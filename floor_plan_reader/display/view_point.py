class ViewPoint:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.zoom_factor = 1
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
            self.zoom_factor = self.min_zoom

    def move_left(self, move_speed):
        self.offset_x -= move_speed

    def move_right(self, move_speed):
        self.offset_x += move_speed

    def convert(self, x, y):
        x = int((x + self.offset_x) * self.zoom_factor)
        y = int((y + self.offset_y) * self.zoom_factor)
        return x, y

    def convert_back(self, screen_x, screen_y):
        """
        Convert from screen coordinates back to map coordinates.
        """
        # Inverse of: (x + offset_x) * zoom_factor
        x_map = screen_x / self.zoom_factor - self.offset_x
        y_map = screen_y / self.zoom_factor - self.offset_y
        return x_map, y_map

    def get_center(self):
        return self.offset_x * self.zoom_factor, self.offset_y * self.zoom_factor