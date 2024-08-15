import bisect
from dataclasses import dataclass, field
from typing import Any, Generator, Literal, Sequence, TypeAlias, TypeVar

from .bounding_box import AABB

Pair: TypeAlias = tuple[float, float]
Comparable = TypeVar("Comparable", bound=Any)


def _cross_product(v1: Pair, v2: Pair) -> float:
    return v1[0] * v2[1] - v1[1] * v2[0]


def _vec_subtract(v1: Pair, v2: Pair) -> Pair:
    return v1[0] - v2[0], v1[1] - v2[1]


@dataclass
class Vertex:
    x: float
    y: float

    convex: bool

    vec_from_prev_vertex: tuple[float, float]
    vec_to_next_vertex: tuple[float, float]


RaycastSegment: TypeAlias = tuple[
    float,  # start (percent of ray)
    float,  # stop (percent of ray)
    Literal[-1, 1],  # -1: graze left, 1: graze right
]


def _colinear_segments_overlapping_region(
    r_o: Pair,
    r_d: Pair,
    t_o: Pair,
    t_d: Pair,
) -> RaycastSegment | Literal[False]:
    r"""
    Given two colinear line segments:
    $$
        R(r) = R_o + rR_d, \quad 0 \leq r 1\leq \\
        T(t) = T_o + tT_d, \quad 0 \leq r 1\leq
    $$
    Find the interval of $r$ for which the lines are coincident.

    The math is quite straightforward and the answer comes out to be:
    $$
        k = \frac{T_{dx}}{R_{dx}} = \frac{T_{dy}}{R_{dy}} \\
        r_i = \frac{T_{ox} - R_{ox}}{R_{dx}} = \frac{T_{oy} - R_{oy}}{R_{dy}} \\
        r_f = r_i + k
    $$
    Where you can use any of the axes that don't have a zero denominator.
    """
    if abs(r_d[0]) > abs(r_d[1]):
        axis = 0
    else:
        axis = 1

    if r_d[axis] == 0:
        return False

    k = t_d[axis] / r_d[axis]
    r_i = (t_o[axis] - r_o[axis]) / r_d[axis]
    r_f = r_i + k

    if k < 0:
        r_i, r_f, side = r_f, r_i, -1
    else:
        side = 1

    if r_i > 1 or r_f < 0:
        return False

    return (max(0, r_i), min(1, r_f), side)


def _raycast_segment(
    r_o: Pair,  # origin of ray
    r_d: Pair,  # direction of ray (magnitude is length of line)
    t_o: Pair,  # origin of target line segment
    t_d: Pair,  # direction of target line segment (magnitude is length of line)
) -> RaycastSegment | bool:
    """
    An intersection occurs when the lines cross
    or if they are overlapping, but not when an
    endpoint is incident on the other segment.
    """
    rd_cross_td = _cross_product(r_d, t_d)
    delta_o = _vec_subtract(t_o, r_o)

    if rd_cross_td == 0:  # parallel
        if _cross_product(delta_o, r_d) != 0:  # not colinear
            return False

        return _colinear_segments_overlapping_region(
            r_o,
            r_d,
            t_o,
            t_d,
        )

    r_t = _cross_product(delta_o, t_d) / rd_cross_td
    if not (0 < r_t < 1):
        # point of intersection does not occur on the ray
        return False

    t_t = _cross_product(delta_o, r_d) / rd_cross_td
    if 0 < t_t < 1:
        # intersection is inside the target line
        return True

    if t_t == 0:
        return (r_t, r_t, 1 if rd_cross_td > 0 else -1)
    if t_t == 1:
        return (r_t, r_t, -1 if rd_cross_td > 0 else 1)

    return False


@dataclass
class RaycastResult:
    # when None, the Ray was fully blocked
    segments: list[RaycastSegment] | None = field(default_factory=list)

    def add_segment(self, segment: RaycastSegment) -> bool:
        if self.segments is None:
            return True

        start, stop, side = segment

        i = bisect.bisect_left(self.segments, (start, -float("inf"), -2))
        while i < len(self.segments):
            p_start, p_stop, p_side = self.segments[i]
            if p_start > start:
                break

            if p_side != side:
                self.segments = None
                return True

            stop = max(stop, p_stop)
            del self.segments[i]

        self.segments.insert(i, (start, stop, side))
        return False

    @property
    def blocked(self) -> bool:
        return self.segments is None

    @property
    def grazed(self) -> bool:
        return self.segments is not None and len(self.segments) > 0

    @property
    def free(self) -> bool:
        return self.segments is not None and len(self.segments) == 0


class Polygon:
    @staticmethod
    def _bake_vertices(
        ccw_vertices: Sequence[tuple[float, float]],
    ) -> Generator[Vertex, None, None]:
        n = len(ccw_vertices)
        if n < 2:
            for x, y in ccw_vertices:
                yield Vertex(x, y, True, (0, 0), (0, 0))
            return

        for i, (v_x, v_y) in enumerate(ccw_vertices):
            p_x, p_y = ccw_vertices[i - 1]  # previous vertex
            n_x, n_y = ccw_vertices[(i + 1) % n]  # next vertex

            r"""
            Determine if $\angle{pvn} < 180^\circ$ (i.e.
            that $v$ is a convex vertex) by checking if
            $\vec{pv} \cross \vec{vn} > 0$
            """
            pv_x, pv_y = v_x - p_x, v_y - p_y
            vn_x, vn_y = n_x - v_x, n_y - v_y
            pv_cross_vn = pv_x * vn_y - pv_y * vn_x

            yield Vertex(v_x, v_y, pv_cross_vn > 0, (pv_x, pv_y), (vn_x, vn_y))

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def __init__(
        self,
        counter_clockwise_vertices: Sequence[tuple[float, float]],
    ) -> None:
        self.vertices = tuple(self._bake_vertices(counter_clockwise_vertices))
        self.vertex_map = {(v.x, v.y): v for v in self.vertices}
        self.bounding_box = AABB.from_points(counter_clockwise_vertices)

    def vertex_vector_direction_too_narrow(
        self,
        v: tuple[float, float],
        x: float,
        y: float,
    ) -> bool:
        r"""
        Returns true if the line through $\vec{v}$ with direction $(x, y)$
        passes through the interior angle of the vertex at $\vec{v}$.
        This includes when $\vec{v}$ is parallel to the adjacent edges.
        It is assumed that $\vec{v}$ is a convex vertex in this Polygon.
        """
        vert = self.vertex_map[v]

        r"""
        Use the mathematical property that $\vec{b}$ is "between"
        vectors $\vec{a}$ and $\vec{c}$ if and only if the signs of
        $\vec{a} \cross \vec{b}$ and $\vec{b} \cross \vec{c}$
        are equal. Additionally, $\vec{b}$ is parallel to
        $\vec{a}$ or $\vec{c}$ if the corresponding product is zero.
        Therefore, if:
        $(\vec{a} \cross \vec{b}) \cdot (\vec{b} \cross \vec{c}) < 0$
        then $\vec{b}$ is "within" the a-b span. Note that $\vec{-b}$
        simplifies to the same inequality, so we don't need to re-process.

        Let $\vec{a}$ be the the edge pointing towards $vert$ and let
        $\vec{b}$ be the edge pointing from $vert$ to the following vertex.
        """
        a_x, a_y = vert.vec_from_prev_vertex
        c_x, c_y = vert.vec_to_next_vertex

        a_cross_b = a_x * y - a_y * x
        c_cross_b = x * c_y - y * c_x

        result = a_cross_b * c_cross_b
        return result < 0

    def includes_point(self, x: float, y: float) -> bool:
        raise NotImplementedError

    def raycast_segmented(
        self,
        origin: tuple[float, float],
        direction: tuple[float, float],  # where the magnitude is the length
    ) -> Generator[RaycastSegment | bool, None, None]:
        """
        Note that this isn't very well optimized
        because in most scenarios there is a better
        way to perform this calculation anyway.
        This (slow) method is provided just as an example
        of a mathematically complete solution.
        """

        if len(self.vertices) < 2:
            return

        for v in self.vertices:
            yield _raycast_segment(
                origin,
                direction,
                (v.x, v.y),
                v.vec_to_next_vertex,
            )

    def raycast(
        self,
        origin: tuple[float, float],
        direction: tuple[float, float],  # where the magnitude is the length
        update_result: RaycastResult | None = None,
    ) -> RaycastResult:
        r = RaycastResult() if update_result is None else update_result

        for segment in self.raycast_segmented(origin, direction):
            if segment is False:
                continue
            if segment is True or r.add_segment(segment):
                r.segments = None
                return r

        return r

    def __str__(self) -> str:
        return "[" + ", ".join(f"({v.x:g}, {v.y:g})" for v in self.vertices) + "]"


class Rectangle(Polygon):
    def __init__(self, left: float, bottom: float, right: float, top: float) -> None:
        super().__init__(
            (
                (left, bottom),
                (right, bottom),
                (right, top),
                (left, top),
            ),
        )

        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top

    def includes_point(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.bottom <= y <= self.top


__all__ = ["Polygon", "Rectangle"]
