from collections import deque
import numpy as np
import numpy.typing as npt
import pygame as pg
from dataclasses import dataclass, field
from typing import List, Optional, Self, Tuple, Deque
from .vertexes import VertexField


@dataclass
class TreeNode:
    vmin: Tuple[float, float] = field(default=(0, 0))
    vmax: Tuple[float, float] = field(default=(0, 0))
    right: Optional[Self] = field(default=None)
    left: Optional[Self] = field(default=None)


@dataclass
class PolyLine:
    indexes: List[int] = field(default_factory=lambda: [])
    tree: Optional[TreeNode] = field(default=None)


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
        last_polyline: PolyLine = self._polylines[-1]
        indexes_to_remove: List[int] = last_polyline.indexes
        self._polylines.pop()
        self._vertex_field.delete_vertexes(indexes_to_remove)

    def build_tree(self, index: int):
        if not self._polylines or not (-1 <= index <= len(self._polylines)):
            return

        polyline: PolyLine = self._polylines[index]
        mask: List[int] = polyline.indexes
        vertexes: npt.NDArray = self._vertex_field.get_vertexes_by_mask(mask)

        polyline.tree = TreeNode()

        job: Deque[Tuple[TreeNode, npt.NDArray]] = deque()
        job.append((polyline.tree, vertexes))

        while job:
            tree, batch = job.pop()
            xs, ys = np.hsplit(batch, 2)
            x_max = np.max(xs)
            x_min = np.min(xs)
            y_max = np.max(ys)
            y_min = np.min(ys)
            tree.vmax = (x_max, y_max)
            tree.vmin = (x_min, y_min)

            batch_len = len(batch)

            if batch_len <= 2:
                continue

            batch_left, batch_right = np.array_split(batch, 2)
            batch_left_len = len(batch_left)
            batch_right_len = len(batch_right)

            if batch_right_len < batch_left_len:
                batch_right = np.append([batch_left[-1]], batch_right, axis=0)

            if batch_left_len <= batch_right_len:
                batch_left = np.append(batch_left, [batch_right[0]], axis=0)

            tree.left, tree.right = TreeNode(), TreeNode()
            job.appendleft((tree.right, batch_right))
            job.appendleft((tree.left, batch_left))

    def draw(self, debug: bool = False):

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

            if not debug or polyline.tree is None:
                continue

            job: Deque[TreeNode] = deque()
            job.appendleft(polyline.tree)

            while job:
                tree = job.pop()
                rect = (
                    tree.vmin[0], tree.vmin[1],
                    tree.vmax[0] - tree.vmin[0],
                    tree.vmax[1] - tree.vmin[1]
                )
                pg.draw.rect(self._screen, (0, 0, 0), rect, 1)

                if tree.right:
                    job.appendleft(tree.right)

                if tree.left:
                    job.appendleft(tree.left)
