from __future__ import annotations
import itertools
import numpy as np
import pygame as pg
from dataclasses import dataclass, field
from typing import Tuple, List, OrderedDict
from collections import OrderedDict as od
from queue import Queue

Color = Tuple[int, int, int]
Rect = Tuple[int, int, int, int]
Vertex = Tuple[int, int]

DOTS_RADIUS = 8

CODE_INSIDE = 0
CODE_LEFT = 1
CODE_RIGHT = 2
CODE_BOTTOM = 4
CODE_TOP = 8


pg.font.init()
node_font = pg.font.SysFont('arial', 10)


def cohen_sutherland_code(
    xmin: int, ymin: int,
    xmax: int, ymax: int,
    x: int, y: int
) -> int:
    result_code: int = CODE_INSIDE

    if x < xmin:
        result_code |= CODE_LEFT
    elif x > xmax:
        result_code |= CODE_RIGHT

    if y < ymin:
        result_code |= CODE_BOTTOM
    elif y > ymax:
        result_code |= CODE_TOP

    return result_code


def dots_distance(x1: int, y1: int, x2: int, y2: int) -> float:
    result: int = np.sqrt(np.power(x2 - x1, 2) + np.power(y2 - y1, 2))
    return result


@dataclass
class Node:
    instances = []
    id_itter = itertools.count()
    id: int = field(init=False)
    x: int = field(default=0)
    y: int = field(default=0)
    degree: int = field(init=False, default=0)

    def __post_init__(self):
        self.id = next(Node.id_itter)
        Node.instances.append(self)

    def draw(self, screen, color: Color = (0, 0, 0)) -> None:
        text_surface = node_font.render(str(self.id), False, (255, 255, 255))
        place = text_surface.get_rect(center=(self.x, self.y))
        pg.draw.circle(screen, color, (self.x, self.y), DOTS_RADIUS)
        screen.blit(text_surface, place)

    @staticmethod
    def generate_field(
        screen,
        number_of_dots: int = 10,
        radius: int = 50
    ) -> None:
        w: int
        h: int
        w, h = screen.get_size()
        dots: List[Vertex] = []
        for _ in range(number_of_dots):
            while True:
                too_close: bool = False
                x: int = np.random.randint(radius, w - radius)
                y: int = np.random.randint(radius, h - radius)
                for dot in dots:
                    if dots_distance(*dot, x, y) < radius:
                        too_close = True
                        break
                if too_close:
                    continue
                dots.append((x, y))
                break
            Node(x, y)

    def over_node(self, x: int, y: int) -> bool:
        if dots_distance(self.x, self.y, x, y) < DOTS_RADIUS:
            return True
        return False

    @staticmethod
    def rise_degree(id: int, rise: int = 1):
        if id < 0:
            return
        node: Node = Node.instances[id]
        if node.degree + rise <= 3:
            node.degree += rise

    @staticmethod
    def lower_degree(id: int):
        if id < 0:
            return
        node: Node = Node.instances[id]
        if node.degree > 0:
            node.degree -= 1

    @staticmethod
    def is_free(id: int) -> bool:
        if id < 0:
            return False
        node: Node = Node.instances[id]
        return node.degree < 3

    @staticmethod
    def over_nodes(x: int, y: int) -> int:
        for dot in Node.instances:
            if dot.over_node(x, y):
                return dot.id
        return -1

    @staticmethod
    def draw_all(screen, over_id: int) -> None:
        for node in Node.instances:
            node_color: Color = (0, 0, 0)
            if node.degree == 3:
                node_color = (100, 100, 100)
            elif node.id == over_id:
                node_color = (255, 0, 0)
            node.draw(screen, node_color)


@dataclass
class RectCheck:

    empty: bool = field(init=False, default=True, repr=False)

    x1: int = field(init=False, default=0)
    y1: int = field(init=False, default=0)
    x2: int = field(init=False, default=0)
    y2: int = field(init=False, default=0)

    @property
    def correct(self) -> bool:
        return (
            (not self.empty) and not
            (
                (self.x1 == self.x2) and
                (self.y1 == self.y2)
            )
        )

    def draw(self, screen) -> None:
        rect: Rect = (self.x1, self.y1, self.x2 - self.x1, self.y2 - self.y1)
        pg.draw.rect(screen, (0, 0, 0), rect, 1)

    def push_vertex(self, x: int, y: int) -> None:
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

    def check_cross(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        code_point1: int = cohen_sutherland_code(
            self.x1, self.y1,
            self.x2, self.y2,
            x1, y1
        )

        code_point2: int = cohen_sutherland_code(
            self.x1, self.y1,
            self.x2, self.y2,
            x2, y2
        )

        final_code: int = code_point1 & code_point2

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

    def push_vertex(self, x: int, y: int) -> None:
        self.rectangle.push_vertex(x, y)


@dataclass
class RectSpace:
    tree: OrderedDict[int, List[RectTreeNode]] = field(init=False)
    old_x: int = field(init=False, default=0, repr=False)
    old_y: int = field(init=False, default=0, repr=False)

    def __post_init__(self):
        self.tree = od()
        self.tree[1] = [RectTreeNode(),]

    def push_vertex(self, x: int, y: int) -> None:
        if self.tree[1][-1].rectangle.correct:
            self.tree[1].append(RectTreeNode())
            self.tree[1][-1].push_vertex(self.old_x, self.old_y)
        self.tree[1][-1].push_vertex(x, y)
        self.old_x = x
        self.old_y = y

        key: int = 1

        number_of_elements: int = len(self.tree[key])
        check_pair: bool = number_of_elements % 2 == 0

        while check_pair:
            left: RectTreeNode = self.tree[key][-2]
            right: RectTreeNode = self.tree[key][-1]

            if key * 2 not in list(self.tree.keys()):
                self.tree[key*2] = []

            self.tree[key*2].append(RectTreeNode(left, right))

            key *= 2

            number_of_elements = len(self.tree[key])
            check_pair = number_of_elements % 2 == 0

    def finish(self) -> None:
        key: int = list(self.tree.keys())[-1]
        cur_len: int = 1
        root_keys: Queue[int] = Queue()
        root_keys.put(key)

        while key >= 1:
            if len(self.tree[key]) != cur_len:
                root_keys.put(key)
            cur_len = len(self.tree[key]) * 2
            key //= 2

        while root_keys.qsize() > 1:
            root_key_first: int = root_keys.get()
            root_key_second: int = root_keys.get()
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

    def check_cross(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        nodes: Queue[RectTreeNode] = Queue()
        nodes.put(self.tree[list(self.tree.keys())[-1]][0])

        while nodes.qsize() != 0:
            node: RectTreeNode = nodes.get()
            if node.rectangle.check_cross(x1, y1, x2, y2):
                if (node.left is None) and (node.right is None):
                    return True
                if node.left:
                    nodes.put(node.left)
                if node.right:
                    nodes.put(node.right)
        return False

    def draw(self, screen) -> None:
        for key in self.tree.keys():
            for node in self.tree[key]:
                node.rectangle.draw(screen)


@dataclass
class PolyLine:
    instances = []
    id_itter = itertools.count()
    vertexes: List[Vertex] = field(init=False)
    rect_space: RectSpace = field(init=False)
    split_distance: float = field(default=5)
    id: int = field(init=False)

    def __post_init__(self):
        self.vertexes = []
        self.rect_space = RectSpace()
        self.id = next(PolyLine.id_itter)
        PolyLine.instances.append(self)

    @property
    def middle_point(self) -> Tuple[int, int]:
        middle: int = len(self.vertexes) // 2
        return self.vertexes[middle]

    @staticmethod
    def add_line(*args: Tuple[int, int]) -> None:
        line: PolyLine = PolyLine(10)
        for arg in args:
            line.push_vertex(*arg)
        line.finish()

    def push_vertex(self, x: int, y: int) -> None:
        self.rect_space.push_vertex(x, y)
        self.vertexes.append((x, y))

    def finish(self) -> None:
        self.rect_space.finish()

    def is_edge_end(self, x, y) -> bool:
        if not self.vertexes:
            return True
        last_x: int
        last_y: int
        last_x, last_y = self.vertexes[-1]
        distance: float = np.sqrt(
            np.power(x - last_x, 2) +
            np.power(y - last_y, 2)
        )

        return distance >= self.split_distance

    @staticmethod
    def pop() -> None:
        return PolyLine.instances.pop()

    def cross_detect(self, new_x: int, new_y: int) -> bool:
        last_x: int
        last_y: int
        last_x, last_y = self.vertexes[-1]
        for polyline in PolyLine.instances[:-1]:
            if polyline.rect_space.check_cross(last_x, last_y, new_x, new_y):
                return True
        rect_tree_nodes: List[RectTreeNode] = self.rect_space.tree[1][:-1]
        for rect_tree_node in rect_tree_nodes:
            rect: RectCheck = rect_tree_node.rectangle
            if rect.check_cross(last_x, last_y, new_x, new_y):
                return True
        return False

    def draw(self, screen, debug: bool = False) -> None:
        if len(self.vertexes) < 2:
            return

        previous_vertex: Vertex = self.vertexes[0]

        colors: List[Color] = [
            (70, 200, 70),
            (30, 150, 20)
        ]

        counter: int = 0

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

    @staticmethod
    def draw_all(screen) -> None:
        for polyline in PolyLine.instances:
            polyline.draw(screen)
