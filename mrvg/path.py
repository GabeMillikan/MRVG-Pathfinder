class PathNode:
    def __init__(self, x, y, weight_from_last):
        self.x, self.y = x, y
        self.weight_from_last = weight_from_last

class Path:
    def __init__(self, path_nodes):
        self.nodes = path_nodes
        self.weight = sum(n.weight_from_last for n in path_nodes)
        
        # alias
        self.length = self.weight
