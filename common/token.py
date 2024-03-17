from __future__ import annotations
from enum import Enum
from copy import copy

class Token:
  class Type(Enum):
    IDENTIFIER = 0
    DECIMAL_INTEGER = 1

  def __init__(
    self,
    token_type: Type,
    lexeme: str,
    literal: Optional[Union[str, int]],
    position: CursorRange,
  ):
    self._token_type = token_type
    self._lexeme = lexeme
    self._literal = literal
    self._position = copy(position)

  def __eq__(self, other: Token) -> bool:
    return self._token_type == other._token_type and \
           self._lexeme == other._lexeme and \
           self._literal == other._literal and \
           self._position == other._position

  def __ne__(self, other: Token) -> bool:
    return not self == other

  @property
  def token_type(self) -> Type:
    return self._token_type

  @property
  def lexeme(self) -> str:
    return self._lexeme

  @property
  def literal(self) -> Optional[Union[str, int]]:
    return self._literal

  @property
  def position(self) -> CursorRange:
    return self._position


  def to_string(self, verbose: bool = False) -> str:
    if verbose:
      return f'{self._token_type.name}(\'{self._lexeme}\') at {self._position.to_string(True)}'
    else:
      return f'{self._token_type.name}(\'{self._lexeme}\')@{self._position.to_string()}'
