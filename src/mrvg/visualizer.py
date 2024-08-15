from math import ceil
from typing import Sequence

from PIL import Image, ImageDraw

from .bounding_box import AABB
from .graph import Graph


class Visualizer:
    def __init__(
        self,
        graph: Graph,
        paths: Sequence[Sequence[tuple[float, float]]] = (),
        width: int = 512,
        height: int = 512,
        *,
        grid: float = 0,
        draw_obstacles: bool = True,
        draw_nodes: bool = False,
        draw_paths: bool = True,
        draw_connections: bool = True,
    ) -> None:
        self.graph = graph
        self.paths = list(paths)
        self.width = width
        self.height = height
        self.grid = grid
        self.draw_obstacles = draw_obstacles
        self.draw_connections = draw_connections
        self.draw_paths = draw_paths
        self.draw_nodes = draw_nodes

        self.update()

    def _draw_grid(self, draw: ImageDraw.ImageDraw) -> None:
        b = self.coordinate_bounds
        x = ceil(b.left / self.grid) * self.grid
        y = ceil(b.bottom / self.grid) * self.grid

        while x <= b.right:
            draw.line(
                (
                    self.coordinates_to_pixel(x, b.bottom),
                    self.coordinates_to_pixel(x, b.top),
                ),
                (200, 200, 200),
                1,
            )
            draw.text(
                self.coordinates_to_pixel(x, b.bottom),
                f"{x:g}",
                stroke_width=1,
                stroke_fill=(0, 0, 0),
                anchor="mb",
            )
            x += self.grid
        while y <= b.top:
            draw.line(
                (
                    self.coordinates_to_pixel(b.left, y),
                    self.coordinates_to_pixel(b.right, y),
                ),
                (200, 200, 200),
                1,
            )
            draw.text(
                self.coordinates_to_pixel(b.left, y),
                f"{y:g}",
                stroke_width=1,
                stroke_fill=(0, 0, 0),
                anchor="lm",
            )
            y += self.grid

    def _draw_obstacles(self, draw: ImageDraw.ImageDraw) -> None:
        for obstacle in self.graph.obstacles:
            draw.polygon(
                [self.coordinates_to_pixel(*point) for point in obstacle.vertex_map],
                (0, 0, 0),
            )

    def _draw_connections(self, draw: ImageDraw.ImageDraw) -> None:
        for node in self.graph._nodes.values():  # noqa: SLF001
            for other in node.connections.tuple:
                draw.line(
                    (
                        self.coordinates_to_pixel(node.x, node.y),
                        self.coordinates_to_pixel(other.x, other.y),
                    ),
                    (66, 100, 168),
                    1,
                )

    def _draw_paths(self, draw: ImageDraw.ImageDraw) -> None:
        for path in self.paths:
            for a, b in zip(path, path[1:]):
                draw.line(
                    (
                        self.coordinates_to_pixel(*a),
                        self.coordinates_to_pixel(*b),
                    ),
                    (209, 6, 162),
                    3,
                )
            draw.circle(self.coordinates_to_pixel(*path[0]), 3, (181, 5, 43))
            draw.circle(self.coordinates_to_pixel(*path[-1]), 3, (7, 145, 28))

    def _draw_nodes(self, draw: ImageDraw.ImageDraw) -> None:
        for node in self.graph._nodes.values():  # noqa: SLF001
            draw.circle(
                self.coordinates_to_pixel(node.x, node.y),
                4 if node.concave else 7,
                (121, 156, 163) if node.concave else (5, 96, 161),
            )
            if not node.concave:
                draw.text(
                    self.coordinates_to_pixel(node.x, node.y),
                    str(len(node.connections.map)),
                    stroke_width=1,
                    stroke_fill=(0, 0, 0),
                    anchor="mm",
                )

    def calculate_coordinate_bounds(self) -> AABB:
        return (
            AABB.from_points(
                [
                    *(point for path in self.paths for point in path),
                    *(vertex for o in self.graph.obstacles for vertex in o.vertex_map),
                ],
            )
            .with_aspect_ratio(self.width / self.height)
            .expand(0.05)
        )

    def coordinates_to_pixel(self, x: float, y: float) -> tuple[float, float]:
        b = self.coordinate_bounds
        return (
            self.width * (x - b.left) / (b.right - b.left),
            self.height * (b.right - y) / (b.top - b.bottom),
        )

    def update(self) -> None:
        self.coordinate_bounds = self.calculate_coordinate_bounds()
        self.image = Image.new("RGB", (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(self.image)

        # grid
        if self.grid > 0:
            self._draw_grid(draw)

        if self.draw_obstacles:
            self._draw_obstacles(draw)

        if self.draw_connections:
            self._draw_connections(draw)

        if self.draw_paths:
            self._draw_paths(draw)

        if self.draw_nodes:
            self._draw_nodes(draw)

    def display(self, title: str | None = None) -> None:
        self.image.show(title)


__all__ = ["Visualizer"]
