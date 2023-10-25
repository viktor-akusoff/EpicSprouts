from dataclasses import dataclass
import pygame as pg
import numpy as np
from typing import Any, Optional, Self, List, Tuple
from .vertexes import VertexField

DOTS_RADIUS = 8

pg.font.init()
node_font = pg.font.SysFont('arial', 10)


@dataclass
class Node:
    index: int
    degree: int


class NodesField:

    _instance: Optional[Self] = None

    @classmethod
    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, vertex_field: VertexField, screen: pg.Surface):
        self._vertex_field: VertexField = vertex_field
        self._nodes: List[Node] = []
        self._screen = screen

    def push_node(self, x: float, y: float, degree: int = 0) -> None:
        index: int = self._vertex_field.push_vertex(x, y)
        degree_to_set = degree
        if degree_to_set < 0:
            degree_to_set = 0
        elif degree_to_set > 3:
            degree_to_set = 3
        self._nodes.append(Node(index, degree_to_set))

    def push_node_by_index(self, index: int) -> None:
        self._nodes.append(Node(index, 2))

    def rise_degree(self, index):
        if 0 <= index < len(self._nodes) and (self._nodes[index].degree < 3):
            self._nodes[index].degree += 1

    def lower_degree(self, index):
        if 0 <= index < len(self._nodes) and (self._nodes[index].degree > 0):
            self._nodes[index].degree -= 1

    def get_degree(self, index) -> int:
        if 0 <= index < len(self._nodes):
            return self._nodes[index].degree
        return 0

    def get_index(self, index) -> int:
        if 0 <= index < len(self._nodes):
            return self._nodes[index].index
        return 0

    def generate_field(self, number_of_nodes: int = 10, radius: int = 50):
        w, h = self._screen.get_size()
        dots: List[Tuple[float, float]] = []
        for _ in range(number_of_nodes):
            while True:
                too_close: bool = False
                x: float = np.random.randint(radius, w - radius)
                y: float = np.random.randint(radius, h - radius)
                for dot in dots:
                    if np.sqrt(
                        np.power(dot[0] - x, 2) + np.power(dot[1] - y, 2)
                    ) < radius:
                        too_close = True
                        break
                if too_close:
                    continue
                dots.append((x, y))
                break
            self.push_node(x, y)

    @property
    def vertexes_indexes(self) -> List[int]:
        return [node.index for node in self._nodes]

    def over_node(self, pos: Tuple[float, float]) -> int:
        indexes = self.vertexes_indexes
        vertexes = self._vertex_field.get_vertexes_by_mask(indexes)
        ord_indexes = np.arange(len(indexes))
        nd_indexes = np.reshape(np.array(ord_indexes), (vertexes.shape[0], 1))
        vxs = vertexes[:, :1]
        vys = vertexes[:, 1:]
        distances = np.sqrt(
            np.power(vxs - pos[0], 2) +
            np.power(vys - pos[1], 2)
        )
        distances_and_indexes = np.concatenate((distances, nd_indexes), axis=1)
        result = distances_and_indexes[
            distances_and_indexes[:, 0] < DOTS_RADIUS
        ]
        if not result.size:
            return -1
        return int(result[0][1])

    def draw(self, select: int):
        for index, node in enumerate(self._nodes):
            coordinates = self._vertex_field.get_vertex(node.index)
            if coordinates is None:
                continue
            text_surface = node_font.render(str(index), False, (255, 255, 255))
            place = text_surface.get_rect(center=coordinates)
            node_color = (0, 0, 0)
            if node.degree == 3:
                node_color = (100, 100, 100)
            elif index == select:
                node_color = (255, 0, 0)
            pg.draw.circle(self._screen, node_color, coordinates, DOTS_RADIUS)
            self._screen.blit(text_surface, place)
