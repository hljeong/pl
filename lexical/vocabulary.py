from __future__ import annotations
import re

from common import Log

class Vocabulary:
  
  # todo: custom regex engine to support matching multiple definitions at the same time
  class Definition:
    def __init__(
      self,
      matcher: re.Pattern,
      literal_generator: Callable[[str], Any] = lambda _: None,
    ):
      self._matcher = matcher
      self._literal_generator = literal_generator

    @property
    def matcher(self) -> re.Pattern:
      return self._matcher

    @property
    def literal_generator(self) -> re.Pattern:
      return self._literal_generator

    # todo: no regex shenanigans with exact matches (e.g. \*)
    def make(
      pattern: str,
      literal_generator: Callable[[str], Any] = lambda _: None,
    ) -> Vocabulary.Definition:
      return Vocabulary.Definition(
        re.compile(f'\\A{pattern}'),
        literal_generator,
      )



  DEFAULT_IGNORE = ['[ \t\n]+']
  
  def __init__(
    self,
    dictionary: dict[str, Definition],
    ignore: list[str] = DEFAULT_IGNORE,
  ):
    self._dictionary: dict[str, Definition] = dictionary
    self._dictionary.update(Vocabulary.Definition.builtin)
    # todo: ew
    self._ignore: list[re.Pattern] = list(map(lambda pattern: re.compile(f'\\A{pattern}'), ignore))

  def __iter__(self) -> Iterator[str]:
    return iter(self._dictionary)

  def __getitem__(self, key: str) -> Definition:
    if key in self._dictionary:
      return self._dictionary[key]

    else:
      # todo: add 'do you mean...'?
      raise KeyError(f'\'{key}\' does not exist in dictionary')

  @property
  def ignore(self) -> list[str]:
    return self._ignore



Vocabulary.Definition.builtin: dict[str, Definition] = {
  'identifier': Vocabulary.Definition.make(
    r'[A-Za-z_$][A-Za-z0-9_$]*',
    str,
  ),
  'decimal_integer': Vocabulary.Definition.make(
    r'0|[1-9][0-9]*',
    int,
  ),
  'escaped_string': Vocabulary.Definition.make(
    r'"(\.|[^\"])*"',
    lambda lexeme: lexeme[1 : -1],
  ),
}
