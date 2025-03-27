from floor_plan_reader.agents.blob import Blob
from floor_plan_reader.id_util import Id_Util
from floor_plan_reader.agents.mushroom_agent import Mushroom


class AgentFactory:

    def __init__(self, world):
        self.world = world

    def create_mushroom(self,  blob, x, y):
        # self, world, blob, start_x, start_y, mush_id
        mush = Mushroom(x, y, self.world, blob, Id_Util.get_id())
        return mush

    def create_blob(self, x, y):
        blob = Blob(Id_Util.get_id(), self.world, x, y)

        return blob
