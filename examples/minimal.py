import mrvg

graph = mrvg.Graph(
    [
        (1, 1, 2, 3),
        (2, 2, 3, 3),
    ],
)

path = graph.find_path((0, 0), (4, 4))
assert path, "No path exists!"
mrvg.Visualizer(graph, [path]).display()
