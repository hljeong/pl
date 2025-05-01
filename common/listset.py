from __future__ import annotations
from typing import TypeVar, Iterable

T = TypeVar("T")


class ListSet(list[T]):
    def add(self, e: T) -> None:
        if e not in self:
            self.append(e)

    def add_all(self, c: Iterable[T]) -> None:
        for e in c:
            self.add(e)

    def diff(self, c: Iterable[T]) -> ListSet[T]:
        return ListSet(filter(lambda e: e not in c, self))

    def __sub__(self, s: object) -> ListSet:
        if type(s) is not ListSet:
            return NotImplemented
        return ListSet(list(e for e in self if e not in s))

    def __and__(self, s: object) -> ListSet:
        if type(s) is not ListSet:
            return NotImplemented
        return ListSet(list(e for e in self if e in s))

    def __or__(self, s: object) -> ListSet:
        if type(s) is not ListSet:
            return NotImplemented
        return ListSet(list(e for e in self) + list(e for e in s if e not in self))

    def __add__(self, s: object) -> ListSet:
        return self | s

    def __mul__(self, s: object) -> ListSet:
        return self & s

    def __xor__(self, s: object) -> ListSet:
        return (self + s) - (self * s)

    def __eq__(self, s: object) -> bool:
        return type(s) is ListSet and len(self ^ s) == 0
