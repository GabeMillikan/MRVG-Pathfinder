# builtins
import math

# visualization
import cv2, numpy as np

# MRVG
from .pathfinder import Pathfinder
from .obstacle import Obstacle

class Graph:
    def __init__(self, obstacles=[], pathfinder=Pathfinder):
        # `pathfinder` is a class, not an instance
        PathfinderClass = pathfinder
        self.pathfinder = PathfinderClass()
        
        # initialize obstacles & nodes
        self.nodes = set()
        self.obstacles = set()
        for o in obstacles:
            if not isinstance(o, Obstacle):
                o = Obstacle(*o)
            self.add_obstacle(o)
    
    def add_obstacle(self, o):
        self.obstacles.add(o)
    
    def visualize(self, path=None, width=400, height=400, title="graph", milliseconds=0):
        img = np.ones((height, width, 3), dtype='uint8') * 255
        
        # determine graph bounds:
        min_x, min_y, max_x, max_y = math.inf, math.inf, -math.inf, -math.inf
        for o in self.obstacles:
            min_x = min(min_x, o.x1)
            min_y = min(min_y, o.y1)
            max_x = max(max_x, o.x2)
            max_y = max(max_y, o.y2)
        
        if path:
            for node in path.nodes:
                min_x = min(min_x, node.x)
                min_y = min(min_y, node.y)
                max_x = max(max_x, node.x)
                max_y = max(max_y, node.y)
        
        graph_width, graph_height = max_x - min_x, max_y - min_y
        print(graph_width, graph_height)
        
        # make it the same aspect ratio as image
        aspect_ratio = height / width
        graph_aspect_ratio = graph_height / graph_width
        
        # add whitespace to make the aspect ratios match
        if graph_aspect_ratio > aspect_ratio:
            ideal_width = graph_height / aspect_ratio
            whitespace = ideal_width - graph_width
            min_x -= whitespace / 2
            max_x += whitespace / 2
            graph_width += whitespace
        else:
            ideal_height = aspect_ratio * graph_width
            whitespace = ideal_height - graph_height
            min_y -= whitespace / 2
            max_y += whitespace / 2
            graph_height += whitespace
        graph_aspect_ratio = aspect_ratio
        
        # zoom out by 10% (add 5% padding on each side)
        width_padding = graph_width * 0.05
        min_x -= width_padding
        max_x += width_padding
        graph_width += width_padding * 2
        height_padding = graph_height * 0.05
        min_y -= height_padding
        max_y += height_padding
        graph_height += height_padding * 2
        
        # function to translate graph coords -> image coords
        def pixel(graph_x, graph_y):
            x_pct = (graph_x - min_x) / graph_width
            y_pct = (graph_y - min_y) / graph_height
            
            x, y = x_pct * width, y_pct * height
            
            # invert y, since the top of an image is at y=0
            y = height - y
            
            return round(x), round(y)
        
        # draw obstacles as black rectangles
        for o in self.obstacles:
            cv2.rectangle(img, pixel(o.x1, o.y1), pixel(o.x2, o.y2), (0, 0, 0), -1)
        
        # draw path as red line
        if path:
            for a, b in zip(path.nodes, path.nodes[1:]):
                cv2.line(img, pixel(a.x, a.y), pixel(b.x, b.y), (0, 0, 255), 1, cv2.LINE_AA)
        
        # display
        cv2.imshow(title, img)
        key_result = cv2.waitKey(milliseconds)
        cv2.destroyWindow(title)
        
        return key_result, img

    def find(self, node_from, node_to):
        return self.pathfinder.find(self, node_from, node_to)