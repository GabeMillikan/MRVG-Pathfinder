from math import dist as distance

class Pathfinder:
    def __init__(self, graph):
        self.graph = graph
    
    def weigh_segment(self, from_node, to_node):
        return distance(from_node, to_node)