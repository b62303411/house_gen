import math


@staticmethod
def unify_close_parallel_lines(vectors,
                               angle_thresh_deg=5.0,
                               dist_thresh=15.0,
                               thick_width=15):
    """
    Replace the old approach of thickening parallel lines.
    Now we actually unify/merge them into a single line if they're nearly parallel & close.

    We keep the same function signature to avoid changing the existing API,
    but internally we do real merging rather than thickening.

    :param vectors: list of {"start":(x1,y1), "end":(x2,y2), "width":val}
    :param angle_thresh_deg: angle difference threshold (degrees)
    :param dist_thresh: normal-form distance threshold for merging
    :param thick_width: ignored now, but we keep it to not break API
    :return: new list of unified lines with the same structure
    """

    def line_angle_and_offset(x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 180.0
        length = math.hypot(dx, dy)
        if length < 1e-9:
            return (angle, 0.0)
        # normal
        nx, ny = dy / length, -dx / length
        dist = abs(nx * x1 + ny * y1)
        return (angle, dist)

    def project_param(px, py, ax, ay, dx, dy):
        """Project point (px,py) onto the param of line from (ax,ay)->(ax+dx,ay+dy)."""
        denom = dx * dx + dy * dy
        if denom < 1e-9:
            return 0.0
        return ((px - ax) * dx + (py - ay) * dy) / denom

    # Convert lines to internal structure
    lines_info = []
    for v in vectors:
        (x1, y1) = v["start"]
        (x2, y2) = v["end"]
        angle, dist = line_angle_and_offset(x1, y1, x2, y2)
        lines_info.append({
            "start": (x1, y1),
            "end": (x2, y2),
            "angle": angle,
            "dist": dist
        })

    # Attempt merges in a loop until no more merges occur
    merged_something = True
    while merged_something:
        merged_something = False
        new_lines = []
        used = [False] * len(lines_info)

        for i in range(len(lines_info)):
            if used[i]:
                continue
            lineA = lines_info[i]
            ax1, ay1 = lineA["start"]
            ax2, ay2 = lineA["end"]
            angleA, distA = lineA["angle"], lineA["dist"]

            dxA, dyA = ax2 - ax1, ay2 - ay1
            lenA = math.hypot(dxA, dyA)
            if lenA < 1e-9:
                used[i] = True
                continue

            best_j = -1
            merged_line = None

            for j in range(i + 1, len(lines_info)):
                if used[j]:
                    continue
                lineB = lines_info[j]
                bx1, by1 = lineB["start"]
                bx2, by2 = lineB["end"]
                angleB, distB = lineB["angle"], lineB["dist"]

                # angle difference
                dAngle = abs(angleA - angleB)
                if dAngle > 90:
                    dAngle = 180 - dAngle

                # if nearly parallel and close in normal-dist
                if dAngle <= angle_thresh_deg and abs(distA - distB) < dist_thresh:
                    # unify them by param projection
                    all_points = [(ax1, ay1), (ax2, ay2), (bx1, by1), (bx2, by2)]
                    tvals = []
                    for (px, py) in all_points:
                        tvals.append(project_param(px, py, ax1, ay1, dxA, dyA))
                    tmin, tmax = min(tvals), max(tvals)
                    new_start = (ax1 + dxA * tmin, ay1 + dyA * tmin)
                    new_end = (ax1 + dxA * tmax, ay1 + dyA * tmax)

                    angleC, distC = line_angle_and_offset(new_start[0], new_start[1],
                                                          new_end[0], new_end[1])
                    merged_line = {
                        "start": new_start,
                        "end": new_end,
                        "angle": angleC,
                        "dist": distC
                    }
                    best_j = j
                    break

            if best_j >= 0 and merged_line is not None:
                used[i] = True
                used[best_j] = True
                new_lines.append(merged_line)
                merged_something = True
            else:
                used[i] = True
                new_lines.append(lineA)

        lines_info = new_lines

    # Convert back to same format (use width=5 by default)
    final = []
    for ln in lines_info:
        final.append({
            "start": ln["start"],
            "end": ln["end"],
            "width": 5  # or keep old width if you want
        })
    return final