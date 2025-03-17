import random


class Id_Util:
    @staticmethod
    def get_id():
        return random.randint(1, 2 ** 31 - 1)