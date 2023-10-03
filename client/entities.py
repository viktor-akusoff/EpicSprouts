import itertools
from dataclasses import dataclass, field


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
