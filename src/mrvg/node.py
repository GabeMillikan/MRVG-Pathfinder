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
        self.set: set["Node"] = set()
        self.node = node

    def link(self, other: "Node") -> None:
        self.set.add(other)
        other.connections.set.add(self.node)

    def sever(self, node: "Node | None" = None) -> None:
        if node:
            self.set.remove(node)
            node.connections.set.remove(self.node)
        else:
            for n in self.set:
                n.connections.set.remove(self.node)
            self.set.clear()

    @property
    def tuple(self) -> tuple["Node", ...]:
        return tuple(self.set)


class Node:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.encompassing_obstacles = EncompassingObstacles()
        self.connections = Connections(self)

    def __str__(self) -> str:
        return f"({self.x:g}, {self.y:g})"

    @property
    def concave(self) -> bool:
        return self.encompassing_obstacles.any_concave
