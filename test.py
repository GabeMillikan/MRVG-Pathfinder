import mrvg

g = mrvg.Graph([
    # x, y, x2, y2
    (1, 2, 4, 5),
    (0, 7, 9, 9),
])

path = g.find((0, 0), (10, 10))
print(f'The length of the path is {path.length} units')

g.visualize(path) # press any key to make this visualization go away
