from threading import Lock
from typing import Generator, Sequence

from .node import Node
from .shapes import Polygon


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
        # TODO: optimize this using a quad tree
        for o in self._obstacles:
            if o.includes_point(node.x, node.y):
                yield o

    def _all_nodes(self) -> Generator[Node, None, None]:
        for row in self._nodes.values():
            yield from row.values()

    def _add_obstacle_locked(
        self,
        obstacle: Polygon,
    ) -> None:
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
                node.connections.sever()

        # sever connections blocked by the new obstacle
        for node in self._all_nodes():
            if node.concave:
                continue

            # immediately blocked because the connection now
            # points towards an interior angle
            if obstacle in node.encompassing_obstacles.convex:
                vertex = node.x, node.y
                for other in node.connections.tuple:
                    if obstacle.vertex_vector_direction_too_narrow(
                        vertex,
                        other.x - node.x,
                        other.y - node.y,
                    ):
                        node.connections.sever(other)

                continue

            for other in node.connections.tuple:
                # TODO: do a really quick distance squared test first
                if obstacle.perimeter_intersects_line(
                    node.x,
                    node.y,
                    other.x,
                    other.y,
                ):
                    node.connections.sever(other)

        # create connections to and from new convex nodes
        for node in created_convex_nodes:
            vertex = node.x, node.y
            for other in self._all_nodes():
                if node is other:
                    continue

                if other.concave:
                    continue

                if other in node.connections.set:
                    continue

                if any(
                    o.vertex_vector_direction_too_narrow(
                        vertex,
                        other.x - node.x,
                        other.y - node.y,
                    )
                    >= (2 if (other.x, other.y) in o.vertex_map else 1)
                    for o in node.encompassing_obstacles.convex
                ):
                    print(
                        "Skipping",
                        node,
                        "to",
                        other,
                        "link due to narrow vertex vector",
                    )
                    continue

                if self._raycast_between_nodes(node, other):
                    print("Skipping", node, "to", other, "link due to raycast")
                    continue

                print("Linked", node, "to", other)
                node.connections.link(other)

        # store the new obstacle
        self._obstacles.add(obstacle)

    def _raycast_between_nodes(self, n0: Node, n1: Node) -> Polygon | None:
        # TODO: optimize with quad tree + distance squared check?
        for obstacle in self._obstacles:
            if obstacle.perimeter_intersects_line(n0.x, n0.y, n1.x, n1.y):
                return obstacle

        return None

    def add_obstacle(self, obstacle: Polygon) -> None:
        with self._lock:
            self._add_obstacle_locked(obstacle)

    def find_path(
        self,
        start_point: tuple[float, float],
        end_point: tuple[float, float],
    ) -> list[tuple[float, float]] | None:
        return [start_point, end_point]


__all__ = ["Graph"]
