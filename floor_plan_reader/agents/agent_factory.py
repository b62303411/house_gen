from floor_plan_reader.agents.blob import Blob
from floor_plan_reader.id_util import IdUtil
from floor_plan_reader.agents.mushroom_agent import Mushroom


class AgentFactory:

    def __init__(self, world):
        self.world = world

    def create_mushroom(self,  blob, x, y):
        # world, blob, start_x, start_y, mush_id
        mush = Mushroom(self.world, blob,x, y, IdUtil.get_id())
        return mush

    def create_blob(self, x, y):
        blob = Blob(IdUtil.get_id(), self.world, x, y)

        return blob
