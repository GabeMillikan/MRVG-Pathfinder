def bubble_sort(a, b):
    if a < b:
        return a, b
    else:
        return b, a

class Obstacle:
    def __init__(self, x1, y1, x2, y2, buffer = 0):
        self.x1, self.x2 = bubble_sort(x1, x2)
        self.y1, self.y2 = bubble_sort(y1, y2)
        self.buffer = buffer
        
        self.width = self.x2 - self.x1
        self.height = self.y2 - self.y1
    
    def __hash__(self):
        return id(self)