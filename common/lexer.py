from __future__ import annotations
from copy import copy
import re

from .cursor import Cursor, CursorRange
from .token import Token, TokenPatternDefinition, TokenMatcherDefinition

matchers = {
  'white_space': re.compile('\\A[ \t]+'),
  '\n': re.compile('\\A\n'),
}

class Lexer:
  def __init__(
    self,
    grammar: Grammar,
    source: str,
  ):
    self.__load_token_defs(grammar)
    self._source: str = source
    self._start: int = 0
    self._start_cursor: Cursor = Cursor(1, 1)
    self._current: int = 0
    self._current_cursor: Cursor = Cursor(1, 1)
    self._lag_cursor: Cursor = None
    self._tokens: list[Token] = []

    self.__lex()

  def __load_token_defs(
    self,
    grammar: Grammar,
  ):
    self._token_defs: dict[str, TokenMatcherDefinition] = {
      token_type: TokenMatcherDefinition.from_token_pattern_definition(definition) \
        for token_type, definition in grammar.token_defs.items()
    }

    for pattern in grammar.ignore:
      self._token_defs[pattern] = TokenMatcherDefinition(
        re.compile(f'\\A{pattern}'),
        None,
        False,
      )

  def __at_end(self):
    return self._current >= len(self._source)

  def __peek(self) -> str:
    if self.__at_end():
      return '\0'
    else:
      return self._source[self._current]

  def __advance(self, steps: int) -> None:
    for _ in range(steps):
      if not self.__at_end():
        self._current += 1
        self._lag_cursor = copy(self._current_cursor)
        self._current_cursor = Cursor(self._current_cursor.line, self._current_cursor.column + 1)
      else:
        break

  # todo: efficiency
  def __match(self, matcher: re.Pattern) -> re.Match:
    return matcher.match(self._source[self._current:])

  def __consume_match(self, matcher_name: str) -> bool:
    match = self.__match(matchers[matcher_name])
    if match:
      self.__advance(len(match.group()))
      return True
    return False

  def __make_token(
    self,
    token_type: str,
  ) -> Token:
    if not self._token_defs[token_type].generate_token:
      return None

    lexeme = self._source[self._start : self._current]

    literal_parser = self._token_defs[token_type].literal_parser
    literal = None
    if literal_parser:
      literal = literal_parser(lexeme)
    
    position = CursorRange(self._start_cursor, self._lag_cursor)

    return Token(
      token_type,
      lexeme,
      literal,
      { 'position': position },
    )

  def __scan_token(self) -> tuple[bool, Optional[Token]]:
    token_matches = {}
    for token_type in self._token_defs:
      token_match = self.__match(self._token_defs[token_type].token_matcher)
      if token_match:
        token_matches[token_type] = token_match.group()

    if len(token_matches) == 0:
      if self.__consume_match('white_space'):
        pass

      elif self.__consume_match('\n'):
        self._current_cursor = Cursor(self._current_cursor.line + 1, 1)

      else:
        raise ValueError(f'invalid character \'{self.__peek()}\' encountered at {self._current_cursor.to_string()}')

      token = None

    else:
      longest_match_token_type = max(token_matches, key=lambda token_type: len(token_matches[token_type]))
      self.__advance(len(token_matches[longest_match_token_type]))
      # todo: fix this hack
      if self._source[self._start : self._current] in token_matches:
        longest_match_token_type = self._source[self._start : self._current]

      token = self.__make_token(longest_match_token_type)

    self._start = self._current
    self._start_cursor = copy(self._current_cursor)
    return token

  def __lex(self):
    while not self.__at_end():
      token = self.__scan_token()
      if token is not None:
        self._tokens.append(token)

  @property
  def tokens(self) -> list[Token]:
    return self._tokens
