from __future__ import annotations
import copy
import itertools
import numpy as np
import pygame as pg
from typing import Tuple, List, OrderedDict
from typing_extensions import Self
from collections import OrderedDict as od
from queue import Queue
import warnings
warnings.filterwarnings("error")

Color = Tuple[int, int, int]
Rect = Tuple[float, float, float, float]

DOTS_RADIUS = 8

CODE_INSIDE = 0
CODE_LEFT = 1
CODE_RIGHT = 2
CODE_BOTTOM = 4
CODE_TOP = 8


pg.font.init()
node_font = pg.font.SysFont('arial', 10)


class Entity:
    instances: List[Self] = []
    id_itter = itertools.count()

    @classmethod
    def get_by_id(cls, id: int):
        return cls.instances[id]


class Vector(Entity):

    instances: List[Self] = []
    id_itter = itertools.count()

    def __init__(self, x: float, y: float, reg: bool = False):
        self.x: float = x
        self.y: float = y
        self.next: Vector | None = None
        self.prev: Vector | None = None

        if not reg:
            return

        self.reg()

    def diff(self, v: Vector):
        a = Vector(self.x, self.y)
        b = Vector(0, 0)
        if (self.next is not None) and (self.prev is not None):
            next_distance = Vector.distance(v, self.next)
            prev_distance = Vector.distance(v, self.prev)
            if next_distance > prev_distance:
                b = self.prev
            else:
                b = self.next
        elif self.next is not None:
            b = self.next
        elif self.prev is not None:
            b = self.prev
        return a - b

    def is_zero(self, prec) -> bool:
        dist = np.linalg.norm(self.pair)
        return dist < prec

    def reg(self):
        self.id = next(Vector.id_itter)
        Vector.instances.append(self)

    def __eq__(self, __value: Vector) -> bool:
        return (self.x == __value.x) and (self.y == __value.y)

    def __ne__(self, __value: Vector) -> bool:
        return (self.x != __value.x) or (self.y != __value.y)

    def __add__(self, __value: Vector) -> Vector:
        return Vector(self.x + __value.x, self.y + __value.y)

    def __sub__(self, __value: Vector) -> Vector:
        return Vector(self.x - __value.x, self.y - __value.y)

    def __mul__(self, __value) -> Vector:
        return Vector(self.x * __value, self.y * __value)

    def __iadd__(self, __value: Vector) -> Vector:
        self.x += __value.x
        self.y += __value.y
        return self.__add__(__value)

    def __isub__(self, __value: Vector) -> Vector:
        self.x -= __value.x
        self.y -= __value.y
        return self.__sub__(__value)

    def __repr__(self) -> str:
        return f"({np.round(self.x, 3)}, {np.round(self.y, 3)})"

    @property
    def pair(self):
        return (self.x, self.y)

    @staticmethod
    def cohen_sutherland_code(vmin: Vector, vmax: Vector, v: Vector) -> int:
        result_code: int = CODE_INSIDE

        if v.x < vmin.x:
            result_code |= CODE_LEFT
        elif v.x > vmax.x:
            result_code |= CODE_RIGHT

        if v.y < vmin.y:
            result_code |= CODE_BOTTOM
        elif v.y > vmax.y:
            result_code |= CODE_TOP

        return result_code

    @staticmethod
    def distance(v1: Vector, v2: Vector) -> float:
        result: float = np.sqrt(
            np.power(v2.x - v1.x, 2) +
            np.power(v2.y - v1.y, 2)
        )
        return result

    @staticmethod
    def sin_angle(v1: Vector, v2: Vector) -> float:
        v1_u = np.array(v1.pair) / np.linalg.norm(v1.pair)
        v2_u = np.array(v2.pair) / np.linalg.norm(v2.pair)

        return np.sin(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)))


class Node(Entity):

    instances: List[Node] = []
    id_itter = itertools.count()

    def __init__(self, v: Vector):
        self.vector = v
        self.degree = 0
        self.id = next(Node.id_itter)
        self.instances.append(self)
        super().__init__()

    def draw(self, screen, color: Color = (0, 0, 0)) -> None:
        text_surface = node_font.render(str(self.id), False, (255, 255, 255))
        place = text_surface.get_rect(center=self.vector.pair)
        pg.draw.circle(screen, color, self.vector.pair, DOTS_RADIUS)
        screen.blit(text_surface, place)

    def force_upon(self, v: Vector) -> Vector:
        dx = v.x - self.vector.x
        dy = v.y - self.vector.y

        Kn = 600

        result: Vector = Vector(
            Kn * dx / (dx ** 2 + dy ** 2) ** 2,
            Kn * dy / (dx ** 2 + dy ** 2) ** 2,
        )

        return result

    @classmethod
    def generate_field(
        cls,
        screen,
        number_of_dots: int = 10,
        radius: int = 50
    ) -> None:
        w: int
        h: int
        w, h = screen.get_size()
        dots: List[Vector] = []
        for _ in range(number_of_dots):
            while True:
                too_close: bool = False
                x: float = np.random.randint(radius, w - radius)
                y: float = np.random.randint(radius, h - radius)
                for dot in dots:
                    if Vector.distance(dot, Vector(x, y)) < radius:
                        too_close = True
                        break
                if too_close:
                    continue
                dots.append(Vector(x, y))
                break
            Node(Vector(x, y, True))

    def over_node(self, v: Vector) -> bool:
        if Vector.distance(self.vector, v) < DOTS_RADIUS:
            return True
        return False

    @classmethod
    def rise_degree(cls, id: int, rise: int = 1):
        if id < 0:
            return
        node: Node = cls.instances[id]
        if node.degree + rise <= 3:
            node.degree += rise

    @classmethod
    def lower_degree(cls, id: int):
        if id < 0:
            return
        node: Node = cls.instances[id]
        if node.degree > 0:
            node.degree -= 1

    @classmethod
    def is_free(cls, id: int) -> bool:
        if id < 0:
            return False
        node: Node = cls.instances[id]
        return node.degree < 3

    @classmethod
    def over_nodes(cls, x: float, y: float) -> int:
        for dot in cls.instances:
            if dot.over_node(Vector(x, y)):
                return dot.id
        return -1

    @classmethod
    def draw_all(cls, screen, over_id: int) -> None:
        for node in cls.instances:
            node_color: Color = (0, 0, 0)
            if node.degree == 3:
                node_color = (100, 100, 100)
            elif node.id == over_id:
                node_color = (255, 0, 0)
            node.draw(screen, node_color)


class RectCheck:

    def __init__(self) -> None:
        self.empty: bool = True
        self.v1: Vector = Vector(0, 0)
        self.v2: Vector = Vector(0, 0)

    @property
    def correct(self) -> bool:
        return not self.empty and not (self.v1 == self.v2)

    def draw(self, screen) -> None:
        rect: Rect = (
            self.v1.x, self.v1.y,
            self.v2.x - self.v1.x,
            self.v2.y - self.v1.y
        )
        pg.draw.rect(screen, (0, 0, 0), rect, 1)

    def push_vertex(self, v: Vector) -> None:
        if self.empty:
            self.empty = False
            self.v1 = copy.deepcopy(v)
            self.v2 = copy.deepcopy(v)
            return

        if self.v1.x > v.x:
            self.v1.x = v.x

        if self.v1.y > v.y:
            self.v1.y = v.y

        if self.v2.x < v.x:
            self.v2.x = v.x

        if self.v2.y < v.y:
            self.v2.y = v.y

    def check_cross(self, v1: Vector, v2: Vector) -> bool:
        code_point1: int = Vector.cohen_sutherland_code(self.v1, self.v2, v1)

        code_point2: int = Vector.cohen_sutherland_code(self.v1, self.v2, v2)

        final_code: int = code_point1 & code_point2

        return not final_code


class RectTreeNode:

    def __init__(self, left=None, right=None):
        self.rectangle = RectCheck()
        self.left: RectTreeNode | None = left
        self.right: RectTreeNode | None = right
        self.update()

    def update(self, total: bool = False):

        if total:
            self.rectangle = RectCheck()

        if not self.left or not self.right:
            return

        first_point = Vector(
            min(
                self.left.rectangle.v1.x,
                self.right.rectangle.v1.x
            ),
            min(
                self.left.rectangle.v1.y,
                self.right.rectangle.v1.y
            )
        )

        second_point = Vector(
            max(
                self.left.rectangle.v2.x,
                self.right.rectangle.v2.x
            ),
            max(
                self.left.rectangle.v2.y,
                self.right.rectangle.v2.y
            ),
        )

        self.rectangle.push_vertex(first_point)
        self.rectangle.push_vertex(second_point)

    def push_vertex(self, v: Vector) -> None:
        self.rectangle.push_vertex(v)


class RectSpace:
    tree: OrderedDict[int, List[RectTreeNode]]
    old_vector: Vector

    def __init__(self):
        self.tree = od()
        self.tree[1] = [RectTreeNode(),]
        super().__init__()

    def update(self, *vertexes: Vector):

        key = 0
        self.tree[1][key].rectangle = RectCheck()
        self.tree[1][key].push_vertex(vertexes[0])

        for vertex in vertexes[1:]:
            self.tree[1][key].push_vertex(vertex)
            key += 1
            if key == len(vertexes) - 1:
                break
            self.tree[1][key].rectangle = RectCheck()
            self.tree[1][key].push_vertex(vertex)

        tree_key = 2
        tree_keys = list(self.tree.keys())

        while tree_key in tree_keys:
            for rect_tree_node in self.tree[tree_key]:
                rect_tree_node.update(total=True)
            tree_key *= 2

    def push_vertex(self, v: Vector) -> None:
        if self.tree[1][-1].rectangle.correct:
            self.tree[1].append(RectTreeNode())
            self.tree[1][-1].push_vertex(self.old_vector)
        self.tree[1][-1].push_vertex(v)
        self.old_vector = copy.deepcopy(v)

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

    def check_cross(self, v1: Vector, v2: Vector) -> bool:
        nodes: Queue[RectTreeNode] = Queue()
        nodes.put(self.tree[list(self.tree.keys())[-1]][0])

        while nodes.qsize() != 0:
            node: RectTreeNode = nodes.get()
            if node.rectangle.check_cross(v1, v2):
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


class PolyLine(Entity):

    instances: List[PolyLine] = []
    id_itter = itertools.count()

    vertexes: List[Vector]
    rect_space: RectSpace
    split_distance: float

    def __init__(self, split_distance: int = 5) -> None:
        self.split_distance = split_distance
        self.vertexes = []
        self.rect_space = RectSpace()
        self.id = next(PolyLine.id_itter)
        self.instances.append(self)
        super().__init__()

    @property
    def middle_point(self) -> Vector:
        middle: int = len(self.vertexes) // 2
        return self.vertexes[middle]

    @classmethod
    def add_line(cls, *args: Vector) -> None:
        line: cls = cls(10)
        for arg in args:
            line.push_vertex(arg)
        line.finish()

    def push_vertex(self, v: Vector) -> None:
        last_vertex = None
        if self.vertexes:
            last_vertex = self.vertexes[-1]
            last_vertex.next = v
        self.rect_space.push_vertex(v)
        self.vertexes.append(v)
        if last_vertex:
            self.vertexes[-1].prev = last_vertex

    def finish(self) -> None:
        for vertex in self.vertexes:
            vertex.reg()
        self.rect_space.finish()

    def is_edge_end(self, x, y) -> bool:
        if not self.vertexes:
            return True
        last_v: Vector
        last_v = self.vertexes[-1]
        distance: float = np.sqrt(
            np.power(x - last_v.x, 2) +
            np.power(y - last_v.y, 2)
        )

        return distance >= self.split_distance

    @classmethod
    def total_update(cls):
        for instance in cls.instances:
            instance.rect_space.update(*instance.vertexes)

    @classmethod
    def pop(cls) -> PolyLine:
        return cls.instances.pop()

    def cross_detect(self, new_v: Vector) -> bool:
        last_v: Vector
        last_v = self.vertexes[-1]
        for polyline in PolyLine.instances[:-1]:
            if polyline.rect_space.check_cross(last_v, new_v):
                return True
        rect_tree_nodes: List[RectTreeNode] = self.rect_space.tree[1][:-1]
        for rect_tree_node in rect_tree_nodes:
            rect: RectCheck = rect_tree_node.rectangle
            if rect.check_cross(last_v, new_v):
                return True
        return False

    def draw(self, screen, debug: bool = False) -> None:
        if len(self.vertexes) < 2:
            return

        previous_vertex: Vector = self.vertexes[0]

        colors: List[Color] = [
            (70, 200, 70),
            (30, 150, 20)
        ]

        counter: int = 0

        for vertex in self.vertexes[1:]:
            pg.draw.line(
                screen,
                colors[counter % 2],
                previous_vertex.pair,
                vertex.pair,
                3
            )
            if debug:
                self.rect_space.draw(screen)
            counter += 1
            previous_vertex = vertex

    @classmethod
    def draw_all(cls, screen) -> None:
        for polyline in cls.instances:
            polyline.draw(screen)
