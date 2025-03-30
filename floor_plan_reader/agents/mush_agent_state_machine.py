class MushAgentStateMachine:
    def __init__(self, mush):
        self.mush = mush
        self.state = "ray_trace"

    def process_state(self):
        if self.state == "ray_trace":
            self.mush.ray_trace_phase()
            self.state = "fill_phase"
            return
        if self.state == "fill_phase":
            self.mush.absorb_bleading_out()
            self.mush.fill_box()
            self.state = "pruning"
            return
        if self.state == "recenter_phase":
            if self.mush.recenter_phase():
                self.state = "recenter_phase"
            else:
                self.mush.fill_box()
                self.state = "pruning"
            return
        elif self.state == "pruning":
            self.mush.prunning_phase()
            self.state = "wall_type"
            return
        elif self.state == "overlap":
            self.mush.overlap_phase()
            self.state = "crawl"
            return
        elif self.state == "crawl":
            self.mush.crawl_phase()
            self.state = "wrapup"
            return
        elif self.state == "wall_type":
            self.mush.wall_type_phase()
            if self.mush.is_centered():
                self.state = "center"
            else:
                self.state = "overlap"
            return
        elif self.state == "center":
            self.mush.try_to_center()
            self.state = "overlap"
            return
        elif self.state == "wrapup":
            if self.mush.is_valid():
                self.mush.forced_fill_box()
                self.state = "done"
            else:
                self.mush.kill()
            return

    def process_state_(self):
        """State machine for floor plan resolution."""
        if self.state == "ray_trace":
            self.ray_trace_phase()
            self.fill_box()
            self.state = "stem_growth"
        elif self.state == "stem_growth":
            self.stem_growth_phase()
            self.state = "width_assessment"
        elif self.state == "width_assessment":
            self.width_assessment_phase()
            self.state = "pruning"
        elif self.state == "width_expansion":
            self.width_ray_trace()
            self.state = "pruning"
        elif self.state == "pruning":
            self.prunning_phase()
            self.state = "overlap"
        elif self.state == "overlap":
            self.overlap_phase()
            self.state = "perimeter_reaction"
        elif self.state == "perimeter_reaction":
            self.perimeter_reaction_phase()
            self.state = "growth" if self.has_growth_cells() else "done"
        elif self.state == "growth":
            self.growth_phase()
            if self.is_valid():
                self.state = "done"
            else:
                self.kill()
        # min_x, max_x, min_y, max_y = self.ray_trace()
        # self.update_bounding_box_and_center(min_x, max_x, min_y, max_y)
