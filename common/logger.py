from enum import Enum
from sys import _getframe
from types import TracebackType
from typing import Callable, Any, DefaultDict, Protocol
from collections import defaultdict
from time import time
from rich.console import Console, ConsoleOptions
from rich.markup import escape
from rich.traceback import install, Trace, Traceback

install(show_locals=False)

from .lib import R
from .pretty import arglist_str


class Log:

    class Logger(Protocol):
        def __call__(
            self,
            content: str = "",
            condition: bool = True,
            tag: str | None = None,
            **kwargs: Any,
        ) -> bool: ...

    class Level(Enum):
        NONE = 0
        ERROR = 1
        WARN = 2
        DEBUG = 3
        TRACE = 4

    _level: Level = Level.ERROR
    _traceback: bool = False
    _colors: DefaultDict[Level, str] = defaultdict(lambda: "white")
    _console: Console = Console()
    _levels: dict[str, Level] = {
        "n": Level.NONE,
        "none": Level.NONE,
        "e": Level.ERROR,
        "error": Level.ERROR,
        "w": Level.WARN,
        "warn": Level.WARN,
        "d": Level.DEBUG,
        "debug": Level.DEBUG,
        "t": Level.TRACE,
        "trace": Level.TRACE,
    }

    t: Logger
    tf: Logger
    d: Logger
    df: Logger
    w: Logger
    wf: Logger
    e: Logger
    ef: Logger

    @classmethod
    def at(cls, level: str | Level) -> None:
        if type(level) is str:
            if level.lower() not in cls._levels:
                raise ValueError(f"invalid log level: '{level}'")
            cls._level = cls._levels[level.lower()]
        elif type(level) is Log.Level:
            cls._level = level
        else:  # pragma: no cover
            assert False

    @classmethod
    def log(
        cls,
        level: Level,
        content: Any,
        tag: str | None = None,
        formatted: bool = False,
        **kwargs: Any,
    ) -> bool:
        # todo: temporary
        if tag == "Parser":
            return True

        if cls._level.value < level.value:
            return False

        for line in str(content).split("\n"):
            if not formatted:
                line = escape(line)

            if tag:
                cls._console.print(
                    f"[{cls._colors[level]}][{level.name}][/{cls._colors[level]}] <{tag}> {line}",
                    **kwargs,
                )
            else:
                cls._console.print(
                    f"[{cls._colors[level]}][{level.name}][/{cls._colors[level]}] {line}",
                    **kwargs,
                )

        return True

    @staticmethod
    def define(
        level: Level,
        color: str = "white",
    ) -> tuple[Logger, Logger]:

        def log(
            content: Any = "",
            condition: bool = True,
            tag: str | None = None,
            **kwargs: Any,
        ) -> bool:
            return not condition or Log.log(level, content, tag, True, **kwargs)

        def logf(
            content: Any = "",
            condition: bool = True,
            tag: str | None = None,
            **kwargs: Any,
        ) -> bool:
            return not condition or Log.log(level, content, tag, True, **kwargs)

        Log._colors[level] = color
        return log, logf

    # weird hack from https://github.com/Textualize/rich/discussions/1531#discussioncomment-6409446
    @staticmethod
    def before_error() -> None:
        if not Log._traceback:
            return

        traceback_type: TracebackType | None = None
        # start at depth 3 to skip logger internal calls
        depth = 3
        while True:
            try:
                frame = _getframe(depth)
                depth += 1
            except ValueError:
                break
            traceback_type = TracebackType(
                traceback_type, frame, frame.f_lasti, frame.f_lineno
            )
        dummy: ValueError = ValueError()
        trace: Trace = Traceback.extract(
            type(dummy), dummy, traceback_type, show_locals=True
        )
        traceback: Traceback = Traceback(trace, show_locals=True)

        # account for width of '[ERROR] ', which is 8
        adjusted_console_options: ConsoleOptions = Log._console.options.copy().update(
            width=Log._console.options.size.width - 8
        )

        # disgusting hack to get the rendered segments
        # last two segments are the error and the final newline which are stripped away
        stack_segments = list(Log._console.render(traceback, adjusted_console_options))[
            :-2
        ]

        # prefix every line with log level
        Log._console.print("[red][ERROR][/red] ", end="")
        for idx, segment in enumerate(stack_segments):
            Log._console._buffer.append(segment)
            if segment.text == "\n" and idx != len(stack_segments) - 1:
                Log._console.print("[red][ERROR][/red] ", end="")

    @staticmethod
    def usage(f: Callable[..., Any]) -> Callable[..., Any]:

        def f_and_log_usage(*args: Any, **kwargs: Any) -> Any:
            global arglist_str

            Log.d(f"calling {f.__qualname__}({arglist_str(args, kwargs)})", tag="usage")

            ret = f(*args, **kwargs)

            Log.d(f"{f.__qualname__}({arglist_str(args, kwargs)}) returned {repr(ret)}")

            return ret

        return f_and_log_usage

    # todo: type annotation
    @staticmethod
    def runtime(
        description: str | None = None,
    ) -> Callable[[Callable[..., R]], Callable[..., R]]:

        def decorator(f: Callable[..., R]) -> Callable[..., R]:

            def f_and_log_time(*args: Any, **kwargs: Any) -> R:
                global arglist_str

                start_time: float = time() * 1000
                ret: R = f(*args, **kwargs)
                end_time: float = time() * 1000
                msg: str = f"took {(end_time - start_time):.2f} ms"

                if description:
                    msg = f"{description} {msg}"
                else:
                    msg = f"{f.__qualname__}({arglist_str(args, kwargs)}) {msg}"

                Log.d(msg, tag="runtime")

                return ret

            return f_and_log_time

        return decorator


Log.t, Log.tf = Log.define(Log.Level.TRACE)
Log.d, Log.df = Log.define(Log.Level.DEBUG, "blue")
Log.w, Log.wf = Log.define(Log.Level.WARN, "yellow")
Log.e, Log.ef = Log.define(Log.Level.ERROR, "red")
