from enum import Enum
from functools import total_ordering
from typing import Type, Callable, Any, Optional
from time import time
from rich.console import Console
from rich.markup import escape

from .lib import R, total_ordering_by

@total_ordering_by(lambda level: level.value)
class LogLevel(Enum):
  NONE = 0
  ERROR = 1
  WARN = 2
  DEBUG = 3
  TRACE = 4



class Log:
  level = LogLevel.NONE
  spaced = True
  _section = False
  _console = Console(highlight=False)

  def begin_section(level: LogLevel) -> None:
    if Log.level < level:
      return

    Log.w('already in section', Log._section)

    Log._section = True

  def end_section(level: LogLevel) -> None:
    if Log.level < level:
      return

    Log.w('not in section', not Log._section)

    Log._section = False

    if Log.spaced:
      Log._console.print()

  def log(
    level: LogLevel,
    content: Any,
    color: str = 'white',
    formatted: bool = False,
  ) -> None:
    if Log.level < level:
      return

    for line in str(content).split('\n'):
      if not formatted:
        line = escape(line)
      Log._console.print(f'[{color}][{level.name}][/{color}] {line}')

    if Log.spaced and not Log._section:
      Log._console.print()

  # goofy reflection hack
  def define(
    name: str,
    level: LogLevel,
    color: str = 'white',
  ) -> None:

    def logger(content: Any = '', condition: bool = True) -> None:
      if condition:
        Log.log(level, content, color, False)

    def loggerf(content: Any = '', condition: bool = True) -> None:
      if condition:
        Log.log(level, content, color, True)

    def begin_section() -> None:
      Log.begin_section(level)

    def end_section() -> None:
      Log.end_section(level)

    setattr(Log, name, staticmethod(logger))
    setattr(Log, f'{name}f', staticmethod(loggerf))
    setattr(Log, f'begin_{name}', staticmethod(begin_section))
    setattr(Log, f'end_{name}', staticmethod(end_section))

  def usage(f: Callable[..., Any]) -> Callable[..., Any]:

    def f_and_log_usage(*args: Any, **kwargs: Any) -> Any:
      global arglist_str

      Log.d(f'calling {f.__qualname__}({arglist_str(args, kwargs)})')

      ret = f(*args, **kwargs)

      Log.d(f'{f.__qualname__}({arglist_str(args, kwargs)}) returned {repr(ret)}')

      return ret

    return f_and_log_usage

  # todo: type annotation
  def runtime(
    description: Optional[str] = None,
    n: int = 1,
  ) -> Callable[[Callable[..., R]], Callable[..., R]]:

    def decorator(f: Callable[..., R]) -> Callable[..., R]:

      def f_and_log_time(*args: Any, **kwargs: Any) -> R: 
        global arglist_str

        start_time = time() * 1000


        for _ in range(n):
          ret = f(*args, **kwargs)

        end_time = time() * 1000
        delta_time = end_time - start_time
        average_time = delta_time / n

        msg = f'took {average_time:.2f} ms'

        if description:
          msg = f'{description} {msg}'

        else:
          msg = f'{f.__qualname__}({arglist_str(args, kwargs)}) {msg}'

        if n > 1:
          msg = f'{msg} on average over {n} runs'

        Log.d(msg)

        return ret

      return f_and_log_time

    return decorator

Log.define('trace', LogLevel.TRACE)
Log.define('t', LogLevel.TRACE)

Log.define('debug', LogLevel.DEBUG, 'blue')
Log.define('d', LogLevel.DEBUG, 'blue')

Log.define('warn', LogLevel.WARN, 'yellow')
Log.define('w', LogLevel.WARN, 'yellow')

Log.define('error', LogLevel.ERROR, 'red')
Log.define('e', LogLevel.ERROR, 'red')



def arglist_str(args: tuple[...], kwargs: dict[str, Any]) -> str:
  args_str = ', '.join(map(repr, args))
  kwargs_str = ', '.join(map(lambda item: f'{item[0]}={repr(item[1])}', kwargs.items()))

  if len(args_str) == 0:
    return kwargs_str

  elif len(kwargs_str) == 0:
    return args_str

  else:
    return f'{args_str}, {kwargs_str}'
