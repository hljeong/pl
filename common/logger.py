from enum import Enum
from functools import total_ordering
from typing import Type, Callable, Any, Optional, TypeVar
from time import time

from .lib import total_ordering_by

@total_ordering_by(lambda level: level.value)
class LogLevel(Enum):
  NONE = 0
  DEBUG = 1
  WARN = 2
  TRACE = 3

  # def __eq__(self, other):
  #   return isinstance(other, LogLevel) and self.value == other.value

  # def __lt__(self, other):
  #   return isinstance(other, LogLevel) and self.value < other.value



class Log:
  level = LogLevel.NONE
  spaced = True
  _section = False

  def begin_section() -> None:
    Log.w('already in section', Log._section)

    Log._section = True

  def end_section() -> None:
    Log.w('not in section', not Log._section)

    Log._section = False

    if Log.spaced:
      print()

  def log(level: LogLevel, msg: str) -> None:
    if Log.level >= level:

      for line in msg.split('\n'):
        print(f'[{level.name}] {line}')

      if Log.spaced and not Log._section:
        print()

  # goofy reflection hack
  def define(name: str, level: LogLevel) -> None:

    def logger(msg: str = '', condition: bool = True) -> None:
      if condition:
        Log.log(level, msg)

    setattr(Log, name, staticmethod(logger))

Log.define('trace', LogLevel.TRACE)
Log.define('t', LogLevel.TRACE)

Log.define('warn', LogLevel.WARN)
Log.define('w', LogLevel.WARN)

Log.define('debug', LogLevel.DEBUG)
Log.define('d', LogLevel.DEBUG)

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
