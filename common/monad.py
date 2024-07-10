from __future__ import annotations
from typing import TypeVar, Callable, Any, Generic, Iterable

from .lib import Placeholder

T = TypeVar("T")
R = TypeVar("R")
U = TypeVar("U")
V = TypeVar("V")


class Monad(Generic[T]):
    @staticmethod
    def use(key: str = "value") -> Placeholder:
        return Placeholder(key)

    # todo: type annotation
    @staticmethod
    def create(c: type) -> Callable[[Any], Any]:
        return lambda *args: c(*args)

    class F(Generic[R, U]):
        def __init__(self, f: Callable[[R], U]) -> None:
            self._f: Callable[[R], U] = f

        def then(self, g: Callable[[U], V]) -> Monad.F[R, V]:
            return Monad.F(lambda x: g(self._f(x)))

        @property
        def f(self) -> Callable[[R], U]:
            return self._f

    def __init__(self, value: T, history: list[Monad] = []):
        self._value: T = value
        self._history: list[Monad] = history

    def then(
        self,
        f: Callable[[Any], R],
    ) -> Monad[R]:
        return Monad(f(self._value), self._history + [self])

    def first(
        self,
        f: Callable[[Any], R],
    ) -> Monad[T]:
        f(self._value)
        return Monad(self._value, self._history)

    def backtrack(self, steps: int = 1) -> Monad[Any]:
        if steps > len(self._history):
            # todo: error type
            raise ValueError(
                f"cannot backtrack {steps} steps when history has length {len(self._history)}"
            )
        return Monad(self._history[-steps], self._history[:-steps])

    def also(
        self,
        f: Callable[[Any], R],
        backtrack_steps: int = 1,
    ) -> Monad[R]:
        return self.backtrack(backtrack_steps).then(f)

    @property
    def v(self) -> T:
        return self._value
