from typing import Generator, Sequence

from .obstacle import Obstacle


class Graph:
    def __init__(
        self,
        obstacles: Sequence[tuple[float, float, float, float] | Obstacle] = (),
    ) -> None:
        self._obstacles = [
            o if isinstance(o, Obstacle) else Obstacle(*o) for o in obstacles
        ]

    @property
    def obstacles(self) -> Generator[Obstacle, None, None]:
        yield from self._obstacles

    def find_path(
        self,
        start_point: tuple[float, float],
        end_point: tuple[float, float],
    ) -> list[tuple[float, float]] | None:
        return [start_point, end_point]


__all__ = ["Graph"]
