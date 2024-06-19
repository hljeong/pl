from enum import Enum
from sys import _getframe
from types import TracebackType
from typing import Callable, Any, Optional, DefaultDict, Dict
from collections import defaultdict
from time import time
from rich.console import Console, ConsoleOptions
from rich.markup import escape
from rich.traceback import install, Trace, Traceback

install(show_locals=True)

from .lib import R, Arglist, total_ordering_by

get_value: Callable[[Enum], int] = lambda level: level.value


class Log:

    @total_ordering_by(get_value)
    class Level(Enum):
        NONE = 0
        ERROR = 1
        WARN = 2
        DEBUG = 3
        TRACE = 4

    level: Level = Level.NONE
    spaced: bool = True
    trace: bool = False
    _section: bool = False
    _colors: DefaultDict[Level, str] = defaultdict(lambda: "white")
    _console: Console = Console()

    @staticmethod
    def begin_section(
        level: Level,
        before: Callable[..., None] = lambda: None,
        before_arglist: Arglist = Arglist(),
    ) -> bool:
        if Log.level < level:
            return False

        Log.w("already in section", Log._section)
        Log._section = True
        before(*before_arglist.args, **before_arglist.kwargs)
        return True

    @staticmethod
    def end_section(
        level: Level,
        after: Callable[..., None] = lambda: None,
        after_arglist: Arglist = Arglist(),
    ) -> bool:
        if Log.level < level:
            return False

        Log.w("not in section", not Log._section)
        after(*after_arglist.args, **after_arglist.kwargs)
        Log._section = False
        if Log.spaced:
            Log._console.print()
        return True

    @staticmethod
    def log(
        level: Level,
        content: Any,
        tag: Optional[str] = None,
        formatted: bool = False,
        before: Callable[..., None] = lambda: None,
        before_arglist: Arglist = Arglist(),
        after: Callable[..., None] = lambda: None,
        after_arglist: Arglist = Arglist(),
        **kwargs: Any,
    ) -> bool:
        if Log.level < level:
            return False

        if not Log._section:
            before(*before_arglist.args, **before_arglist.kwargs)

        for line in str(content).split("\n"):
            if not formatted:
                line = escape(line)

            if tag is None:
                Log._console.print(
                    f"[{Log._colors[level]}][{level.name}][/{Log._colors[level]}] {line}",
                    **kwargs,
                )
            else:
                Log._console.print(
                    f"[{Log._colors[level]}][{level.name}][/{Log._colors[level]}] <{tag}> {line}",
                    **kwargs,
                )

        if not Log._section:
            after(*after_arglist.args, **after_arglist.kwargs)

        if Log.spaced and not Log._section:
            Log._console.print(**kwargs)

        return True

    # weird hack from https://github.com/Textualize/rich/discussions/1531#discussioncomment-6409446
    @staticmethod
    def before_error() -> None:
        if not Log.trace:
            return

        traceback_type: Optional[TracebackType] = None
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
    def after_error() -> None:
        exit(1)

    # goofy reflection hack
    @staticmethod
    def define(
        name: str,
        level: Level,
        color: str = "white",
        before: Callable[..., None] = lambda: None,
        after: Callable[..., None] = lambda: None,
    ) -> None:

        def logger(
            content: Any = "",
            condition: bool = True,
            tag: Optional[str] = None,
            before_arglist: Arglist = Arglist(),
            after_arglist: Arglist = Arglist(),
            **kwargs: Any,
        ) -> bool:
            if condition:
                return Log.log(
                    level,
                    content,
                    tag,
                    False,
                    before,
                    before_arglist,
                    after,
                    after_arglist,
                    **kwargs,
                )
            return True

        def loggerf(
            content: Any = "",
            condition: bool = True,
            tag: Optional[str] = None,
            before_arglist: Arglist = Arglist(),
            after_arglist: Arglist = Arglist(),
            **kwargs: Any,
        ) -> bool:
            if condition:
                return Log.log(
                    level,
                    content,
                    tag,
                    True,
                    before,
                    before_arglist,
                    after,
                    after_arglist,
                    **kwargs,
                )
            return True

        def begin_section(before_arglist: Arglist = Arglist()) -> bool:
            return Log.begin_section(level, before, before_arglist)

        def end_section(after_arglist: Arglist = Arglist()) -> bool:
            return Log.end_section(level, after, after_arglist)

        Log._colors[level] = color
        setattr(Log, name, staticmethod(logger))
        setattr(Log, f"{name}f", staticmethod(loggerf))
        setattr(Log, f"begin_{name}", staticmethod(begin_section))
        setattr(Log, f"end_{name}", staticmethod(end_section))

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
        description: Optional[str] = None,
        n: int = 1,
    ) -> Callable[[Callable[..., R]], Callable[..., R]]:

        def decorator(f: Callable[..., R]) -> Callable[..., R]:

            def f_and_log_time(*args: Any, **kwargs: Any) -> R:
                global arglist_str

                start_time: float = time() * 1000

                for _ in range(n):
                    ret = f(*args, **kwargs)

                end_time: float = time() * 1000
                delta_time: float = end_time - start_time
                average_time: float = delta_time / n

                msg: str = f"took {average_time:.2f} ms"

                if description:
                    msg = f"{description} {msg}"

                else:
                    msg = f"{f.__qualname__}({arglist_str(args, kwargs)}) {msg}"

                if n > 1:
                    msg = f"{msg} on average over {n} runs"

                Log.d(msg, tag="runtime")

                return ret

            return f_and_log_time

        return decorator


Log.define("trace", Log.Level.TRACE)
Log.define("t", Log.Level.TRACE)

Log.define("debug", Log.Level.DEBUG, "blue")
Log.define("d", Log.Level.DEBUG, "blue")

Log.define("warn", Log.Level.WARN, "yellow")
Log.define("w", Log.Level.WARN, "yellow")

Log.define("error", Log.Level.ERROR, "red", Log.before_error, Log.after_error)
Log.define("e", Log.Level.ERROR, "red", Log.before_error, Log.after_error)


def arglist_str(args: tuple, kwargs: Dict[str, Any]) -> str:
    # args_str: str = ', '.join(map(repr, args))
    # kwargs_str: str = ', '.join(map(lambda item: f'{item[0]}={repr(item[1])}', kwargs.items()))
    args_str: str = ""
    kwargs_str: str = ""

    if len(args_str) == 0:
        return kwargs_str

    elif len(kwargs_str) == 0:
        return args_str

    else:
        return f"{args_str}, {kwargs_str}"
