import time

import mrvg

data = """
#####################
#A#               # #
# # # ######### ### #
#   #       #     # #
### ### ### # # ### #
#     # #   # #     #
# ### ### ### # # ###
# # # # #   # # #   #
# # # # ######### # #
# #   # #     # # # #
### # # ##### # # # #
#   #   # # # # # # #
# ####### # # # ### #
#     # #     #     #
# ### # ### # # #####
#   # # # # #       #
### # # # ##### ### #
#   #       # # #   #
# ### ##### # # # # #
#   #     #   # # #B#
#####################
"""


graph = mrvg.Graph()

for y, row in enumerate(data.splitlines()[::-1]):
    for x, v in enumerate(row):
        if v == "#":
            before = time.perf_counter()
            graph.add_obstacle(mrvg.Rectangle(x - 0.5, y - 0.5, x + 0.5, y + 0.5))
            print(f"Added {(x, y)} in {(time.perf_counter() - before) * 1000:.2f}ms")
            print()
        elif v == "A":
            start_point = (x, y)
        elif v == "B":
            end_point = (x, y)

path = graph.find_path(start_point, end_point)
assert path

mrvg.Visualizer(
    graph,
    [path],
).display()
