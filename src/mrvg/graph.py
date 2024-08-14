from threading import Lock
from typing import Generator, Literal, Sequence

from .node import Node
from .shapes import Polygon, RaycastResult


class Graph:
    def __init__(
        self,
        obstacles: Sequence[Polygon] = (),
    ) -> None:
        self._lock = Lock()
        self._obstacles: set[Polygon] = set()
        self._nodes: dict[float, dict[float, Node]] = {}  # nodes[y][x] = node

        for o in obstacles:
            self.add_obstacle(o)

    @property
    def obstacles(self) -> Generator[Polygon, None, None]:
        yield from self._obstacles

    def _get_or_create_node(self, x: float, y: float) -> tuple[Node, bool]:
        self._nodes.setdefault(y, {})
        node = self._nodes[y].get(x)

        if node:
            return node, False

        node = Node(x, y)
        self._nodes[y][x] = node
        return node, True

    def _get_encompassing_obstacles(
        self,
        node: Node,
    ) -> Generator[Polygon, None, None]:
        for o in self._obstacles:  # TODO: quad tree
            if o.includes_point(node.x, node.y):
                yield o

    def _all_nodes(self) -> Generator[Node, None, None]:
        for row in self._nodes.values():
            yield from row.values()

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
        for node in self._all_nodes():
            if obstacle in node.encompassing_obstacles.all:
                continue

            if not obstacle.includes_point(node.x, node.y):
                continue

            # must be concave because convex vertices were handled above
            became_concave = node.encompassing_obstacles.add(obstacle, False)
            if became_concave:
                print(
                    f"Severing {node} connections because it's now concave.",
                )
                node.connections.sever()

        # sever connections blocked by the new obstacle
        for node in self._all_nodes():
            if node.concave:
                continue

            for other in node.connections.tuple:
                # blocking (or useless) because too narrow...
                if (
                    obstacle in node.encompassing_obstacles.convex
                    and obstacle.vertex_vector_direction_too_narrow(
                        (node.x, node.y),
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

                if (node.x, node.y, other.x, other.y) == (2, 1, 2, 3):
                    print("RAYCAST FAILED (YIPPEE)")

        # create connections to and from new convex nodes
        for node in created_convex_nodes:
            for other in self._all_nodes():
                if node is other:
                    continue

                if other.concave:
                    continue

                if other in node.connections.set:
                    continue

                if any(
                    o.vertex_vector_direction_too_narrow(
                        (node.x, node.y),
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

        return []


__all__ = ["Graph"]
