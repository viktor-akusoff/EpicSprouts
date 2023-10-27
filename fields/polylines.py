from __future__ import annotations
from collections import deque
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import numpy.typing as npt
import pygame as pg
from dataclasses import dataclass, field
from typing import List, Optional, Self, Tuple, Deque, Set

from .nodes import NodesField
from .vertexes import VertexField

CODE_INSIDE = 0
CODE_LEFT = 1
CODE_RIGHT = 2
CODE_BOTTOM = 4
CODE_TOP = 8


def projections_intersects(a: float, b: float, c: float, d: float):
    if (a > b):
        b, a = a, b

    if (c > d):
        d, c = c, d

    return np.max([a, c]) <= np.min([b, d])


def orientated_area(a: Tuple[float, float],
                    b: Tuple[float, float],
                    c: Tuple[float, float]):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def intersection(a: Tuple[float, float], b: Tuple[float, float],
                 c: Tuple[float, float], d: Tuple[float, float]):
    return (
        projections_intersects(a[0], b[0], c[0], d[0]) and
        projections_intersects(a[1], b[1], c[1], d[1]) and
        (orientated_area(a, b, c) * orientated_area(a, b, d) <= 0) and
        (orientated_area(c, d, a) * orientated_area(c, d, b) <= 0)
    )


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

    @property
    def middle_point(self):
        return self.indexes[len(self.indexes)//2]


class PolylinesField:

    _instance: Optional[Self] = None

    @classmethod
    def __new__(cls, *args, **kwargs) -> PolylinesField:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self,
                 screen: pg.Surface,
                 vertex_field: VertexField,
                 nodes_field: NodesField) -> None:
        self._polylines: List[PolyLine] = []
        self._vertex_field: VertexField = vertex_field
        self._nodes_field: NodesField = nodes_field
        self._indexes: Set[int] = set()
        self._screen = screen

    def start_polyline(self, index: int):
        polyline = PolyLine()
        polyline.indexes.append(index)
        self._polylines.append(polyline)
        self._indexes.add(index)

    def end_polyline(self, index: int):
        polyline = self._polylines[-1]
        polyline.indexes.append(index)
        self._indexes.add(index)

    def check_intersection(
        self,
        pos: Tuple[float, float],
        debug: bool = False
    ):
        if not len(self._polylines):
            return False

        last_polyline = self._polylines[-1]

        if (len(last_polyline.indexes) < 2):
            return False

        vertexes = self._vertex_field.get_vertexes_by_mask(
            last_polyline.indexes
        )

        vertex_pairs = np.squeeze(
            sliding_window_view(vertexes, window_shape=(2, 2))
        )

        list_vertex = vertexes[-1]

        v1: Tuple[float, float] = (
            float(list_vertex[0]),
            float(list_vertex[1])
        )
        v2 = pos

        if len(vertex_pairs) > 2:
            last_two = vertex_pairs[-2: -1]
            for segment in last_two:

                a: Tuple[float, float] = (
                    float(segment[0][0]),
                    float(segment[0][1])
                )

                b: Tuple[float, float] = (
                    float(segment[1][0]),
                    float(segment[1][1])
                )

                for vertex_pair in vertex_pairs[:-3]:

                    c: Tuple[float, float] = (
                        float(vertex_pair[0][0]),
                        float(vertex_pair[0][1])
                    )

                    d: Tuple[float, float] = (
                        float(vertex_pair[1][0]),
                        float(vertex_pair[1][1])
                    )

                    if intersection(a, b, c, d):
                        return True

        for p in self._polylines:

            if p.tree is None:
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

    def push_vertex(self, pos: Tuple[float, float], distance: float) -> None:
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
            self._indexes.add(index)
        return None

    def pop(self):
        last_polyline: PolyLine = self._polylines[-1]
        indexes_to_remove: List[int] = last_polyline.indexes
        self._polylines.pop()
        self._vertex_field.delete_vertexes(indexes_to_remove[1:])

    def get_polyline(self, index):
        return self._polylines[index]

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

    def rebuild_trees(self):
        for index in range(len(self._polylines)):
            self.build_tree(index)

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

    def force_update(self, power: float, ms: int):
        indexes_set: Set[int] = set(self._vertex_field.indexes)
        for p in self._polylines:
            polyline_indexes_set: Set[int] = set(p.indexes)
            indexes_set: Set[int] = set(self._vertex_field.indexes)
            nodes_indexes = self._nodes_field.get_indexes_by_degree([0])
            nodes_indexes_set = set(nodes_indexes)
            other_indexes_set = (
                indexes_set -
                polyline_indexes_set -
                nodes_indexes_set
            )
            other_indexes = list(other_indexes_set)
            nodes_vertexes = self._vertex_field._vertexes[nodes_indexes]

            v_update = self._vertex_field._vertexes
            f_vertexes = self._vertex_field.get_vertexes_by_mask(other_indexes)

            for i, index in enumerate(p.indexes):
                xs, ys = np.hsplit(f_vertexes, 2)

                dx = -xs + v_update[index][0]
                dy = -ys + v_update[index][1]

                length = np.power(np.power(dx, 2) + np.power(dy, 2), 2)

                repulsive_forcex = dx * 50 / length
                repulsive_forcey = dy * 50 / length

                repulsive_force_vectors = np.concatenate(
                    [repulsive_forcex, repulsive_forcey],
                    axis=1
                )

                xs, ys = np.hsplit(nodes_vertexes, 2)

                dx = -xs + v_update[index][0]
                dy = -ys + v_update[index][1]

                length = np.power(np.power(dx, 2) + np.power(dy, 2), 2)

                nodes_repulsive_forcex = dx * 2000 / length
                nodes_repulsive_forcey = dy * 2000 / length

                nodes_repulsive_force_vectors = np.concatenate(
                    [nodes_repulsive_forcex, nodes_repulsive_forcey],
                    axis=1
                )

                repulsive_force_vectors = np.concatenate(
                    [
                        repulsive_force_vectors,
                        nodes_repulsive_force_vectors
                    ],
                    axis=0
                )

                if i - 1 > 0:
                    prev_index = p.indexes[i - 1]
                    prev_neighbour = self._vertex_field.get_vertex(prev_index)
                    if prev_neighbour:
                        force_v = v_update[index] - prev_neighbour
                        dx = prev_neighbour[0] - v_update[index][0]
                        dy = prev_neighbour[1] - v_update[index][1]
                        length = np.sqrt(np.power(dx, 2) + np.power(dy, 2))
                        grav_force = -0.002 * force_v * abs(5-length)
                        repulsive_force_vectors = np.concatenate(
                            [
                                repulsive_force_vectors,
                                [grav_force]
                            ],
                            axis=0
                        )

                if i + 1 < len(p.indexes):
                    next_index = p.indexes[i + 1]
                    next_neighbour = self._vertex_field.get_vertex(next_index)
                    if next_neighbour:
                        force_v = v_update[index] - next_neighbour
                        dx = next_neighbour[0] - v_update[index][0]
                        dy = next_neighbour[1] - v_update[index][1]
                        length = np.sqrt(np.power(dx, 2) + np.power(dy, 2))
                        grav_force = -0.002 * force_v * abs(5-length)

                        repulsive_force_vectors = np.concatenate(
                            [
                                repulsive_force_vectors,
                                [grav_force],
                            ],
                            axis=0
                        )

                repulsive_force_vector = np.sum(
                    repulsive_force_vectors,
                    axis=0
                )

                v_update[index] += ms * power * repulsive_force_vector
