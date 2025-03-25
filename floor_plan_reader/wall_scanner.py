from floor_plan_reader.sonde import Sonde
from floor_plan_reader.sonde_data import SondeData
from floor_plan_reader.vector import Vector
from sortedcontainers import SortedList


class ScanResult:
    def __init__(self):
        self.sondes = SortedList()
        self.sonde_dic = {}
        self.stem_sonde = None
        self.width_sonde = None
        self.center = None

    def add_sonde(self, direction, sonde):
        self.sonde_dic[direction] = sonde
        self.sonde_dic[direction.opposite()] = sonde
        self.sondes.add(sonde)

    def get_longest(self):
        return self.sondes[-1]

    def get_from_dir(self, dir):
        return self.sonde_dic.get(dir)

    def calculate_result(self):
        self.stem_sonde = self.get_longest()
        width_dir = self.stem_sonde.direction.get_normal()
        width_sonde = self.get_from_dir(width_dir)
        if width_sonde is None:
            width_sonde = self.get_from_dir(width_dir.opposite())
        self.width_sonde = width_sonde
        self.center = self.stem_sonde.get_center()

    def get_lenght(self):
        return self.stem_sonde.get_magnitude()

    def get_width(self):
        return self.width_sonde.get_magnitude()

    def get_dir(self):
        return self.stem_sonde.direction
    def is_valid(self):
        return self.get_lenght()>0
class WallScanner:
    def __init__(self, world):
        self.world = world

    def is_food(self, x, y):
        return self.world.is_food(int(x), int(y))

    def is_3_wide_food(self, cx, cy, direction):
        normal = direction.get_normal()
        nx, ny = normal.direction
        # For offset in [-1, 0, 1], check (cx + offset*nx, cy + offset*ny)
        for offset in [-1, 0, 1]:
            test_x = int(cx + offset * nx)
            test_y = int(cy + offset * ny)
            # Check bounds + food
            if not self.world.is_within_bounds(test_x, test_y):
                return False
            if not self.is_food(test_x, test_y):
                return False
        return True

    def is_within_bounds(self,x,y):
        return self.world.is_within_bounds(x,y)

    def ping(self,x,y,d):
        is_within_bounds = self.is_within_bounds(x,y)
        if not is_within_bounds:
            return False
        is_food = self.is_food(x,y)

        is_wide_enough = self.is_3_wide_food(x,y,d)
        return is_food and is_wide_enough

    def measure_extent(self, x, y, d):
        """Measure extent along a given direction vector (dx, dy) properly.
       - First, crawl backward to find the start.
       - Then, count forward to find the total steps.
        """
        dx, dy = d.dx(), d.dy()
        height, width = self.world.grid.shape
        min_x = None
        min_y = None
        max_x = None
        max_y = None
        # Step 1: Crawl backward until hitting a boundary
        if self.is_food(x, y):
            min_x = x
            min_y = y
        else:
            pass

        while self.ping(x,y,d):
            x -= dx
            y -= dy
            min_x = x
            min_y = y
        if min_x is None:
            logging.info(f"{x} {y}  {width} {height}")
        # Step 2: Move one step forward to set the actual starting point
        x += dx
        y += dy
        steps = 0

        # Step 3: Count steps moving forward until hitting another boundary
        while 0 <= x < width and 0 <= y < height and self.is_food(x, y):
            x += dx
            y += dy
            steps += 1  # Count steps only in the forward direction
            max_x = x
            max_y = y
        if min_x is None or min_y is None:
            pass
        data = SondeData(steps, min_x, min_y, max_x, max_y)
        return data  # The total step count along this direction

    def scan_for_walls(self, x, y, directions=list(
        map(lambda direction: Vector(direction), [(1, 0), (0, 1), (0.5, 0.5), (0.5, -0.5)]))):
        results = ScanResult()
        for d in directions:
            data = self.measure_extent(x, y, d)
            s = Sonde(d, data)
            results.add_sonde(d, s)
        results.calculate_result()

        return results
