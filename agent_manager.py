from floor_plan_reader.agents.blob import Blob
from floor_plan_reader.agents.mushroom_agent import Mushroom
from floor_plan_reader.agents.wall_segment import WallSegment


class AgentManager:

    def __init__(self, simulation):
        self.simulation = simulation
        self.zombie_candidates = []

    def get_blob_count(self):
        return len(self.simulation.world.blobs)

    def run(self):
        world = self.simulation.world
        agents = world.agents.copy()
        for agent in agents:
            if agent.alive:
                agent.run()
            else:
                self.zombie_candidates.append(agent)
        for zombie in self.zombie_candidates:
            if zombie in world.agents:
                world.agents.remove(zombie)
            if zombie in world.walls:
                world.walls.remove(zombie)
            if zombie in world.blobs:
                world.blobs.remove(zombie)
            if zombie in world.wall_segments:
                world.wall_segments.remove(zombie)

            # else: no moves => ant stays put
        if not len(world.candidates) == 0:
            agent = world.candidates.popleft()
            if isinstance(agent, Mushroom):
                world.walls.add(agent)
            if isinstance(agent, WallSegment):
                world.wall_segments.add(agent)
            if isinstance(agent, Blob):
                world.blobs.add(agent)

            world.agents.add(agent)
