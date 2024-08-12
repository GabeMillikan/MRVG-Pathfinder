from typing import Iterable

from .obstacle import BaseObstacle


class TouchingObstacles:
    # This class tracks the "concavity" of touched obstacles.
    # If the node touches any obstacle at any location that
    # isn't a convex point (i.e. yielded from BaseObstacle.convex_points)
    # then the node is said to be "at a concave location", which
    # implies that the node is entirely useless for pathfinding.
    # No optimal path could ever visit a concave node.

    def __init__(self) -> None:
        self.convex: set[BaseObstacle] = set()
        self.all: set[BaseObstacle] = set()

        self.concave_count = 0

    def add(self, obstacle: BaseObstacle, is_convex: bool) -> bool:
        self.all.add(obstacle)

        if is_convex:
            became_concave = False
            self.convex.add(obstacle)
        else:
            became_concave = self.concave_count == 0
            self.concave_count += 1

        return became_concave

    def update(self, obstacles: Iterable[BaseObstacle], is_convex: bool) -> bool:
        obstacles = tuple(obstacles)
        self.all.update(obstacles)

        if is_convex:
            became_concave = False
            self.convex.update(obstacles)
        else:
            became_concave = self.concave_count == 0 and len(obstacles) > 0
            self.concave_count += len(obstacles)

        return became_concave

    def remove(self, obstacle: BaseObstacle) -> bool:
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
        self.outgoing: set["Node"] = set()
        self.incoming: set["Node"] = set()
        self.node = node

    def link_in(self, from_other: "Node") -> None:
        from_other.connections.outgoing.add(self.node)
        self.incoming.add(from_other)

    def link_out(self, to_other: "Node") -> None:
        self.outgoing.add(to_other)
        to_other.connections.incoming.add(self.node)

    def link(self, other: "Node") -> None:
        self.link_in(other)
        self.link_out(other)

    def sever_in(self, from_other: "Node") -> None:
        self.incoming.remove(from_other)
        from_other.connections.outgoing.remove(self.node)

    def sever_out(self, to_other: "Node") -> None:
        self.outgoing.remove(to_other)
        to_other.connections.incoming.remove(self.node)

    def sever(self, node: "Node | None" = None) -> None:
        if node:
            if node in self.incoming:
                self.sever_in(node)
            if node in self.outgoing:
                self.sever_out(node)
        else:
            for n in self.incoming:
                n.connections.outgoing.remove(self.node)
            self.incoming.clear()

            for n in self.outgoing:
                n.connections.incoming.remove(self.node)
            self.outgoing.clear()

    @property
    def all(self) -> set["Node"]:
        return {*self.outgoing, *self.incoming}


class Node:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.touching_obstacles = TouchingObstacles()
        self.connections = Connections(self)

    @property
    def concave(self) -> bool:
        return self.touching_obstacles.any_concave
