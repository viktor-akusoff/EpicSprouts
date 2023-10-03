import itertools
import numpy as np
import pygame as pg
from dataclasses import dataclass, field
from typing import Tuple, List


@dataclass
class Node:
    instances = []
    id_itter = itertools.count()
    id: int = field(init=False)
    x: float
    y: float

    def __post_init__(self):
        self.id = next(Node.id_itter)
        Node.instances.append(self)

    def draw(self, screen):
        pg.draw.circle(screen, (0, 0, 0), (self.x, self.y), 5)


@dataclass
class PolyLine:
    instances = []
    id_itter = itertools.count()
    vertexes: List[Tuple[int, int]] = field(init=False)
    split_distance: float = field(default=5)
    id: int = field(init=False)

    def __post_init__(self):
        self.vertexes = []
        self.id = next(PolyLine.id_itter)
        PolyLine.instances.append(self)

    def push_vertex(self, x: int, y: int):
        self.vertexes.append((x, y))

    def is_edge_end(self, x, y) -> bool:
        last_x, last_y = self.vertexes[-1]
        distance = np.sqrt(
            np.power(x - last_x, 2) +
            np.power(y - last_y, 2)
        )

        return distance >= self.split_distance

    def draw(self, screen):
        if len(self.vertexes) < 2:
            return

        previous_vertex = self.vertexes[0]

        colors = [
            (70, 125, 70),
            (125, 70, 70)
        ]

        counter = 0

        for vertex in self.vertexes[1:]:
            pg.draw.line(
                screen,
                colors[counter % 2],
                previous_vertex,
                vertex,
                3
            )
            counter += 1
            previous_vertex = vertex
