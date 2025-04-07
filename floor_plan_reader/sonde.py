import statistics


class Sonde:
    def __init__(self, direction, data):
        self.direction = direction
        if data is None:
            pass
        self.data = data
        self.min = 500
        self.max = 0
        self.corrected_length = None
        self.med = None

    def get_center(self):
        return self.data.get_center()

    def get_magnitude(self):
        if self.corrected_length is None:
            max_width = -1
            self.med = statistics.median(self.data.extra.results.values())

            i = 0
            for e in self.data.extra.results.values():
                if e > self.med:
                    i = i + 1
                elif abs(self.med-e) < 2:
                    i = i + 1

            self.corrected_length = i

        return self.corrected_length

    def __lt__(self, other):
        """Define how to compare two Vector objects for sorting."""
        if self.data is None:
            return True
        return self.data.steps < other.data.steps
