from threading import Lock
from typing import Generator, Sequence

from .node import Node
from .obstacle import BaseObstacle


class Graph:
    def __init__(
        self,
        obstacles: Sequence[BaseObstacle] = (),
    ) -> None:
        self._lock = Lock()
        self._obstacles: set[BaseObstacle] = set()
        self._nodes: dict[float, dict[float, Node]] = {}  # nodes[y][x] = node

        for o in obstacles:
            self.add_obstacle(o)

    @property
    def obstacles(self) -> Generator[BaseObstacle, None, None]:
        yield from self._obstacles

    def _get_or_create_node(self, x: float, y: float) -> tuple[Node, bool]:
        self._nodes.setdefault(y, {})
        node = self._nodes[y].get(x)

        if node:
            return node, False

        node = Node(x, y)
        self._nodes[y][x] = node

        # We know that these cannot be convex points because
        # otherwise the node would have already existed.
        node.touching_obstacles.update(self._get_convex_touching_obstacles(node), False)
        return node, True

    def _get_convex_touching_obstacles(
        self,
        node: Node,
    ) -> Generator[BaseObstacle, None, None]:
        # TODO: optimize this using a quad tree
        for o in self._obstacles:
            if o.touches_convex_hull(node.x, node.y):
                yield o

    def _all_nodes(self) -> Generator[Node, None, None]:
        for row in self._nodes.values():
            yield from row.values()

    def _get_newly_touching_nodes(
        self,
        obstacle: BaseObstacle,
    ) -> Generator[Node, None, None]:
        # TODO: optimize this using a quad tree
        for node in self._all_nodes():
            if obstacle in node.touching_obstacles.all:
                continue

            yield node

    def _add_obstacle_locked(
        self,
        obstacle: BaseObstacle,
    ) -> None:
        assert obstacle not in self._obstacles, "This obstacle is already in the graph."

        created_convex_nodes: set[Node] = set()

        # create or update nodes on each convex point on the obstacle
        for x, y in obstacle.convex_hull:
            node, created = self._get_or_create_node(x, y)
            became_concave = node.touching_obstacles.add(obstacle, True)
            if became_concave:
                node.connections.sever()
            elif created and not node.concave:
                created_convex_nodes.add(node)

        # check if this new obstacle touches any preexisting nodes
        for node in self._get_newly_touching_nodes(obstacle):
            became_concave = node.touching_obstacles.add(obstacle, False)
            if became_concave:
                node.connections.sever()

        for node in self._all_nodes():
            if node.concave:
                continue

            if obstacle in node.touching_obstacles.convex:
                # TODO: sever connections in the "useless" range from "important-optimization.png"
                continue

            for other in node.connections.all:
                # TODO: do a really quick distance squared test first
                if obstacle.line_blocked_by_convex_hull(
                    node.x,
                    node.y,
                    other.x,
                    other.y,
                ):
                    node.connections.sever(other)

        # create connections to and from new convex nodes
        for node in created_convex_nodes:
            for other in self._all_nodes():
                if other.concave:
                    continue

                # TODO: skip checks in the "useless" range from "important-optimization.png"

                if self._raycast_between_nodes(node, other):
                    continue

                node.connections.link(other)

        # store the new obstacle
        self._obstacles.add(obstacle)

    def _raycast_between_nodes(self, n0: Node, n1: Node) -> BaseObstacle | None:
        # TODO: optimize with quad tree + distance squared check?
        for obstacle in self._obstacles:
            if obstacle.line_blocked_by_convex_hull(n0.x, n0.y, n1.x, n1.y):
                return obstacle

        return None

    def _raycast_exact(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
    ) -> BaseObstacle | None:
        # TODO: optimize with quad tree + distance squared check?
        for obstacle in self._obstacles:
            if obstacle.blocks_line(x0, y0, x1, y1):
                return obstacle

        return None

    def add_obstacle(self, obstacle: BaseObstacle) -> None:
        with self._lock:
            self._add_obstacle_locked(obstacle)

    def find_path(
        self,
        start_point: tuple[float, float],
        end_point: tuple[float, float],
    ) -> list[tuple[float, float]] | None:
        return [start_point, end_point]


__all__ = ["Graph"]
