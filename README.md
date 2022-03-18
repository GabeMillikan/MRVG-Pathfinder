### Modular Reduced Visibility Graph Pathfinder
Efficient omnidirectional pathfinding on 2D planes with arbitrarily placed rectangular obstacles (not grid-confined). 

- **Modular**: Obstacle are added & removed one-at-a-time. This means that you can add/delete/move a single obstacle without recalculating the entire navigation mesh. This is an extremely important optimization in scenarios where the majority of a map will remain unchanged while small portions of it do change. 
- **Reduced**: An optimization on the visibilty graph which removes nodes which cannot possibly be used in a pathfinding result (i.e. nodes on concave corners). Those calculations are instead performed up-front while adding/removing obstacles. 
- **Visibility Graph**: Every node stores a precalculated list of nodes which are visible from that node.
- **Pathfinder**: Determines the fastest way to get from one point to another, without hitting any obstacles. The "fastest way" is usually determined by shortest distance, but you can supply your own scoring function which returns the numeric value of a certain path segment and the pathfinder will minimize that.

# Quickstart Example
```py
import mrvg

g = mrvg.Graph([
    # x, y, x2, y2
    (1, 2, 4, 5),
    (0, 7, 9, 9),
])

path = g.find((0, 0), (10, 10))
print(f'The length of the path is {path.length} units')

g.visualize(path) # press any key to make this visualization go away
```

# Modular Example
```py
import mrvg

g = mrvg.Graph()

obstacle_to_delete = g.add_obstacle(4, 4, 5, 5)
g.add_obstacle(1, 2, 4, 5)
g.add_obstacle(0, 7, 9, 9)
g.remove_obstacle(obstacle_to_delete)

# Note: If you ever want to remove every obstacle,
# use g.clear() instead of removing them one-by-one.
# That will be significantly more efficient.

path = g.find((0, 0), (10, 10))
g.visualize(path)
```

# Complex Shapes
```py
# TODO
```

# Obstacle Buffers
The pathfinder will do its best to stay outside of these buffers unless it needs to squeeze through somewhere.
```py
# TODO
```

# Pathfinder Options
```py
# TODO
# show off g.pathfinder.configure()
```

# Custom Pathfinder Settings
```py
import mrvg

class CustomPathfinder(mrvg.Pathfinder):
    def weigh_segment(self, at_node, next_node):
        # nodes are just tuples of (x, y) coordinates
        x1, y1 = from_node
        x2, y2 = to_node
        
        # lets say that movements on the y-axis cost half as much
        y_dist = (y2 - y1) / 2
        x_dist = x2 - x1
        
        # normal distance formula
        return (x_dist ** 2 + y_dist ** 2) ** 0.5

g = mrvg.Graph(pathfinder=CustomPathfinder)

g.add_obstacle() # TODO

g.visualize(g.find())
```