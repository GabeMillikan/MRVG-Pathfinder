from typing import Sequence


class AABB:
    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: object) -> bool:
        return self is other

    @classmethod
    def from_points(cls, points: Sequence[tuple[float, float]]) -> "AABB":
        if not points:
            return AABB(0, 0, 1, 1)

        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        for x, y in points:
            if x < min_x:
                min_x = x
            if y < min_y:
                min_y = y
            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y

        return AABB(min_x, min_y, max_x, max_y)

    def __init__(
        self,
        left: float,
        bottom: float,
        right: float,
        top: float,
    ) -> None:
        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top

        self.x = (self.left + self.right) / 2
        self.y = (self.bottom + self.top) / 2

    @property
    def quadrant_one(self) -> "AABB":  # upper right
        return AABB(self.x, self.y, self.right, self.top)

    @property
    def quadrant_two(self) -> "AABB":  # upper left
        return AABB(self.left, self.y, self.x, self.top)

    @property
    def quadrant_three(self) -> "AABB":  # lower left
        return AABB(self.left, self.bottom, self.x, self.y)

    @property
    def quadrant_four(self) -> "AABB":  # lower right
        return AABB(self.x, self.bottom, self.right, self.y)

    @property
    def expand_as_quadrant_one(self) -> "AABB":
        return AABB(
            2 * self.left - self.right,
            2 * self.bottom - self.top,
            self.right,
            self.top,
        )

    @property
    def expand_as_quadrant_two(self) -> "AABB":
        return AABB(
            self.left,
            2 * self.bottom - self.top,
            2 * self.right - self.left,
            self.top,
        )

    @property
    def expand_as_quadrant_three(self) -> "AABB":
        return AABB(
            self.left,
            self.bottom,
            2 * self.right - self.left,
            2 * self.top - self.bottom,
        )

    @property
    def expand_as_quadrant_four(self) -> "AABB":
        return AABB(
            2 * self.left - self.right,
            self.bottom,
            self.right,
            2 * self.top - self.bottom,
        )

    def copy(self) -> "AABB":
        return AABB(self.left, self.bottom, self.right, self.top)

    def expand_inplace_to_aspect_ratio(self, width_over_height: float) -> None:
        current_aspect_ratio = (self.right - self.left) / (self.top - self.bottom)

        if current_aspect_ratio < width_over_height:  # expand width
            padding = (self.top - self.bottom) * width_over_height / 2
            self.left = self.x - padding
            self.right = self.x + padding
        elif current_aspect_ratio > width_over_height:  # expand height
            padding = (self.right - self.left) / width_over_height / 2
            self.bottom = self.y - padding
            self.top = self.y + padding

    def expand_inplace(self, f: float) -> None:
        px = (self.right - self.left) * f
        self.left -= px
        self.right += px

        py = (self.top - self.bottom) * f
        self.bottom -= py
        self.top += py

    def expand_inplace_to_positive_area(self) -> None:
        if self.top <= self.bottom:
            self.top = self.y + 0.1
            self.bottom = self.y - 0.1
        if self.right <= self.left:
            self.right = self.x + 0.1
            self.left = self.x - 0.1

    def intersects_line_segment(
        self,
        ox: float,
        oy: float,
        dx: float,
        dy: float,
    ) -> bool:
        # Returns true even if just touching the boundary
        # https://en.wikipedia.org/wiki/Liang%E2%80%93Barsky_algorithm
        # ^ contains some incorrect details... read this instead:
        # https://gist.github.com/ChickenProp/3194723

        u_1 = 0
        u_2 = 1

        for p, q in (
            (-dx, ox - self.left),  # left edge
            (dx, self.right - ox),  # right edge
            (-dy, oy - self.bottom),  # bottom edge
            (dy, self.top - oy),  # top edge
        ):
            if p == 0:  # parallel
                if q < 0:  # not on the inner side
                    return False
                continue

            t = q / p
            if p < 0:
                if t > u_1:
                    u_1 = t
            elif t < u_2:
                u_2 = t

        return u_1 <= u_2 and u_1 <= 1 and u_2 >= 0

    def __repr__(self) -> str:
        return f"AABB({self.left!r}, {self.bottom!r}, {self.right!r}, {self.top!r})"


__all__ = ["AABB"]
