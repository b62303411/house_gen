from decimal import Decimal


def decimal_dot(ax, ay, bx, by):
    """
    Dot product using Decimal
    """
    return ax * bx + ay * by

def decimal_cross(ax, ay, bx, by):
    """
    2D cross product (ax,ay) x (bx,by) = ax*by - ay*bx
    """
    return ax * by - ay * bx

def decimal_hypot(dx, dy):
    """
    Equivalent of math.hypot(dx, dy) but for Decimals
    sqrt(dx^2 + dy^2)
    """
    return (dx * dx + dy * dy).sqrt()

def combine_segments_decimal(a,
                            b,
                            eps=Decimal('1e-9')):
    """
    Combine two line segments into one bounding segment, using Decimal to avoid float rounding.

    Each segment is defined by:
      - center_x (cx), center_y (cy)
      - direction_x (dx), direction_y (dy)  (not necessarily normalized)
      - length

    Steps:
      1) Check that directions are parallel or anti-parallel
      2) Flip one direction if needed, so they point roughly the same way
      3) Convert directions to Decimal, normalize
      4) Compute start/end points in 2D using Decimals
      5) Project to 1D, find min start and max end
      6) The new bounding segment = [min_start, max_end]
         new length = max_end - min_start
         new center = midpoint in 1D, mapped back to 2D
         new direction = normalized direction of the first segment
    """
    a_c,a_d,a_l=  a.get_definition()
    b_c, b_d, b_l=  b.get_definition()
    cx1, cy1 = a_c[0],a_c[1]
    cx2, cy2 = b_c[0], b_c[1]
    dx1,dy1 = a_d[0],a_d[1]
    dx2, dy2 = b_d[0], b_d[1]

    # Convert inputs to Decimal
    cx1, cy1 = map(Decimal, (cx1, cy1))
    dx1, dy1 = map(Decimal, (dx1, dy1))
    length1  = Decimal(a_l)

    cx2, cy2 = map(Decimal, (cx2, cy2))
    dx2, dy2 = map(Decimal, (dx2, dy2))
    length2  = Decimal(b_l)

    # 1) Check parallel via cross product
    cross_dir = decimal_cross(dx1, dy1, dx2, dy2)
    if cross_dir.copy_abs() > eps:
        raise ValueError("Segments not parallel => cannot combine on the same axis.")

    # 2) If the dot product is negative, flip the second direction
    dot_dir = decimal_dot(dx1, dy1, dx2, dy2)
    if dot_dir < 0:
        dx2, dy2 = -dx2, -dy2

    # 3) Normalize the first direction for final use
    mag1 = decimal_hypot(dx1, dy1)
    if mag1.copy_abs() < eps:
        raise ValueError("Degenerate direction for first segment.")
    dirx = dx1 / mag1
    diry = dy1 / mag1

    # 4) Start/End for each segment
    # segment A
    halfA = length1 / Decimal(2)
    start1x = cx1 - (halfA * dirx)
    start1y = cy1 - (halfA * diry)
    end1x   = cx1 + (halfA * dirx)
    end1y   = cy1 + (halfA * diry)

    # segment B
    halfB = length2 / Decimal(2)
    start2x = cx2 - (halfB * dirx)
    start2y = cy2 - (halfB * diry)
    end2x   = cx2 + (halfB * dirx)
    end2y   = cy2 + (halfB * diry)

    # 5) Project onto dir -> 1D coordinates
    s1 = decimal_dot(start1x, start1y, dirx, diry)
    e1 = decimal_dot(end1x, end1y, dirx, diry)
    s2 = decimal_dot(start2x, start2y, dirx, diry)
    e2 = decimal_dot(end2x, end2y, dirx, diry)

    min_s = min(s1, s2)
    max_e = max(e1, e2)

    # 6) Construct bounding segment
    new_length = max_e - min_s
    if new_length < 0:
        raise ValueError("Calculated negative length => segments must not overlap or data invalid.")

    mid_1d = (min_s + max_e) / Decimal(2)

    new_cx = mid_1d * dirx
    new_cy = mid_1d * diry

    return (new_cx, new_cy, dirx, diry, new_length)