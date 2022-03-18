import cv2, numpy # visualization
from . import Pathfinder, Obstacle

class Graph:
    def __init__(self, obstacles=[], pathfinder=Pathfinder):
        self.pathfinder = pathfinder()
        self.obstacles = {o if isinstance(o, Obstacle) else Obstacle(*o) for o in obstacles}
