from abc import ABC, abstractmethod
from threading import Lock
from typing import ClassVar, Generator


class BaseObstacle(ABC):
    next_unique_id: ClassVar[int] = 1
    unique_id_lock: ClassVar[Lock] = Lock()

    @classmethod
    def take_next_unique_id(cls) -> int:
        with cls.unique_id_lock:
            cls.next_unique_id += 1
            return cls.next_unique_id - 1

    def __init__(self) -> None:
        self.unique_id = self.take_next_unique_id()

    def __eq__(self, other: "BaseObstacle") -> bool:
        return self.unique_id == other.unique_id

    def __hash__(self) -> int:
        return self.unique_id

    def line_blocked_by_convex_hull(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
    ) -> bool:
        # note: it's guaranteed that these points are not *inside* of the convex hull!
        # TODO: generic algorithm!
        return self.blocks_line(x0, y0, x1, y1)

    def blocks_line(self, x0: float, y0: float, x1: float, y1: float) -> bool:
        if self.is_convex:
            # TODO: optimize
            return (
                self.touches_convex_hull(x0, y0)
                or self.touches_convex_hull(x1, y1)
                or self.line_blocked_by_convex_hull(x0, y0, x1, y1)
            )

        # TODO: generic algorithm
        raise NotImplementedError

    def touches_convex_hull(self, x: float, y: float) -> bool:
        # TODO: use a generic algorithm!
        raise NotImplementedError

    def touches(self, x: float, y: float) -> bool:
        if self.is_convex:
            return self.touches_convex_hull(x, y)

        # TODO: use a generic algorithm!
        raise NotImplementedError

    @property
    @abstractmethod
    def points(self) -> Generator[tuple[float, float], None, None]: ...

    @property
    def convex_hull(self) -> Generator[tuple[float, float], None, None]:
        if self.is_convex:
            return self.points

        # TODO: build a convex hull automatically!
        raise NotImplementedError

    @property
    def is_convex(self) -> bool:
        return False


class Rectangle(BaseObstacle):
    def __init__(self, x0: float, y0: float, x1: float, y1: float) -> None:
        super().__init__()

        assert y0 is not None
        assert x1 is not None
        assert y1 is not None

        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    @property
    def is_convex(self) -> bool:
        return True

    @property
    def points(self) -> Generator[tuple[float, float], None, None]:
        yield (self.x0, self.y0)
        yield (self.x1, self.y0)
        yield (self.x1, self.y1)
        yield (self.x0, self.y1)

    def touches_convex_hull(self, x: float, y: float) -> bool:
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1

    def line_blocked_by_convex_hull(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
    ) -> bool:
        if y0 < y1:
            min_y, max_y = y0, y1
        else:
            min_y, max_y = y1, y0

        # handle vertical lines
        if x0 == x1:
            return (self.x0 < x0 < self.x1) and max_y > self.y0 and self.y1 > min_y

        if x0 < x1:
            min_x, max_x = x0, x1
        else:
            min_x, max_x = x1, x0

        # rise over run
        slope = (max_y - min_y) / (max_x - min_x)

        # bottom edge
        if min_y <= self.y0 < max_y:
            x_int = x1 + (self.y0 - y1) / slope
            if self.x0 < x_int < self.x1:
                return True

        # right edge
        if min_x < self.x1 <= max_x:
            y_int = slope * (self.x1 - x1) + y1
            if self.y0 < y_int < self.y1:
                return True

        # top edge
        if min_y < self.y1 <= max_y:
            x_int = x1 + (self.y1 - y1) / slope
            if self.x0 < x_int < self.x1:
                return True

        # left edge
        if min_x <= self.x0 < max_x:
            y_int = slope * (self.x0 - x1) + y1
            if self.y0 < y_int < self.y1:
                return True

        return False


__all__ = ["BaseObstacle", "Rectangle"]
