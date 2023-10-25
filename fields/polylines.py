from __future__ import annotations
from collections import deque
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import numpy.typing as npt
import pygame as pg
from dataclasses import dataclass, field
from typing import List, Optional, Self, Tuple, Deque
from .vertexes import VertexField

CODE_INSIDE = 0
CODE_LEFT = 1
CODE_RIGHT = 2
CODE_BOTTOM = 4
CODE_TOP = 8


def cohen_sutherland_code(
    vmin: Tuple[float, float],
    vmax: Tuple[float, float],
    v: Tuple[float, float]
) -> int:

    result_code: int = CODE_INSIDE

    if v[0] < vmin[0]:
        result_code |= CODE_LEFT
    elif v[0] > vmax[0]:
        result_code |= CODE_RIGHT

    if v[1] < vmin[1]:
        result_code |= CODE_BOTTOM
    elif v[1] > vmax[1]:
        result_code |= CODE_TOP

    return result_code


@dataclass
class TreeNode:
    vmin: Tuple[float, float] = field(default=(0, 0))
    vmax: Tuple[float, float] = field(default=(0, 0))
    right: Optional[Self] = field(default=None, repr=False)
    left: Optional[Self] = field(default=None, repr=False)

    def check_intersection(
        self: Self,
        v1: Tuple[float, float],
        v2: Tuple[float, float]
    ) -> bool:
        vmin = self.vmin
        vmax = self.vmax

        code_point1: int = cohen_sutherland_code(vmin, vmax, v1)
        code_point2: int = cohen_sutherland_code(vmin, vmax, v2)

        final_code: int = code_point1 & code_point2

        return not final_code

    def draw(self, screen, color=(0, 0, 0)):
        rect = (
            self.vmin[0], self.vmin[1],
            self.vmax[0] - self.vmin[0],
            self.vmax[1] - self.vmin[1]
        )
        pg.draw.rect(screen, color, rect, 1)

    @staticmethod
    def combine_nodes(tree_left: TreeNode, tree_right: TreeNode):
        xs = np.array(
            [
                tree_right.vmin[0],
                tree_right.vmax[0],
                tree_left.vmin[0],
                tree_left.vmax[0]
            ]
        )

        ys = np.array(
            [
                tree_right.vmin[1],
                tree_right.vmax[1],
                tree_left.vmin[1],
                tree_left.vmax[1]
            ]
        )

        x_max: float = np.max(xs)
        y_max: float = np.max(ys)
        x_min: float = np.min(xs)
        y_min: float = np.min(ys)

        vmax = (x_max, y_max)
        vmin = (x_min, y_min)

        return vmax, vmin


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

    def check_intersection(
        self,
        pos: Tuple[float, float],
        debug: bool = False
    ):
        if len(self._polylines) < 2:
            return False

        last_polyline = self._polylines[-1]

        if (len(last_polyline.indexes) < 2):
            return False

        list_vertex = self._vertex_field.get_vertex(-1)

        v1 = list_vertex if list_vertex else pos
        v2 = pos

        for p in self._polylines:

            if p.tree is None or v1 is None or v2 is None:
                continue

            tree = p.tree

            job: Deque[TreeNode] = deque()
            job.appendleft(tree)

            while job:
                tree = job.pop()

                if not tree.check_intersection(v1, v2):
                    continue
                elif debug:
                    tree.draw(self._screen, (0, 0, 255))

                if tree.right:
                    job.appendleft(tree.right)

                if tree.left:
                    job.appendleft(tree.left)

                if tree.right is None and tree.left is None:
                    return True

        return False

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
        vertex_pairs = np.squeeze(
            sliding_window_view(vertexes, window_shape=(2, 2))
        )

        job_a: Deque[TreeNode] = deque()
        job_b: Deque[TreeNode] = deque()

        for vertex_pair in vertex_pairs:
            xs, ys = np.hsplit(vertex_pair, 2)

            x_max: float = np.max(xs)
            y_max: float = np.max(ys)
            x_min: float = np.min(xs)
            y_min: float = np.min(ys)

            if np.abs(x_max - x_min) < 5:
                x_max += 2.5
                x_min -= 2.5

            if np.abs(y_max - y_min) < 5:
                y_max += 2.5
                y_min -= 2.5

            vmax = (x_max, y_max)
            vmin = (x_min, y_min)

            job_a.appendleft(TreeNode(vmin, vmax))

        while len(job_a) > 1:

            last_tree: Optional[TreeNode] = None

            while len(job_a) > 1:
                tree_right = job_a.pop()
                tree_left = job_a.pop()

                vmax, vmin = TreeNode.combine_nodes(tree_left, tree_right)

                last_tree = TreeNode(vmin, vmax, tree_right, tree_left)

                job_b.appendleft(last_tree)

            if job_a:
                job_b.appendleft(job_a.pop())

            job_a = job_b
            job_b = deque()

        polyline.tree = job_a.pop()

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

                tree.draw(self._screen)

                if tree.right:
                    job.appendleft(tree.right)

                if tree.left:
                    job.appendleft(tree.left)
