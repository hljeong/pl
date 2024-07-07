from __future__ import annotations
from copy import copy
from functools import total_ordering

from .logger import Log


@total_ordering
class Cursor:
    def __init__(
        self,
        line: int = 1,
        column: int = 1,
    ):
        if not Log.e(
            f"cursor error: line number ({line}) has to be at least 1", line <= 0
        ):
            raise ValueError(f"line number ({line}) has to be at least 1")

        if not Log.e(
            f"cursor error: column number ({column}) has to be at least 1", column <= 0
        ):
            raise ValueError(f"column number ({column}) has to be at least 1")

        self._line = line
        self._column = column

    def __str__(self) -> str:
        return f"line {self._line} column {self._column}"

    def __copy__(self) -> Cursor:
        return Cursor(self._line, self._column)

    def __lt__(self, other: Cursor) -> bool:
        return (
            self._line < other._line
            or self._line == other._line
            and self._column < other._column
        )

    def __ne__(self, other: Cursor) -> bool:
        return self < other or other < self

    @property
    def line(self) -> int:
        return self._line

    @property
    def column(self) -> int:
        return self._column

    @property
    def right(self) -> Cursor:
        return Cursor(self._line, self._column + 1)

    @property
    def next_line(self) -> Cursor:
        return Cursor(self._line + 1, 1)


class CursorRange:
    def __init__(self, start: Cursor, end: Cursor):
        # todo
        # if end < start:
        #     raise ValueError(
        #         f"end ({str(end)}) cannot come before start ({str(start)})"
        #     )

        self._start = copy(start)
        self._end = copy(end)

    def __str__(self) -> str:
        if self._start.line == self._end.line:
            if self._start.column == self._end.column:
                return str(self._start)
            else:
                return f"{str(self._start)}-{self._end.column}".replace(
                    "column", "columns"
                )
        else:
            return f"{str(self._start)} - {str(self._end)}"

    def __copy__(self) -> CursorRange:
        return CursorRange(copy(self._start), copy(self._end))

    def __eq__(self, other: CursorRange) -> bool:
        return self._start == other._start and self._end == other._end

    def __ne__(self, other: CursorRange) -> bool:
        return not self == other

    @property
    def start(self) -> Cursor:
        return self._start

    @property
    def end(self) -> Cursor:
        return self._end
