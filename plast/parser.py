from __future__ import annotations

from .ast import Node

class Parser:
  def __init__(
    self,
    grammar: Grammar,
    tokens: list[Token],
  ):
    self._grammar: Grammar = grammar
    self._tokens: list[Token] = tokens
    self._current: int = 0
    self._root: Node = self.__parse()
    if not self.at_end():
      raise ValueError('did not parse to end of file')

  def __parse(self) -> Node:
    return self._grammar.entry_point_parser(self, True)

  def parse(self, node_type: str) -> Node:
    return self._grammar.get_parser(node_type)(self)

  def at_end(self) -> bool:
    return self._current >= len(self._tokens)

  def __peek(self) -> Token:
    return self._tokens[self._current]

  def expect(self, token_type: str) -> Optional[Token]:
    if self.at_end():
      return None

    token: Token = self.__peek()
    if token.token_type != token_type:
      return None
    self._current += 1
    return token

  def backtrack(self, n_tokens: int) -> None:
    self._current -= n_tokens

  @property
  def ast(self) -> Node:
    return self._root

def generate_nonterminal_parser(nonterminal: str, rules: list[list[str]]) -> Callable[[Parser], Optional[Union[Node, Token]]]:
  def nonterminal_parser(parser: Parser, entry_point = False) -> Optional[Union[Node, Token]]:
    for idx, rule in enumerate(rules):
      node: Node = Node(nonterminal, idx)
      good: bool = True
      for term in rule:
        subnode: Optional[Union[Node, Token]] = parser.parse(term)
        if subnode is None:
          parser.backtrack(len(node.tokens))
          good = False
          break
        node.add(subnode)
      if good:
        return node
    return None
  return nonterminal_parser

def generate_terminal_parser(terminal: str) -> Callable[[Parser], Optional[Union[Node, Token]]]:
  def terminal_parser(parser: Parser) -> Optional[Union[Node, Token]]:
    return parser.expect(terminal)
  return terminal_parser
