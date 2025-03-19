class PruningUtil:
    @staticmethod
    def prune(candiate,list):
        for m in list:
            if m != candiate and m.alive and m.is_valid():
                if candiate.collision_box.is_parallel_to(m.collision_box):
                    if candiate.collision_box.is_overlapping(m.collision_box):
                        candiate.overlapping.add(m)
                        ratio = candiate.get_occupation_ratio()
                        if ratio < m.get_occupation_ratio():
                            #candiate.kill()
                            return True,m
        return False,None