from typing import Callable, Any, TypeVar
from time import sleep

R = TypeVar('R')

def slowdown(delay_ms: int) -> Callable[[Callable[..., R]], Callable[..., R]]:

  def decorator(f: Callable[..., R]) -> Callable[..., R]:

    def f_with_slowdown(*args: Any, **kwargs: Any) -> R:
      ret: R = f(*args, **kwargs)
      sleep(delay_ms / 1000)
      return ret

    return f_with_slowdown

  return decorator
