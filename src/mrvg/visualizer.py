from math import ceil
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
        *,
        grid: float = 0,
    ) -> None:
        self.graph = graph
        self.paths = list(paths)
        self.width = width
        self.height = height
        self.grid = grid

        self.update()

    def calculate_coordinate_bounds(self) -> tuple[float, float, float, float]:
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        point_generators = [
            (point for path in self.paths for point in path),
            (vertex for o in self.graph.obstacles for vertex in o.vertex_map),
        ]

        for points in point_generators:
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
        height *= 1.1
        width *= 1.1

        # fit to window; avoid messing with aspect ratio
        aspect_ratio_adjustment = (height / self.height) / (width / self.width)
        if aspect_ratio_adjustment > 1:
            # graph is too tall, add width
            pad = width * (aspect_ratio_adjustment - 1)
            min_x -= pad / 2
            max_x += pad / 2
        else:
            # graph is too wide, add height
            pad = height * (1 / aspect_ratio_adjustment - 1)
            min_x -= pad / 2
            max_x += pad / 2

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

        # grid
        if self.grid > 0:
            min_x, min_y, max_x, max_y = self.coordinate_bounds
            x = ceil(min_x / self.grid) * self.grid
            y = ceil(min_y / self.grid) * self.grid

            while x <= max_x:
                draw.line(
                    (
                        self.coordinates_to_pixel(x, min_y),
                        self.coordinates_to_pixel(x, max_y),
                    ),
                    (200, 200, 200),
                    1,
                )
                x += self.grid
            while y <= max_y:
                draw.line(
                    (
                        self.coordinates_to_pixel(min_x, y),
                        self.coordinates_to_pixel(max_x, y),
                    ),
                    (200, 200, 200),
                    1,
                )
                y += self.grid

        # obstacles
        for obstacle in self.graph.obstacles:
            draw.polygon(
                [self.coordinates_to_pixel(*point) for point in obstacle.vertex_map],
                (0, 0, 0),
            )

        # connections
        for node in self.graph._all_nodes():  # noqa: SLF001
            for other in node.connections.tuple:
                draw.line(
                    (
                        self.coordinates_to_pixel(node.x, node.y),
                        self.coordinates_to_pixel(other.x, other.y),
                    ),
                    (118, 30, 176),
                    2,
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
            draw.text(
                self.coordinates_to_pixel(node.x, node.y),
                str(len(node.connections.set)),
                stroke_width=1,
                stroke_fill=(0, 0, 0),
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
