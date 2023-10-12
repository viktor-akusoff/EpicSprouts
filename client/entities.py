from __future__ import annotations
import itertools
import numpy as np
import pygame as pg
from dataclasses import dataclass, field
from typing import Tuple, List, OrderedDict
from collections import OrderedDict as od
from queue import Queue

CODE_INSIDE = 0
CODE_LEFT = 1
CODE_RIGHT = 2
CODE_BOTTOM = 4
CODE_TOP = 8


def cohen_sutherland_code(xmin, ymin, xmax, ymax, x, y):
    result_code = CODE_INSIDE

    if x < xmin:
        result_code |= CODE_LEFT
    elif x > xmax:
        result_code |= CODE_RIGHT

    if y < ymin:
        result_code |= CODE_BOTTOM
    elif y > ymax:
        result_code |= CODE_TOP

    return result_code


@dataclass
class Node:
    instances = []
    id_itter = itertools.count()
    id: int = field(init=False)
    x: float = field(default=0)
    y: float = field(default=0)

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

    @property
    def correct(self):
        return (
            (not self.empty) and not
            (
                (self.x1 == self.x2) and
                (self.y1 == self.y2)
            )
        )

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

    def check_cross(self, x1, y1, x2, y2):
        code_point1 = cohen_sutherland_code(
            self.x1, self.y1,
            self.x2, self.y2,
            x1, y1
        )

        code_point2 = cohen_sutherland_code(
            self.x1, self.y1,
            self.x2, self.y2,
            x2, y2
        )

        final_code = code_point1 & code_point2

        return not final_code


@dataclass
class RectTreeNode:
    rectangle: RectCheck = field(init=False)
    left: RectTreeNode | None = field(default=None, repr=False)
    right: RectTreeNode | None = field(default=None, repr=False)

    def __post_init__(self):
        self.rectangle = RectCheck()

        if not self.left or not self.right:
            return

        first_point = [
            min(
                self.left.rectangle.x1,
                self.right.rectangle.x1
            ),
            min(
                self.left.rectangle.y1,
                self.right.rectangle.y1
            ),
        ]

        second_point = [
            max(
                self.left.rectangle.x2,
                self.right.rectangle.x2
            ),
            max(
                self.left.rectangle.y2,
                self.right.rectangle.y2
            ),
        ]

        self.rectangle.push_vertex(*first_point)
        self.rectangle.push_vertex(*second_point)

    def push_vertex(self, x: int, y: int):
        self.rectangle.push_vertex(x, y)


@dataclass
class RectSpace:
    tree: OrderedDict[int, List[RectTreeNode]] = field(init=False)
    old_x: int = field(init=False, default=0, repr=False)
    old_y: int = field(init=False, default=0, repr=False)

    def __post_init__(self):
        self.tree = od()
        self.tree[1] = [RectTreeNode(),]

    def push_vertex(self, x: int, y: int):
        if self.tree[1][-1].rectangle.correct:
            self.tree[1].append(RectTreeNode())
            self.tree[1][-1].push_vertex(self.old_x, self.old_y)
        self.tree[1][-1].push_vertex(x, y)
        self.old_x = x
        self.old_y = y

        key = 1

        number_of_elements = len(self.tree[key])
        check_pair = number_of_elements % 2 == 0

        while check_pair:
            left = self.tree[key][-2]
            right = self.tree[key][-1]

            if key*2 not in list(self.tree.keys()):
                self.tree[key*2] = []

            self.tree[key*2].append(RectTreeNode(left, right))

            key *= 2

            number_of_elements = len(self.tree[key])
            check_pair = number_of_elements % 2 == 0

    def finish(self):
        key = list(self.tree.keys())[-1]
        cur_len = 1
        root_keys = Queue()
        root_keys.put(key)

        while key >= 1:
            if len(self.tree[key]) != cur_len:
                root_keys.put(key)
            cur_len = len(self.tree[key]) * 2
            key //= 2

        while root_keys.qsize() > 1:
            root_key_first = root_keys.get()
            root_key_second = root_keys.get()
            new_key = root_key_second * 2
            left = self.tree[root_key_second][-1]
            right = self.tree[root_key_first][-1]
            if new_key not in list(self.tree.keys()):
                self.tree[new_key] = []
            self.tree[new_key].append(RectTreeNode(left, right))
            root_keys.put(new_key)

        if root_keys.qsize():
            last_key = list(self.tree.keys())[-1]
            final_root_key = root_keys.get()
            self.tree[last_key*2] = []
            left = self.tree[last_key][-1]
            right = self.tree[final_root_key][-1]
            self.tree[last_key*2].append(RectTreeNode(left, right))

    def check_cross(self, x1, y1, x2, y2):
        nodes: Queue[RectTreeNode] = Queue()
        nodes.put(self.tree[list(self.tree.keys())[-1]][0])

        while nodes.qsize() != 0:
            node = nodes.get()
            if node.rectangle.check_cross(x1, y1, x2, y2):
                if (node.left is None) and (node.right is None):
                    return True
                if node.left:
                    nodes.put(node.left)
                if node.right:
                    nodes.put(node.right)
        return False

    def draw(self, screen):
        for key in self.tree.keys():
            for node in self.tree[key]:
                node.rectangle.draw(screen)


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

    @staticmethod
    def add_line(*args):
        line = PolyLine(10)
        for arg in args:
            line.push_vertex(*arg)
        line.finish()

    def push_vertex(self, x: int, y: int):
        self.rect_space.push_vertex(x, y)
        self.vertexes.append((x, y))

    def finish(self):
        self.rect_space.finish()

    def is_edge_end(self, x, y) -> bool:
        if not self.vertexes:
            return True
        last_x, last_y = self.vertexes[-1]
        distance = np.sqrt(
            np.power(x - last_x, 2) +
            np.power(y - last_y, 2)
        )

        return distance >= self.split_distance

    @staticmethod
    def pop():
        return PolyLine.instances.pop()

    def cross_detect(self, new_x, new_y):
        last_x, last_y = self.vertexes[-1]
        for polyline in PolyLine.instances[:-1]:
            if polyline.rect_space.check_cross(last_x, last_y, new_x, new_y):
                return True
        rect_tree_nodes = self.rect_space.tree[1][:-1]
        for rect_tree_node in rect_tree_nodes:
            rect = rect_tree_node.rectangle
            if rect.check_cross(last_x, last_y, new_x, new_y):
                return True
        return False

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
