import numpy as np
import pygame as pg
from dataclasses import dataclass, field
from typing import List, Optional, Self, Tuple
from .vertexes import VertexField


@dataclass
class PolyLine:
    indexes: List[int] = field(default_factory=lambda: [])


class PolylinesField:

    _instance: Optional[Self] = None

    @classmethod
    def __new__(cls, *args, **kwargs) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, vertex_field: VertexField, screen: pg.Surface) -> None:
        self._polylines: List[PolyLine] = []
        self._vertex_field: VertexField = vertex_field
        self._screen = screen

    def start_polyline(self):
        self._polylines.append(PolyLine())

    def push_vertex(self, pos: Tuple[int, int], distance: float) -> None:
        last_polyline: PolyLine = self._polylines[-1]
        last_index = last_polyline.indexes[-1] if last_polyline.indexes else -1
        last_vertex = self._vertex_field.get_vertex(last_index)
        if (
            (last_vertex is None) or
            (
                np.sqrt(
                    np.power(last_vertex[0] - pos[0], 2) +
                    np.power(last_vertex[1] - pos[1], 2)
                ) > distance
            )
        ):
            index = self._vertex_field.push_vertex(*pos)
            last_polyline.indexes.append(index)
        return None

    def pop(self):
        self._polylines.pop()

    def draw(self):

        colors: List[Tuple[int, int, int]] = [
            (70, 200, 70),
            (30, 150, 20)
        ]

        for polyline in self._polylines:
            if len(polyline.indexes) < 2:
                continue

            previous_index: int = polyline.indexes[0]

            counter: int = 0

            for index in polyline.indexes[1:]:
                previous_vertex = self._vertex_field.get_vertex(previous_index)
                vertex = self._vertex_field.get_vertex(index)

                if (previous_vertex is not None) and (vertex is not None):
                    pg.draw.line(
                        self._screen,
                        colors[counter % 2],
                        previous_vertex,
                        vertex,
                        3
                    )
                counter += 1
                previous_index = index
