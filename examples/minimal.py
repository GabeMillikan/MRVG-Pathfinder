import mrvg

graph = mrvg.Graph(
    [
        mrvg.Rectangle(0, 0, 1, 1),
        mrvg.Rectangle(2, 2, 3, 3),
        mrvg.Rectangle(4, 4, 5, 5),
    ],
)
mrvg.Visualizer(
    graph,
    grid=1,
).display()
