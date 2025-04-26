from __future__ import annotations
from typing import Generic, TypeVar

from .util import cached_property
from .listset import ListSet

T = TypeVar("T")


class Graph(Generic[T]):
    def __init__(self) -> None:
        self._g: dict[int, ListSet[int]] = {}
        self._key_to_idx: dict[T, int] = {}
        self._idx_to_key: dict[int, T] = {}

    def arc(self, u: T, v: T) -> None:
        self._g[self[u]].add(self[v])

    def edge(self, u: T, v: T) -> None:
        self.arc(u, v)
        self.arc(v, u)

    def node(self, u: T) -> None:
        self[u]

    def _node(self) -> int:
        u: int = len(self._g)
        self._g[u] = ListSet()
        return u

    def __getitem__(self, key: T) -> int:
        if key not in self._key_to_idx:
            u: int = self._node()
            self._key_to_idx[key] = u
            self._idx_to_key[u] = key
        return self._key_to_idx[key]

    def _topological_order(self) -> list[T] | None:
        indegree: dict[int, int] = {u: 0 for u in self._g}
        for u in self._g:
            for v in self._g[u]:
                indegree[v] += 1

        # typically a queue is used here, but no need
        # (i dont want to look up python deque)
        stack: list[int] = []
        for u in self._g:
            if not indegree[u]:
                stack.append(u)

        topological_order: list[T] = []
        while stack:
            u: int = stack.pop()
            topological_order.append(self._idx_to_key[u])
            for v in self._g[u]:
                indegree[v] -= 1
                if not indegree[v]:
                    stack.append(v)

        return None if len(topological_order) < len(self._g) else topological_order

    def is_dag(self) -> bool:
        return self._topological_order() is not None

    @cached_property
    def topological_order(self) -> list[T]:
        topological_order = self._topological_order()
        if topological_order is None:
            raise ValueError("not a dag")
        return topological_order
