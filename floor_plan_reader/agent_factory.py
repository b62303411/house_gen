import random

from floor_plan_reader.mushroom_agent import Mushroom


class AgentFactory:
    def create_mushroom(self, world,x, y):
        mush = Mushroom(x, y, world, random.randint(1, 2**31 - 1))
        return mush