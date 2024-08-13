import mrvg

graph = mrvg.Graph()
visualizer = mrvg.Visualizer(graph)

obstacles = [
    mrvg.Rectangle(1, 1, 2, 3),
    mrvg.Rectangle(2, 2, 3, 3),
]

for i, o in enumerate(obstacles, 1):
    print("ADDING", i)
    graph.add_obstacle(o)
    path = graph.find_path((0, 0), (4, 4))
    assert path, "No path exists!"

    visualizer.paths.append(path)
    visualizer.update()
    visualizer.display(f"{i} obstacle(s)")
