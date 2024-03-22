from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re

@dataclass(eq=False, match_args=False)
class TokenPatternDefinition:
  token_pattern: str
  literal_parser: Callable[[str], Any] = None
  generate_token: bool = True

  def make_plain(plain_pattern: str) -> TokenPatternDefinition:
    return TokenPatternDefinition(
      plain_pattern,
      None,
      True,
    )

@dataclass(eq=False, match_args=False)
class TokenMatcherDefinition:
  token_matcher: re.Pattern
  literal_parser: Callable[[str], Any] = None
  generate_token: bool = True

  def from_token_pattern_definition(
    definition: TokenPatternDefinition
  ) -> TokenMatcherDefinition:
    return TokenMatcherDefinition(
      re.compile(f'\\A{definition.token_pattern}'),
      definition.literal_parser,
      definition.generate_token,
    )

builtin_tokens = {
  'identifier': TokenPatternDefinition(
    r'[A-Za-z_$][A-Za-z0-9_$]*',
    str,
    True,
  ),
  'decimal_integer': TokenPatternDefinition(
    r'0|[1-9][0-9]*',
    int,
    True,
  ),
  'escaped_string': TokenPatternDefinition(
    r'"(\.|[^\"])*"',
    lambda lexeme: lexeme[1 : -1],
    True,
  ),
}

class Token:
  def __init__(
    self,
    token_type: str,
    lexeme: str,
    literal: Optional[Union[str, int]] = None,
    extra: dict[str, Any] = {},
  ):
    self._token_type = token_type
    self._lexeme = lexeme
    self._literal = literal
    self._extra = extra

  def __eq__(self, other: Token) -> bool:
    return self._token_type == other._token_type and \
           self._lexeme == other._lexeme and \
           self._literal == other._literal

  def __ne__(self, other: Token) -> bool:
    return not self == other

  @property
  def token_type(self) -> str:
    return self._token_type

  @property
  def lexeme(self) -> str:
    return self._lexeme

  @property
  def literal(self) -> Optional[Union[str, int]]:
    return self._literal

  # todo: access control
  @property
  def extra(self) -> dict[str, Any]:
    return self._extra

  def __str__(self) -> str:
    # builtin token type
    if self._token_type in builtin_tokens:
      return f'{self._token_type}(\'{self._lexeme}\')'

    else:
      return f'\'{self._lexeme}\''

  def __repr__(self) -> str:
    return f'Token({self})'
