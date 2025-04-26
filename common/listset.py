from __future__ import annotations
from typing import TypeVar, Iterable

T = TypeVar("T")


class ListSet(list[T]):
    def add(self, e: T) -> None:
        if e not in self:
            self.append(e)

    def __sub__(self, s: object) -> ListSet:
        # todo: check type of elements of s
        if not (hasattr(s, "__iter__") and hasattr(s, "__contains__")):
            return NotImplemented
        return ListSet(list(e for e in self if e not in s))  # type: ignore

    def __isub__(self, s: object) -> ListSet:
        return self - s

    def __and__(self, s: object) -> ListSet:
        # todo: check type of elements of s
        if not (hasattr(s, "__iter__") and hasattr(s, "__contains__")):
            return NotImplemented
        return ListSet(list(e for e in self if e in s))  # type: ignore

    def __iand__(self, s: object) -> ListSet:
        return self & s

    def __or__(self, s: object) -> ListSet:
        # todo: check type of elements of s
        if not hasattr(s, "__iter__"):
            return NotImplemented
        return ListSet(list(e for e in self) + list(e for e in s if e not in self))  # type: ignore

    def __ior__(self, s: object) -> ListSet:
        return self | s

    def __add__(self, s: object) -> ListSet:
        return self | s

    def __iadd__(self, s: object) -> ListSet:
        return self + s

    def __mul__(self, s: object) -> ListSet:
        return self & s

    def __imul__(self, s: object) -> ListSet:
        return self * s

    def __xor__(self, s: object) -> ListSet:
        return (self + s) - (self * s)

    def __ixor__(self, s: object) -> ListSet:
        return self ^ s

    def __eq__(self, s: object) -> bool:
        return type(s) is ListSet and len(self ^ s) == 0
