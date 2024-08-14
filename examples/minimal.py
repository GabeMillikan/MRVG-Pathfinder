import mrvg

graph = mrvg.Graph(
    [
        # simple "+" shape
        mrvg.Rectangle(-5, -1, 5, 1),
        mrvg.Rectangle(-1, -5, 1, 5),
    ],
)

path = graph.find_path((-2, -2), (2, 2))
assert path

mrvg.Visualizer(
    graph,
    [path],
    grid=2,
).display()
