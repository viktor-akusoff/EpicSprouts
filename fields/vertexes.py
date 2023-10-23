import numpy as np
import numpy.typing as npt
from typing import Optional, Self, List, Tuple


class VectorAlg:

    @staticmethod
    def distance(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
        result: float = np.sqrt(
            np.power(v2[0] - v1[0], 2) +
            np.power(v2[1] - v1[1], 2)
        )

        return result


class VertexField:

    _instance: Optional[Self] = None

    @classmethod
    def __new__(cls, *args, **kwargs) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self._vertexes: Optional[npt.NDArray] = None

    def push_vertex(self, x, y) -> int:
        if self._vertexes is None:
            self._vertexes = np.array([[x, y]], dtype=float)
        else:
            self._vertexes = np.append(self._vertexes, [[x, y]], axis=0)
        return self._vertexes.shape[0] - 1

    def get_vertex(self, index) -> Optional[List[int]]:
        if self._vertexes is None:
            return None
        return list(self._vertexes[index])

    def get_vertexes_by_mask(self, mask: List[int]) -> npt.NDArray:
        if self._vertexes is None:
            return np.array([])
        return self._vertexes[mask]
