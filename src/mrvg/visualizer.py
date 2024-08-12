from itertools import chain
from typing import Sequence

from PIL import Image, ImageDraw

from .graph import Graph


class Visualizer:
    def __init__(
        self,
        graph: Graph,
        paths: Sequence[Sequence[tuple[float, float]]] = (),
        width: int = 400,
        height: int = 400,
    ) -> None:
        self.graph = graph
        self.paths = paths
        self.width = width
        self.height = height

        self.update()

    def calculate_coordinate_bounds(self) -> tuple[float, float, float, float]:
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        for points in chain(self.paths, (o.points for o in self.graph.obstacles)):
            for x, y in points:
                if x < min_x:
                    min_x = x
                if y < min_y:
                    min_y = y
                if x > max_x:
                    max_x = x
                if y > max_y:
                    max_y = y

        if min_x > max_x:
            min_x = 0
            max_x = 1

        if min_y > max_y:
            min_y = 0
            max_y = 1

        width = max_x - min_x
        height = max_y - min_y

        # 5% padding on all sides
        min_x -= width * 0.05
        max_x += width * 0.05
        min_y -= height * 0.05
        max_y += height * 0.05

        return min_x, min_y, max_x, max_y

    def coordinates_to_pixel(self, x: float, y: float) -> tuple[float, float]:
        b_x0, b_y0, b_x1, b_y1 = self.coordinate_bounds
        return (
            self.width * (x - b_x0) / (b_x1 - b_x0),
            self.height * (b_y1 - y) / (b_y1 - b_y0),
        )

    def update(self) -> None:
        self.coordinate_bounds = self.calculate_coordinate_bounds()
        self.image = Image.new("RGB", (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(self.image)

        # obstacles
        for obstacle in self.graph.obstacles:
            draw.polygon(
                [self.coordinates_to_pixel(*point) for point in obstacle.points],
                (0, 0, 0),
            )

        # connections
        for node in self.graph._all_nodes():  # noqa: SLF001
            for other in node.connections.all:
                draw.line(
                    (
                        self.coordinates_to_pixel(node.x, node.y),
                        self.coordinates_to_pixel(other.x, other.y),
                    ),
                    (118, 30, 176),
                )
            draw.circle(
                self.coordinates_to_pixel(node.x, node.y),
                2,
                (121, 156, 163) if node.concave else (5, 96, 161),
            )

        # nodes
        for node in self.graph._all_nodes():  # noqa: SLF001
            draw.circle(
                self.coordinates_to_pixel(node.x, node.y),
                2,
                (121, 156, 163) if node.concave else (5, 96, 161),
            )

        for path in self.paths:
            for a, b in zip(path, path[1:]):
                draw.line(
                    (
                        self.coordinates_to_pixel(*a),
                        self.coordinates_to_pixel(*b),
                    ),
                    (255, 0, 0),
                )

    def display(self, title: str | None = None) -> None:
        self.image.show(title)


__all__ = ["Visualizer"]
