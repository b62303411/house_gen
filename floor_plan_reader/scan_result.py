from sortedcontainers import SortedList

from floor_plan_reader.math.vector import Vector


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

    def to_global(self, u, v, origin, d_dir, n_dir):
        return (
            origin[0] + u * d_dir.dx() + v * n_dir.dx(),
            origin[1] + u * d_dir.dy() + v * n_dir.dy()
        )

    def calculate_result(self):
        self.stem_sonde = self.get_longest()
        width_dir = self.stem_sonde.direction.get_normal()
        width_sonde = self.get_from_dir(width_dir)
        if width_sonde is None:
            width_sonde = self.get_from_dir(width_dir.opposite())
        self.width_sonde = width_sonde

        d_data = self.stem_sonde.data
        n_data = self.width_sonde.data
        d_direction = self.stem_sonde.direction
        n_direction = self.width_sonde.direction
        origin = self.stem_sonde.get_center()
        min_d = Vector.project((d_data.min_x, d_data.min_y), origin, d_direction)
        max_d = Vector.project((d_data.max_x, d_data.max_y), origin, d_direction)
        min_n = Vector.project((n_data.min_x, n_data.min_y), origin, n_direction)
        max_n = Vector.project((n_data.max_x, n_data.max_y), origin, n_direction)
        corner_1 = self.to_global(min_d, min_n, origin, d_direction, n_direction)
        corner_2 = self.to_global(min_d, max_n, origin, d_direction, n_direction)
        corner_3 = self.to_global(max_d, min_n, origin, d_direction, n_direction)
        corner_4 = self.to_global(max_d, max_n, origin, d_direction, n_direction)
        center = self.to_global(
            0.5 * (min_d + max_d),
            0.5 * (min_n + max_n),
            origin, d_direction, n_direction
        )

        self.center = center

    def get_lenght(self):
        return self.stem_sonde.get_magnitude()

    def get_width(self):
        return self.width_sonde.get_magnitude()

    def get_dir(self):
        return self.stem_sonde.direction

    def is_valid(self):
        lenght_valid = self.get_lenght() > 2
        width_valid = self.get_width() > 2 and self.get_width() < 15
        return lenght_valid and width_valid