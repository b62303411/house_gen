from floor_plan_reader.display.text_box import TextBox
from floor_plan_reader.display.window import Window


class StatusWindow(Window):
    def __init__(self, simulation, x, y, width, height, title="Action Menu"):
        self.simulation = simulation
        super().__init__(x, y, width, height)
        self.text_box = TextBox(self, [], (0, 0))
        self.components.add(self.text_box)

    def draw(self, surface):
        super().draw(surface)
        txt =[]
        agent_txt = f"Agents: {self.simulation.get_agent_count()}"
        seg_txt = f"Wall Seg: {self.simulation.get_wall_segment_count()}"
        txt.append(agent_txt)
        txt.append(seg_txt)
        self.text_box.set_text(txt)
