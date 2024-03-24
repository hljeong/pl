from enum import Enum
from functools import total_ordering
from typing import Type, Callable, Any, Optional, TypeVar
from time import time

from .lib import total_ordering_by

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
      print()

  def log(level: LogLevel, content: Any) -> None:
    if Log.level < level:
      return

    for line in str(content).split('\n'):
      print(f'[{level.name}] {line}')

    if Log.spaced and not Log._section:
      print()

  # goofy reflection hack
  def define(name: str, level: LogLevel) -> None:

    def logger(content: Any = '', condition: bool = True) -> None:
      if condition:
        Log.log(level, content)

    def begin_section() -> None:
      Log.begin_section(level)

    def end_section() -> None:
      Log.end_section(level)

    setattr(Log, name, staticmethod(logger))
    setattr(Log, f'begin_{name}', staticmethod(begin_section))
    setattr(Log, f'end_{name}', staticmethod(end_section))

Log.define('trace', LogLevel.TRACE)
Log.define('t', LogLevel.TRACE)

Log.define('debug', LogLevel.DEBUG)
Log.define('d', LogLevel.DEBUG)

Log.define('warn', LogLevel.WARN)
Log.define('w', LogLevel.WARN)

Log.define('error', LogLevel.ERROR)
Log.define('e', LogLevel.ERROR)



def log_use(f: Callable[..., Any]) -> Callable[..., Any]:

  def f_and_log_usage(*args: Any, **kwargs: Any) -> Any:
    args_str = ', '.join(map(repr, args))
    kwargs_str = ', '.join(map(lambda item: f'{item[0]}={repr(item[1])}', kwargs.items()))

    if len(args_str) == 0:
      arglist_str = kwargs_str
    elif len(kwargs_str) == 0:
      arglist_str = args_str
    else:
      arglist_str = f'{args_str}, {kwargs_str}'

    Log.d(f'calling {f.__qualname__}({arglist_str})')

    ret = f(*args, **kwargs)

    Log.d(f'{f.__qualname__}({arglist_str}) returned {repr(ret)}')

    return ret

  return f_and_log_usage



# todo: type annotation
def log_time(f: Callable[..., Any]) -> Callable[..., Any]:

  def f_and_log_time(*args: Any, **kwargs: Any) -> Any: 
    args_str = ', '.join(map(repr, args))
    kwargs_str = ', '.join(map(lambda item: f'{item[0]}={repr(item[1])}', kwargs.items()))

    if len(args_str) == 0:
      arglist_str = kwargs_str
    elif len(kwargs_str) == 0:
      arglist_str = args_str
    else:
      arglist_str = f'{args_str}, {kwargs_str}'

    start_time = round(time() * 1000)

    ret = f(*args, **kwargs)

    end_time = round(time() * 1000)
    delta_time = end_time - start_time

    Log.d(f'{f.__qualname__}({arglist_str}) took {delta_time} ms')

    return ret

  return f_and_log_time

R = TypeVar('R')

def log_timed(
  f: Callable[[], R],
  description: Optional[str] = None,
  n: int = 1,
) -> R:
  start_time = round(time() * 1000)

  for _ in range(n):
    ret = f()

  end_time = round(time() * 1000)
  delta_time = end_time - start_time
  average_time = round(delta_time // n)
  
  msg = f'took {average_time} ms'

  if description is not None:
    msg = f'{description} {msg}'

  if n > 1:
    msg = f'{msg} on average over {n} runs'

  Log.d(msg)

  return ret
