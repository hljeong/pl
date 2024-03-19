from __future__ import annotations
from copy import copy

from common import Cursor, CursorRange, Token

IDENTIFIER_FIRST_MATCH = [
  'A', 'B', 'C', 'D', 'E', 'F', 'G',
  'H', 'I', 'J', 'K', 'L', 'M', 'N',
  'O', 'P', 'Q', 'R', 'S', 'T', 'U',
  'V', 'W', 'X', 'Y', 'Z', 
  'a', 'b', 'c', 'd', 'e', 'f', 'g',
  'h', 'i', 'j', 'k', 'l', 'm', 'n',
  'o', 'p', 'q', 'r', 's', 't', 'u',
  'v', 'w', 'x', 'y', 'z', 
  '_', '$',
]

IDENTIFIER_REST_MATCH = [
  'A', 'B', 'C', 'D', 'E', 'F', 'G',
  'H', 'I', 'J', 'K', 'L', 'M', 'N',
  'O', 'P', 'Q', 'R', 'S', 'T', 'U',
  'V', 'W', 'X', 'Y', 'Z', 
  'a', 'b', 'c', 'd', 'e', 'f', 'g',
  'h', 'i', 'j', 'k', 'l', 'm', 'n',
  'o', 'p', 'q', 'r', 's', 't', 'u',
  'v', 'w', 'x', 'y', 'z', 
  '0', '1', '2', '3', '4',
  '5', '6', '7', '8', '9',
  '_', '$',
]

DECIMAL_INTEGER_NON_ZERO_FIRST_MATCH = [
  '1', '2', '3', '4', '5', '6', '7', '8', '9',
]

DECIMAL_INTEGER_REST_MATCH = [
  '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
]

WHITE_SPACE_MATCH = [
  ' ', '\t', '\r',
]

class Lexer:
  def __init__(
    self,
    source: str,
  ):
    self._source = source
    self._start = 0
    self._start_cursor = Cursor(1, 1)
    self._current = 0
    self._current_cursor = Cursor(1, 1)
    self._lag_cursor = None
    self._tokens = []

    self.__lex()

  def __at_end(self) -> bool:
    return self._current >= len(self._source)

  def __peek(self) -> str:
    if self.__at_end():
      return '\0'
    else:
      return self._source[self._current]

  def __advance(self) -> None:
    if not self.__at_end():
      self._current += 1
      self._lag_cursor = copy(self._current_cursor)
      self._current_cursor = Cursor(self._current_cursor.line, self._current_cursor.column + 1)

  def __consume_match(self, ch) -> bool:
    if self.__peek() != ch:
      return False

    self.__advance()
    return True

  def __consume_match_set(self, ch_set) -> bool:
    return any(map(lambda ch: self.__consume_match(ch), ch_set))

  def __consume_expect(self, ch) -> None:
    if not self.__consume_match(ch):
      # todo: LexError?
      raise ValueError(f'expected \'{ch}\' at {self._current_cursor.to_string(True)}, found \'{self.__peek()}\'')

  def __consume_expect_set(self, ch_set) -> None:
    if not self.__consume_match_set(ch_set):
      # todo: LexError?
      ch_set_str = ' or '.join(map(lambda ch: f"'{ch}'", ch_set))
      raise ValueError(f'expected {ch_set_str} at {self._current_cursor.to_string(True)}, found {self.__peek()}')

  def __make_token(
    self,
    token_type: Token.Type,
    literal: Optional[Union[str, int]] = None,
  ) -> Token:
    lexeme = self._source[self._start : self._current]
    position = CursorRange(self._start_cursor, self._lag_cursor)
    return Token(token_type, lexeme, literal, position)

  def __scan_token(self) -> Token:
    if self.__consume_match_set(IDENTIFIER_FIRST_MATCH):
      while self.__consume_match_set(IDENTIFIER_REST_MATCH):
        pass

      token = self.__make_token(
        Token.Type.IDENTIFIER,
        self._source[self._start : self._current],
      )

    elif self.__consume_match_set(DECIMAL_INTEGER_NON_ZERO_FIRST_MATCH):
      while self.__consume_match_set(DECIMAL_INTEGER_REST_MATCH):
        pass

      token = self.__make_token(
        Token.Type.DECIMAL_INTEGER,
        int(self._source[self._start : self._current]),
      )

    elif self.__consume_match('0'):
      token = self.__make_token(
        Token.Type.DECIMAL_INTEGER,
        int(self._source[self._start : self._current]),
      )

    elif self.__consume_match('"'):
      while not self.__consume_match('"'):
        self.__consume_match('\\')
        self.__advance()

      token = self.__make_token(
        Token.Type.ESCAPED_STRING,
        bytes(self._source[self._start + 1 : self._current - 1], "utf-8").decode("unicode_escape"),
      )

    elif self.__consume_match(':'):
      self.__consume_expect(':')
      self.__consume_expect('=')

      token = self.__make_token(Token.Type.COLON_COLON_EQUAL)

    elif self.__consume_match(';'):
      token = self.__make_token(Token.Type.SEMICOLON)

    elif self.__consume_match('<'):
      token = self.__make_token(Token.Type.LESS_THAN)

    elif self.__consume_match('>'):
      token = self.__make_token(Token.Type.GREATER_THAN)

    elif self.__consume_match('#'):
      while self.__peek() != '\n' and not self.__at_end():
        self.__advance()
      token = None

    elif self.__consume_match_set(WHITE_SPACE_MATCH):
      token = None

    elif self.__consume_match('\n'):
      self._current_cursor = Cursor(self._current_cursor.line + 1, 1)
      token = None

    else:
      raise ValueError(f'invalid character ({self.__peek()}) encountered at {self._current_cursor.to_string(True)}')
    self._start = self._current
    self._start_cursor = copy(self._current_cursor)
    return token
        
  def __lex(self) -> None:
    while not self.__at_end():
      token = self.__scan_token()
      if token is not None:
        self._tokens.append(token)

  @property
  def tokens(self) -> list[Token]:
    return self._tokens
