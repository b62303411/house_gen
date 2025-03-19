class MinMax:
    def __init__(self,
                 min_x=9999, max_x=0, min_y=9999, max_y=0):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def evaluate(self, min_x=9999, max_x=9999, min_y=9999, max_y=9999):
        self.min_x = min(self.min_x, min_x)
        self.min_y = min(self.min_y, min_y)
        self.max_y = min(self.max_y, max_y)
        self.max_x = min(self.max_x, max_x)