from math import dist as distance

from .path import Path, PathNode

class Pathfinder:
    def __init__(self):
        self.configure()
    
    def configure(self, radius=0):
        self.radius = radius

    def weigh_segment(self, x1, y1, x2, y2):
        return distance((x1, y1), (x2, y2))

    def find(self, graph, from_node, to_node):
        # expand vars so that time isn't wasted looking them up
        x1, y1 = from_node
        x2, y2 = to_node
        weigh_segment = self.weigh_segment
        obstacles = graph.obstacles
        nodes = graph.nodes
        
        # TODO
        
        return Path([
            PathNode(x1, y1, 0),
            PathNode(x2, y2, weigh_segment(x1, y1, x2, y2)),
        ])