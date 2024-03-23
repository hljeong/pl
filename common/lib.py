from typing import Protocol, TypeVar, Type, Callable, Any
from functools import total_ordering

T = TypeVar('T')

def Comparable(Protocol):
  def __eq__(self, other: 'Comparable') -> bool:
    ...

  def __ne__(self, other: 'Comparable') -> bool:
    ...

  def __lt__(self, other: 'Comparable') -> bool:
    ...

  def __le__(self, other: 'Comparable') -> bool:
    ...

  def __gt__(self, other: 'Comparable') -> bool:
    ...

  def __ge__(self, other: 'Comparable') -> bool:
    ...

def total_ordering_by(key: Callable[[T], Comparable]):

  # cls should the type T...
  def decorator(cls):
    # todo: messy type annotations
    def eq_by_key(self, other: Any) -> bool:
      return isinstance(other, type(self)) and key(self) == key(other)

    # todo: messy type annotations
    def lt_by_key(self, other: Any) -> bool:
      return isinstance(other, type(self)) and key(self) < key(other)

    setattr(cls, '__eq__', eq_by_key)
    setattr(cls, '__lt__', lt_by_key)

    return total_ordering(cls)

  return decorator
