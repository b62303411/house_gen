import random

from floor_plan_reader.blob import Blob
from floor_plan_reader.id_util import Id_Util
from floor_plan_reader.mushroom_agent import Mushroom


class AgentFactory:
    def create_mushroom(self, world,x, y):
        mush = Mushroom(x, y, world, Id_Util.get_id())
        return mush
    def create_blob(self, world,x, y):
        blob = Blob(Id_Util.get_id(),world ,x, y)

        return blob