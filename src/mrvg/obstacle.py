from threading import Lock
from typing import ClassVar


class Obstacle:
    next_unique_id: ClassVar[int] = 1
    unique_id_lock: ClassVar[Lock] = Lock()

    @classmethod
    def take_next_unique_id(cls) -> int:
        with cls.unique_id_lock:
            cls.next_unique_id += 1
            return cls.next_unique_id - 1

    def __init__(self, x0: float, y0: float, x1: float, y1: float) -> None:
        assert y0 is not None
        assert x1 is not None
        assert y1 is not None

        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.unique_id = self.take_next_unique_id()

    def __eq__(self, other: "Obstacle") -> bool:
        return self.unique_id == other.unique_id

    def __hash__(self) -> int:
        return self.unique_id


__all__ = ["Obstacle"]
