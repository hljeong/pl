from __future__ import annotations
from typing import (
    TypeVar,
    Callable,
    Any,
    Generic,
    Union,
    cast,
    Iterable,
)

from .lib import Placeholder

T = TypeVar("T")
R = TypeVar("R")
U = TypeVar("U")


class Mutable(Generic[T]):
    def __init__(self, value: T) -> None:
        self._value: T = value

    def __iadd__(self, other: T) -> Mutable[T]:
        self._value += other  # type: ignore
        return self

    # todo: add implementations as needed

    @property
    def value(self) -> T:
        return self._value
