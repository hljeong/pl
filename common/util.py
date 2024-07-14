from __future__ import annotations
from typing import TypeVar, Callable, Any, TYPE_CHECKING
from time import sleep
from dataclasses import dataclass

T = TypeVar("T")
R = TypeVar("R")

NoTyping: type
if TYPE_CHECKING:
    NoTyping = Any  # type: ignore
else:
    NoTyping = object


def it(it: T) -> T:
    return it


def fixed_point(
    seed: T, iterate: Callable[[T], T], eq: Callable[[T, T], bool] | None = None
) -> T:
    if eq is None:
        eq = lambda a, b: a == b
    cur: T = seed
    nxt = iterate(cur)
    while not eq(cur, nxt):
        cur = nxt
        nxt = iterate(cur)
    return cur


def load(filename: str) -> str:
    with open(filename) as f:
        data: str = f.read()
    return data


def unescape(s: str) -> str:
    return bytes(s, "utf-8").decode("unicode_escape")


Bit = bool


class Bits(list[Bit]):
    @classmethod
    def of(cls, bits: list[Bit]) -> Bits:
        return cls(sum(b << i for i, b in enumerate(bits)), len(bits))

    def __init__(self, value: int, bitwidth: int) -> None:
        super().__init__(list(bool((value >> i) & 1) for i in range(bitwidth)))

    def split(self, *sizes: int) -> tuple[Bits, ...]:
        at: int = len(self)
        fragments: list[Bits] = []
        for size in sizes:
            fragments.append(Bits.of(self[at - size : at]))
            at -= size
        return tuple(fragments)

    @property
    def value(self) -> int:
        return sum(b << i for i, b in enumerate(self))

    @property
    def svalue(self) -> int:
        bitwidth: int = len(self)
        nominal_value: int = self.value
        if nominal_value >= (1 << (bitwidth - 1)):
            return (1 << (bitwidth - 1)) - nominal_value

        else:
            return nominal_value


@dataclass(frozen=True)
class Placeholder:
    key: str | int = "value"


class Arglist:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._args: tuple = args
        self._kwargs: dict[str, Any] = kwargs

    @property
    def args(self) -> tuple:
        return self._args

    @property
    def kwargs(self) -> dict[str, Any]:
        return self._kwargs


def slowdown(delay_ms: int) -> Callable[[Callable[..., R]], Callable[..., R]]:

    def decorator(f: Callable[..., R]) -> Callable[..., R]:

        def f_with_slowdown(*args: Any, **kwargs: Any) -> R:
            ret: R = f(*args, **kwargs)
            sleep(delay_ms / 1000)
            return ret

        return f_with_slowdown

    return decorator
