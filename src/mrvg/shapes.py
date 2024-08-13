from dataclasses import dataclass
from typing import Generator, Literal, Sequence, TypeAlias

Pair: TypeAlias = tuple[float, float]


def _cross_product(v1: Pair, v2: Pair) -> float:
    return v1[0] * v2[1] - v1[1] * v2[0]


def _vec_subtract(v1: Pair, v2: Pair) -> Pair:
    return v1[0] - v2[0], v1[1] - v2[1]


def _line_segments_intersect(
    o0: Pair,  # origin
    d0: Pair,  # direction (magnitude is length of line)
    o1: Pair,
    d1: Pair,
) -> bool:
    """
    An intersection occurs even if an endpoint is
    incident, or if the lines are overlapping.
    """

    # AABB check
    if min(o0[0], o0[0] + d0[0]) > max(o1[0], o1[0] + d1[0]):
        return False
    if min(o1[0], o1[0] + d1[0]) > max(o0[0], o0[0] + d0[0]):
        return False
    if min(o0[1], o0[1] + d0[1]) > max(o1[1], o1[1] + d1[1]):
        return False
    if min(o1[1], o1[1] + d1[1]) > max(o0[1], o0[1] + d0[1]):
        return False

    d0_cross_d1 = _cross_product(d0, d1)
    o1_minus_o0 = _vec_subtract(o1, o0)
    return (
        0 <= _cross_product(o1_minus_o0, d1) <= d0_cross_d1
        and 0 <= _cross_product(o1_minus_o0, d0) <= d0_cross_d1
    )


@dataclass
class Vertex:
    x: float
    y: float

    convex: bool

    vec_from_prev_vertex: tuple[float, float]
    vec_to_next_vertex: tuple[float, float]


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

    def vertex_vector_direction_too_narrow(
        self,
        v: tuple[float, float],
        x: float,
        y: float,
    ) -> Literal[0, 1, 2]:  # 0: not too narrow, 1: parallel, 2: too narrow
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
        $(\vec{a} \cross \vec{b}) \cdot (\vec{b} \cross \vec{c}) \leq 0$
        then $\vec{b}$ is "within" the a-b span. Note that $\vec{-b}$
        simplifies to the same inequality, so we don't need to re-process.

        Let $\vec{a}$ be the the edge pointing towards $vert$ and let
        $\vec{b}$ be the edge pointing from $vert$ to the following vertex.
        """
        a_x, a_y = vert.vec_from_prev_vertex
        c_x, c_y = vert.vec_to_next_vertex

        result = (a_x * y - a_y * x) * (x * c_y - y * c_x)
        if result < 0:
            return 2
        if result == 0:
            return 1
        return 0

    def includes_point(self, x: float, y: float) -> bool:
        raise NotImplementedError

    def perimeter_intersects_line(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
    ) -> bool:
        # TODO: optimize this

        if len(self.vertices) < 2:
            return False

        origin = x0, y0
        direction = x1 - x0, y1 - y0

        for v in self.vertices[:-1]:
            if _line_segments_intersect(
                origin,
                direction,
                (v.x, v.y),
                v.vec_to_next_vertex,
            ):
                return True

        return False


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
