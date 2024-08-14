import mrvg

graph = mrvg.Graph(
    [
        mrvg.Rectangle(0, 0, 1, 1),
        mrvg.Rectangle(4, 0, 5, 1),
        mrvg.Rectangle(4, 4, 5, 5),
        mrvg.Rectangle(0, 4, 1, 5),
        mrvg.Rectangle(2, 2, 3, 3),
    ],
)

path = graph.find_path((-1, -1), (6, 6))
assert path

mrvg.Visualizer(
    graph,
    [path],
    grid=1,
).display()
