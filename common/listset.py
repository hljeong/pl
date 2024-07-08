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

    def __eq__(self, s: object) -> bool:
        return type(s) is ListSet and len(self) == len(s) and all(e in s for e in self)
