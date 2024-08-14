import math
from typing import Iterable

from .shapes import Polygon


class EncompassingObstacles:
    # This class tracks the "concavity" of encompassing obstacles.
    # If the node intersects any obstacle at any location that
    # isn't a convex point then the node is said to be
    # "at a concave location", which implies that the node
    # is entirely useless for pathfinding. No optimal path could
    # ever visit a concave node.

    def __init__(self) -> None:
        self.convex: set[Polygon] = set()
        self.all: set[Polygon] = set()

        self.concave_count = 0

    def add(self, obstacle: Polygon, is_convex: bool) -> bool:
        self.all.add(obstacle)

        if is_convex:
            became_concave = False
            self.convex.add(obstacle)
        else:
            became_concave = self.concave_count == 0
            self.concave_count += 1

        return became_concave

    def update(self, obstacles: Iterable[Polygon], is_convex: bool) -> bool:
        obstacles = tuple(obstacles)
        self.all.update(obstacles)

        if is_convex:
            became_concave = False
            self.convex.update(obstacles)
        else:
            became_concave = self.concave_count == 0 and len(obstacles) > 0
            self.concave_count += len(obstacles)

        return became_concave

    def remove(self, obstacle: Polygon) -> bool:
        self.all.remove(obstacle)

        if obstacle in self.convex:
            self.convex.remove(obstacle)
            became_convex = False
        else:
            self.concave_count -= 1
            became_convex = self.concave_count == 0

        return became_convex

    @property
    def any_concave(self) -> bool:
        return self.concave_count > 0

    def __bool__(self) -> bool:
        return len(self.all) > 0


class Connections:
    def __init__(self, node: "Node") -> None:
        self.map: dict["Node", float] = {}
        self.node = node

    def link(self, other: "Node") -> None:
        distance = math.dist((self.node.x, self.node.y), (other.x, other.y))
        self.map[other] = distance
        other.connections.map[self.node] = distance

    def sever(self, node: "Node | None" = None) -> None:
        if node:
            del self.map[node]
            del node.connections.map[self.node]
        else:
            for n in self.map:
                del n.connections.map[self.node]
            self.map.clear()

    @property
    def tuple(self) -> tuple["Node", ...]:
        return tuple(self.map)


class Node:
    def __init__(self, x: float, y: float) -> None:
        self.point = (x, y)
        self.encompassing_obstacles = EncompassingObstacles()
        self.connections = Connections(self)

    def __str__(self) -> str:
        return f"({self.x:g}, {self.y:g})"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)

    @property
    def concave(self) -> bool:
        return self.encompassing_obstacles.any_concave

    @property
    def x(self) -> float:
        return self.point[0]

    @property
    def y(self) -> float:
        return self.point[1]
