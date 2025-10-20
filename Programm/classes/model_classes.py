from dataclasses import dataclass


@dataclass()
class Dot:
    x: float
    y: float
    z: float


@dataclass()
class Edge:
    start_dot: Dot
    end_dot: Dot


@dataclass
class Face:
    vertices: list
    color: list[int] = None
    uv: list = None
