from __future__ import annotations
from copy import copy

class Cursor:
  def __init__(
    self,
    line: int,
    column: int,
  ):
    if line <= 0:
      raise ValueError(f'line number ({line}) has to be at least 1')
    if column <= 0:
      raise ValueError(f'column number ({column}) has to be at least 1')
    self._line = line
    self._column = column

  @property
  def line(self):
    return self._line

  @property
  def column(self):
    return self._column

  def to_string(self, verbose: bool = False) -> str:
    if verbose:
      return f'line {self._line} column {self._column}'
    else:
      return f'l{self._line}c{self._column}'

  def __lt__(self, other: Cursor) -> bool:
    return self._line < other._line or \
           self._line == other._line and \
           self._column < other._column

  def __ne__(self, other: Cursor) -> bool:
    return self < other or other < self

  def __eq__(self, other: Cursor) -> bool:
    return not self != other

  def __le__(self, other: Cursor) -> bool:
    return self < other or self == other

  def __gt__(self, other: Cursor) -> bool:
    return other < self

  def __ge__(self, other: Cursor) -> bool:
    return other <= self

class CursorRange:
  def __init__(
    self,
    start: Cursor,
    end: Cursor
  ):
    if end < start:
      raise ValueError(f'end ({end.to_string()}) cannot come before start ({start.to_string()})')

    self._start = copy(start)
    self._end = copy(end)

  def __copy__(self) -> CursorRange:
    return CursorRange(self._start, self._end)

  def __eq__(self, other: CursorRange) -> bool:
    return self._start == other._start and \
           self._end == other._end

  def __ne__(self, other: CursorRange) -> bool:
    return not self == other

  @property
  def start(self):
    return self._start

  @property
  def end(self):
    return self._end

  def to_string(self, verbose: bool = False) -> str:
    if self._start.line == self._end.line:
      if self._start.column == self._end.column:
        return self._start.to_string(verbose)
      else:
        return f'{self.start.to_string(verbose)}-{self.end.column}'.replace('column', 'columns')
    elif verbose:
      return f'{self.start.to_string(True)} - {self.end.to_string(True)}'
    else:
      return f'{self.start.to_string()}-{self.end.to_string()}'
