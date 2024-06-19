from __future__ import annotations
from typing import Protocol, TypeVar, Callable, Any, Generic
from functools import total_ordering
from time import sleep

T = TypeVar("T")
R = TypeVar("R")


class Monad(Generic[T]):
    def __init__(self, value: T):
        self._value: T = value

    def then(self, f: Callable[[T], R]) -> Monad[R]:
        return Monad(f(self._value))

    def also(self, f: Callable[[T], None]) -> Monad[T]:
        f(self._value)
        return self

    @property
    def value(self) -> T:
        return self._value


class Arglist:
    def __init__(self, *args: Any, **kwargs: Any):
        self._args: tuple = args
        self._kwargs: dict[str, Any] = kwargs

    @property
    def args(self) -> tuple:
        return self._args

    @property
    def kwargs(self) -> dict[str, Any]:
        return self._kwargs


def Comparable(Protocol):
    def __eq__(self, other: "Comparable") -> bool: ...

    def __ne__(self, other: "Comparable") -> bool: ...

    def __lt__(self, other: "Comparable") -> bool: ...

    def __le__(self, other: "Comparable") -> bool: ...

    def __gt__(self, other: "Comparable") -> bool: ...

    def __ge__(self, other: "Comparable") -> bool: ...


def total_ordering_by(key: Callable[[T], Comparable]):

    # cls should be the type T...
    def decorator(cls):
        # todo: messy type annotations
        def eq_by_key(self, other: Any) -> bool:
            return isinstance(other, type(self)) and key(self) == key(other)

        # todo: messy type annotations
        def lt_by_key(self, other: Any) -> bool:
            return isinstance(other, type(self)) and key(self) < key(other)

        setattr(cls, "__eq__", eq_by_key)
        setattr(cls, "__lt__", lt_by_key)

        return total_ordering(cls)

    return decorator


def slowdown(delay_ms: int) -> Callable[[Callable[..., R]], Callable[..., R]]:

    def decorator(f: Callable[..., R]) -> Callable[..., R]:

        def f_with_slowdown(*args: Any, **kwargs: Any) -> R:
            ret: R = f(*args, **kwargs)
            sleep(delay_ms / 1000)
            return ret

        return f_with_slowdown

    return decorator
