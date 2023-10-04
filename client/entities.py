import itertools
import numpy as np
import pygame as pg
from dataclasses import dataclass, field
from typing import Tuple, List, Dict


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
class RectCheck:
    empty: bool = field(init=False, default=True, repr=False)
    x1: int = field(init=False, default=0)
    y1: int = field(init=False, default=0)
    x2: int = field(init=False, default=0)
    y2: int = field(init=False, default=0)

    def draw(self, screen):
        rect = [self.x1, self.y1, self.x2 - self.x1, self.y2 - self.y1]
        pg.draw.rect(screen, (0, 0, 0), rect, 1)

    def push_vertex(self, x, y):
        if self.empty:
            self.empty = False
            self.x1 = x
            self.y1 = y
            self.x2 = x
            self.y2 = y
            return

        if self.x1 > x:
            self.x1 = x

        if self.y1 > y:
            self.y1 = y

        if self.x2 < x:
            self.x2 = x

        if self.y2 < y:
            self.y2 = y

    def check_cross(self, x, y):
        check_x = (x >= self.x1) and (x <= self.x2)
        check_y = (y >= self.y1) and (y <= self.y2)
        return check_x and check_y


@dataclass
class RectSpace:
    start_x: int = field(init=False, default=0)
    start_y: int = field(init=False, default=0)
    vertex_counter: int = field(init=False, default=0)
    power_counter: int = field(init=False, default=1)
    preparing_rect: RectCheck = field(init=False)
    rectangles: Dict[int, List[RectCheck]] = field(init=False)

    def __post_init__(self):
        self.rectangles = {1: [RectCheck()]}
        self.preparing_rect = RectCheck()

    def push_vertex(self, x, y):

        self.preparing_rect.push_vertex(x, y)

        for key in self.rectangles:
            self.rectangles[key][-1].push_vertex(x, y)

        if self.vertex_counter == self.power_counter:
            rect = self.rectangles[self.power_counter][-1]
            self.power_counter *= 2
            self.rectangles[self.power_counter] = [
                RectCheck()
            ]
            self.rectangles[self.power_counter][0].push_vertex(
                 rect.x1,
                 rect.y1
            )
            self.rectangles[self.power_counter][0].push_vertex(
                rect.x2,
                rect.y2
            )

        for key in self.rectangles:
            if not (self.vertex_counter % key):
                self.rectangles[key].append(RectCheck())
                self.rectangles[key][-1].push_vertex(x, y)

        self.vertex_counter += 1

    def draw(self, screen):
        for _, value in self.rectangles.items():
            for rect in value:
                rect.draw(screen)


@dataclass
class PolyLine:
    instances = []
    id_itter = itertools.count()
    vertexes: List[Tuple[int, int]] = field(init=False)
    rect_space: RectSpace = field(init=False)
    split_distance: float = field(default=5)
    id: int = field(init=False)

    def __post_init__(self):
        self.vertexes = []
        self.rect_space = RectSpace()
        self.id = next(PolyLine.id_itter)
        PolyLine.instances.append(self)

    def push_vertex(self, x: int, y: int):
        self.rect_space.push_vertex(x, y)
        self.vertexes.append((x, y))

    def is_edge_end(self, x, y) -> bool:
        last_x, last_y = self.vertexes[-1]
        distance = np.sqrt(
            np.power(x - last_x, 2) +
            np.power(y - last_y, 2)
        )

        return distance >= self.split_distance

    def draw(self, screen, debug: bool = False):
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
            if debug:
                self.rect_space.draw(screen)
            counter += 1
            previous_vertex = vertex
