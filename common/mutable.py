from __future__ import annotations
from typing import TypeVar, Generic

T = TypeVar("T")
R = TypeVar("R")
U = TypeVar("U")


class Mutable(Generic[T]):
    def __init__(self, value: T) -> None:
        self._v: T = value

    def __iadd__(self, other: T) -> Mutable[T]:
        self._v += other  # type: ignore
        return self

    # todo: add implementations as needed

    @property
    def v(self) -> T:
        return self._v
