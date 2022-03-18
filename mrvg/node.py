class Node:
    def __init__(self, x, y, visible = {}, concave = False):
        self.x, self.y = x, y
        self.visible = visible
        self.concave = concave
    
    def __hash__(self):
        return id(self)
