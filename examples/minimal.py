import mrvg

graph = mrvg.Graph([mrvg.Rectangle(1, 1, 2, 3)])
visualizer = mrvg.Visualizer(
    graph,
    grid=1,
)
visualizer.display()

print("ADDING")
graph.add_obstacle(mrvg.Rectangle(2, 2, 3, 3))
visualizer.update()
visualizer.display()
