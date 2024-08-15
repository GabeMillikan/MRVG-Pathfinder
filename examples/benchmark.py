import cProfile

import mrvg

graph = mrvg.Graph(
    [
        mrvg.Rectangle(x - 0.25, y - 0.25, x + 0.25, y + 0.25)
        for x in range(5)
        for y in range(5)
    ],
)

o = mrvg.Rectangle(9, 9, 10, 10)
cProfile.run("graph.add_obstacle(o)", "benchmark")

import pstats
from pstats import SortKey

p = pstats.Stats("benchmark")
p.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats()

mrvg.Visualizer(graph).display()
