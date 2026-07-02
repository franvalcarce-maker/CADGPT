# geometry_engine.py
from typing import Tuple
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"
class Line:
    def length(self) -> float:
        return ((self.end.x - self.start.x)**2 + (self.end.y - self.start.y)**2)**0.5

    def __init__(self, start: Point, end: Point):
        self.start = start
        self.end = end
    def __repr__(self) -> str:
        return f"Line(start={self.start}, end={self.end})"
class Plane:
    def __init__(self, point: Point, normal: Tuple[float, float, float]):
        self.point = point
        self.normal = normal
    def __repr__(self) -> str:
        return f"Plane(point={self.point}, normal={self.normal})"