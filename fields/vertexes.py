import numpy as np
import numpy.typing as npt
from typing import Optional, Self, List, Tuple


class VertexField:

    _instance: Optional[Self] = None

    @classmethod
    def __new__(cls, *args, **kwargs) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self._vertexes: npt.NDArray = np.array([])

    def push_vertex(self, x, y) -> int:
        if not len(self._vertexes):
            self._vertexes = np.array([[x, y]], dtype=float)
        else:
            self._vertexes = np.append(self._vertexes, [[x, y]], axis=0)
        return self._vertexes.shape[0] - 1

    def get_vertex(self, index) -> Optional[Tuple[float, float]]:
        if self._vertexes is None:
            return None
        x = self._vertexes[index][0]
        y = self._vertexes[index][1]
        return (x, y)

    @property
    def indexes(self) -> npt.NDArray:
        return np.arange(len(self._vertexes))

    def get_vertexes_by_mask(self, mask: List[int]) -> npt.NDArray:
        if self._vertexes is None:
            return np.array([])
        return self._vertexes[mask]

    def delete_vertexes(self, indexes: List[int]):
        if self._vertexes is not None:
            self._vertexes = np.delete(self._vertexes, indexes, axis=0)
