from __future__ import annotations
from typing import TypeVar, Callable, Any, Generic, Union, cast, Iterable

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

    def __init__(self, value: T, history: list[Monad] = [], kept: dict[str, Any] = {}):
        self._history: list[Monad] = history
        self._kept: dict[str, Any] = kept
        self._kept["value"] = value

    # todo: monadify this
    def _dispatch(self, arg: Any) -> Any:
        if type(arg) is Placeholder:
            if type(arg.key) is str:
                if arg.key not in self._kept:
                    raise ValueError(f"invalid kept key: '{arg.key}'")

                return self._kept[arg.key]

            else:
                return self._history[cast(int, arg.key)].value

        return arg

    def then(
        self,
        f: Union[Callable[[Any], R], Placeholder],
        args: tuple[Any, ...] = (Placeholder(),),
    ) -> Monad[R]:
        f_: Callable[[T], R] = cast(Callable[[T], R], self._dispatch(f))
        args_: Iterable[Any] = (self._dispatch(arg) for arg in args)

        return self._next(
            history=self._history + [self],
            kept=dict(self._kept, value=f_(*args_)),
        )

    def then_and_keep(
        self,
        f: Union[Callable[[Any], tuple[R, Any]], Placeholder],
        returns: Union[str, Iterable[str]],
        args: tuple[Any, ...] = (Placeholder(),),
    ) -> Monad[R]:
        f_: Callable[[Any], tuple[R, Any]] = cast(
            Callable[[Any], tuple[R, Any]], self._dispatch(f)
        )
        args_ = (self._dispatch(arg) for arg in args)

        to_keep: dict[str, Any] = {}
        if type(returns) is str:
            to_keep["value"], to_keep[cast(str, returns)] = f_(*args_)

        else:
            # todo: validate len(returns)
            to_keep = {k: v for (k, v) in zip(cast(list[str], returns), f_(*args_))}

        return self._next(
            history=self._history + [self],
            kept=dict(self._kept, **to_keep),
        )

    def keep(
        self,
        f: Union[Callable[[Any], R], Placeholder],
        returns: Union[str, Iterable[str]],
        args: tuple[Any, ...] = (Placeholder(),),
    ) -> Monad[T]:
        f_: Callable[[T], R] = cast(Callable[[T], R], self._dispatch(f))
        args_ = (self._dispatch(arg) for arg in args)

        to_keep: dict[str, Any] = {}
        if type(returns) is str:
            to_keep[cast(str, returns)] = f_(*args_)

        else:
            # todo: validate len(returns)
            to_keep = {
                k: v
                for (k, v) in zip(cast(list[str], returns), cast(Iterable, f_(*args_)))
            }

        return self._next(kept=dict(self._kept, **to_keep))

    def first(
        self,
        f: Union[Callable[[Any], R], Placeholder],
        args: tuple[Any, ...] = (Placeholder(),),
    ) -> Monad[T]:
        f_: Callable[[T], R] = cast(Callable[[T], R], self._dispatch(f))
        args_: Iterable[Any] = (self._dispatch(arg) for arg in args)

        f_(*args_)

        return self._next(
            history=self._history,
            kept=dict(self._kept),
        )

    def also(
        self,
        f: Union[Callable[[Any], R], Placeholder],
        args: tuple[Any, ...] = (Placeholder(),),
    ) -> Monad[T]:
        if not self._history:
            # todo: error type
            raise ValueError("cannot 'also' when no functions have been applied")

        # todo: decrement all other int placeholders and edge case on 0?
        args = tuple(
            (
                Placeholder(-1)
                if type(arg) is Placeholder and arg.key == "value"
                else arg
            )
            for arg in args
        )
        f_: Callable[[T], Any] = cast(Callable[[T], Any], self._dispatch(f))
        args_ = (self._dispatch(arg) for arg in args)

        return self._next(kept=dict(self._kept, value=f_(*args_)))

    def _next(
        self,
        history: Union[list[Any], Placeholder] = Placeholder(),
        kept: Union[dict[str, Any], Placeholder] = Placeholder(),
    ) -> Monad[Any]:
        history_: list[Any] = cast(
            list[Any],
            self._history[:] if type(history) is Placeholder else history,
        )

        kept_: dict[str, Any] = cast(
            dict[str, Any],
            dict(self._kept) if type(kept) is Placeholder else kept,
        )

        return Monad(kept_["value"], history_, kept_)

    @property
    def value(self) -> T:
        return self._kept["value"]
