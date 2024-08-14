import bisect
import math
from dataclasses import dataclass
from threading import Lock
from typing import Generator, Sequence

from .node import Node
from .shapes import Polygon, RaycastResult


@dataclass
class PathfindingNode:
    point: tuple[float, float]
    g: float
    h: float
    previous: "PathfindingNode | None" = None

    @property
    def f(self) -> float:
        return self.g + self.h


class AStarSets:
    @staticmethod
    def open_sort_key(
        n: PathfindingNode,
    ) -> tuple[float, float, tuple[float, float], int]:
        return -n.f, n.g, n.point, id(n)

    def __init__(self) -> None:
        self.opened: dict[tuple[float, float], PathfindingNode] = {}
        self.closed: set[tuple[float, float]] = set()
        self.sorted_open: list[PathfindingNode] = []

    def take_best(self) -> PathfindingNode:
        pn = self.sorted_open.pop()
        del self.opened[pn.point]
        self.closed.add(pn.point)
        return pn

    def open(self, pn: PathfindingNode) -> None:
        existing = self.opened.get(pn.point)
        if existing:
            if pn.g >= existing.g:
                # proposed distance to point is longer
                # than existing distance to point (so
                # its worse), discard the update
                return

            i = bisect.bisect(
                self.sorted_open,
                AStarSets.open_sort_key(existing),
                key=AStarSets.open_sort_key,
            )
            del self.sorted_open[i]
            del self.opened[pn.point]

        bisect.insort(self.sorted_open, pn, key=AStarSets.open_sort_key)
        self.opened[pn.point] = pn


class Graph:
    def __init__(
        self,
        obstacles: Sequence[Polygon] = (),
    ) -> None:
        self._lock = Lock()
        self._obstacles: set[Polygon] = set()
        self._nodes: dict[tuple[float, float], Node] = {}  # nodes[(x, y)] = node

        for o in obstacles:
            self.add_obstacle(o)

    @property
    def obstacles(self) -> Generator[Polygon, None, None]:
        yield from self._obstacles

    def _get_or_create_node(self, x: float, y: float) -> tuple[Node, bool]:
        node = self._nodes.get((x, y))
        if node:
            return node, False

        node = Node(x, y)
        self._nodes[x, y] = node
        return node, True

    def _get_encompassing_obstacles(
        self,
        node: Node,
    ) -> Generator[Polygon, None, None]:
        for o in self._obstacles:  # TODO: quad tree
            if o.includes_point(*node.point):
                yield o

    def _add_obstacle_locked(
        self,
        obstacle: Polygon,
    ) -> None:
        print(f"Adding obstacle: {obstacle}")
        assert obstacle not in self._obstacles, "This obstacle is already in the graph."

        created_convex_nodes: set[Node] = set()

        # create or update nodes on each convex point on the obstacle
        for v in obstacle.vertices:
            if not v.convex:
                continue

            node, created = self._get_or_create_node(v.x, v.y)
            if created:
                node.encompassing_obstacles.update(
                    self._get_encompassing_obstacles(node),
                    False,  # cannot be convex because otherwise the node would've existed
                )
            became_concave = node.encompassing_obstacles.add(obstacle, True)
            if became_concave:
                node.connections.sever()

            if created and not node.concave:
                created_convex_nodes.add(node)

        # check if this new obstacle touches any preexisting nodes
        for node in self._nodes.values():
            if obstacle in node.encompassing_obstacles.all:
                continue

            if not obstacle.includes_point(*node.point):
                continue

            # must be concave because convex vertices were handled above
            became_concave = node.encompassing_obstacles.add(obstacle, False)
            if became_concave:
                print(
                    f"Severing {node} connections because it's now concave.",
                )
                node.connections.sever()

        # sever connections blocked by the new obstacle
        for node in self._nodes.values():
            if node.concave:
                continue

            for other in node.connections.tuple:
                # blocking (or useless) because too narrow...
                if (
                    obstacle in node.encompassing_obstacles.convex
                    and obstacle.vertex_vector_direction_too_narrow(
                        node.point,
                        other.x - node.x,
                        other.y - node.y,
                    )
                ):
                    print(
                        f"Severing {node} -> {other} because it's now outgoing too narrow.",
                    )
                    node.connections.sever(other)
                    continue

                # blocking by raycast...
                if self._node_raycast(node, other, obstacle).blocked:
                    print(f"Severing {node} -> {other} because it's now blocked.")
                    node.connections.sever(other)

        # create connections to and from new convex nodes
        for node in created_convex_nodes:
            for other in self._nodes.values():
                if node is other:
                    continue

                if other.concave:
                    continue

                if other in node.connections.map:
                    continue

                if any(
                    o.vertex_vector_direction_too_narrow(
                        node.point,
                        other.x - node.x,
                        other.y - node.y,
                    )
                    for o in node.encompassing_obstacles.convex
                ):  # TODO: quad tree - we shouldn't need to calculate this for _every_ node, just for regions
                    print(
                        f"Did not connect {node} -> {other} because it's outgoing too narrow.",
                    )
                    continue

                if any(
                    o.vertex_vector_direction_too_narrow(
                        (other.x, other.y),
                        node.x - other.x,
                        node.y - other.y,
                    )
                    for o in other.encompassing_obstacles.convex
                ):  # TODO: quad tree - we shouldn't need to calculate this for _every_ node, just for regions
                    print(
                        f"Did not connect {node} -> {other} because it's incoming to narrow.",
                    )
                    continue

                if self._node_raycast(node, other, obstacle).blocked:
                    print(f"Did not connect {node} -> {other} because it's blocked")
                    continue

                print(f"Connected {node} -> {other}")
                node.connections.link(other)

        # store the new obstacle
        self._obstacles.add(obstacle)

    def _node_raycast(
        self,
        n0: Node,
        n1: Node,
        prioritize_obstacle: Polygon | None = None,
    ) -> RaycastResult:
        return self.raycast(
            n0.x,
            n0.y,
            n1.x,
            n1.y,
            prioritize_obstacle,
        )

    def raycast(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        prioritize_obstacle: Polygon | None = None,
    ) -> RaycastResult:
        result = RaycastResult()
        if (
            prioritize_obstacle is not None
            and prioritize_obstacle.raycast(x0, y0, x1, y1, result).blocked
        ):
            return result

        for obstacle in self._obstacles:  # TODO: quad tree
            if obstacle is prioritize_obstacle:
                continue
            if obstacle.raycast(x0, y0, x1, y1, result).blocked:
                break

        return result

    def add_obstacle(self, obstacle: Polygon) -> None:
        with self._lock:
            self._add_obstacle_locked(obstacle)

    def find_path(
        self,
        start_point: tuple[float, float],
        end_point: tuple[float, float],
    ) -> list[tuple[float, float]] | None:
        if not self.raycast(*start_point, *end_point).blocked:
            return [start_point, end_point]

        start_node = self._nodes.get(start_point)
        end_node = self._nodes.get(end_point)

        sets = AStarSets()

        total_distance = math.dist(start_point, end_point)
        current = PathfindingNode(start_point, 0, total_distance)

        # initially populate the open/closed sets
        if start_node and not start_node.concave:
            sets.closed.add(start_point)

            for node, distance in start_node.connections.map.items():
                sets.open(
                    PathfindingNode(
                        node.point,
                        distance,
                        math.dist(node.point, end_point),
                        current,
                    ),
                )
        else:
            for node in self._nodes.values():
                if not node.connections.map:
                    continue

                if not self.raycast(*start_point, *node.point).blocked:
                    sets.open(
                        PathfindingNode(
                            node.point,
                            math.dist(start_point, node.point),
                            math.dist(node.point, end_point),
                            current,
                        ),
                    )

        # perform A* pathfinding until all open nodes
        # are closed, or until reaching the destination
        complete = False
        while sets.opened:
            current = sets.take_best()

            if current.point == end_point:
                complete = True
                break

            if (
                end_node is None
                and not self.raycast(*current.point, *end_point).blocked
            ):
                complete = True
                break

            for node, distance in self._nodes[current.point].connections.map.items():
                if node.point in sets.closed:
                    continue

                sets.open(
                    PathfindingNode(
                        node.point,
                        current.g + distance,
                        math.dist(node.point, end_point),
                        current,
                    ),
                )

        if not complete:
            # TODO: should allow at least something useful to be returned
            return None

        # rebuild the path
        path = [end_point]
        if current.point == end_point:
            current = current.previous

        while current:
            path.append(current.point)
            current = current.previous

        return path[::-1]


__all__ = ["Graph"]
