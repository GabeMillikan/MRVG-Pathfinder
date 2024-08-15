from typing import Sequence


class AABB:
    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: object) -> bool:
        return self is other

    @classmethod
    def from_points(
        cls,
        points: Sequence[tuple[float, float]],
        data: object | None = None,
    ) -> "AABB":
        if not points:
            return AABB(0, 0, 1, 1, data)

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

        return AABB(min_x, min_y, max_x, max_y, data)

    def __init__(
        self,
        left: float,
        bottom: float,
        right: float,
        top: float,
        data: object | None = None,
    ) -> None:
        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top
        self.data = data

        self.x = (self.left + self.right) / 2
        self.y = (self.left + self.right) / 2

    @property
    def quadrant_one(self) -> "AABB":  # upper right
        return AABB(self.x, self.y, self.right, self.top, self.data)

    @property
    def quadrant_two(self) -> "AABB":  # upper left
        return AABB(self.left, self.y, self.x, self.top, self.data)

    @property
    def quadrant_three(self) -> "AABB":  # lower left
        return AABB(self.left, self.bottom, self.x, self.y, self.data)

    @property
    def quadrant_four(self) -> "AABB":  # lower right
        return AABB(self.x, self.bottom, self.right, self.y, self.data)

    @property
    def expand_as_quadrant_one(self) -> "AABB":
        return AABB(
            2 * self.left - self.right,
            2 * self.bottom - self.top,
            self.right,
            self.top,
            self.data,
        )

    @property
    def expand_as_quadrant_two(self) -> "AABB":
        return AABB(
            self.left,
            2 * self.bottom - self.top,
            2 * self.right - self.left,
            self.top,
            self.data,
        )

    @property
    def expand_as_quadrant_three(self) -> "AABB":
        return AABB(
            self.left,
            self.bottom,
            2 * self.right - self.left,
            2 * self.top - self.bottom,
            self.data,
        )

    @property
    def expand_as_quadrant_four(self) -> "AABB":
        return AABB(
            2 * self.left - self.right,
            self.bottom,
            self.right,
            2 * self.top - self.bottom,
            self.data,
        )

    def copy(self) -> "AABB":
        return AABB(self.left, self.bottom, self.right, self.top, self.data)

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

    def with_aspect_ratio(self, width_over_height: float) -> "AABB":
        c = self.copy()
        c.expand_inplace_to_aspect_ratio(width_over_height)
        return c

    def expand_inplace(self, f: float) -> None:
        px = (self.right - self.left) * f
        self.left -= px
        self.right += px

        py = (self.top - self.bottom) * f
        self.bottom -= py
        self.top += py

    def expand(self, f: float) -> "AABB":
        c = self.copy()
        c.expand_inplace(f)
        return c

    def with_positive_area(self) -> "AABB":
        c = self.copy()
        if c.top <= c.bottom:
            c.top = c.y + 0.1
            c.bottom = c.y - 0.1
        if c.right <= c.left:
            c.right = c.x + 0.1
            c.left = c.x - 0.1
        return c

    def __repr__(self) -> str:
        return f"AABB({self.left!r}, {self.bottom!r}, {self.right!r}, {self.top!r}, {self.data!r})"


__all__ = ["AABB"]
