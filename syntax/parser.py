from __future__ import annotations
from copy import copy

from common import Log
from lexical import Token

from .ast import Node

class ExpressionTerm:
  def __init__(
    self,
    node_type: str,
    multiplicity: Union[str, int] = 1,
  ):
    self._node_type = node_type
    self._multiplicity = multiplicity

  @property
  def node_type(self) -> str:
    return self._node_type

  @property
  def multiplicity(self) -> Union[str, int]:
    return self._multiplicity

  def __str__(self) -> str:
    if type(self._multiplicity) is int and self._multiplicity == 1:
      return f'{self._node_type}'
    else:
      return f'{self._node_type}{self._multiplicity}'

  def __repr__(self) -> str:
    return f'ExpressionTerm({self})'

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

  # todo: delete
  @property
  def current(self) -> int:
    return self._current

  # todo: delete
  def set_current(self, current: int) -> None:
    self._current = current

  def parse(self, node_type: str, backtrack: bool = False) -> Optional[Union[Node, list[Node], Token]]:
    Log.t(f'parsing {node_type}, next token (index {self._current}) is {self.__safe_peek()}')

    save: int = self._current
    # todo: type annotation
    parser: Any = self._grammar.get_parser(node_type)
    node: Optional[Union[Node, list[Node], Token]] = parser(self)

    if node is None:
      Log.t(f'unable to parse {node_type}, backtracking...')
      self._current = save
    else:
      Log.t(f'parsed {node_type}')

      if backtrack:
        Log.t('backtracking...')
        self._current = save
        

    Log.t(f'next token (index {self._current}) is {self.__safe_peek()}')

    return node
    # return self._grammar.get_parser(node_type)(self)

  def at_end(self) -> bool:
    return self._current >= len(self._tokens)

  def __peek(self) -> Token:
    return self._tokens[self._current]

  def __safe_peek(self) -> Token:
    if self.at_end():
      return 'EOF'
    else:
      return self.__peek()

  # todo: delete
  def peek(self) -> Token:
    return self.__safe_peek()

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



def generate_extended_nonterminal_parser(
  nonterminal: str,
  body: list[list[ExpressionTerm]]
) -> Callable[[Parser], Optional[Union[Node, list[Token], Token]]]:
  def nonterminal_parser(parser: Parser, entry_point = False) -> Optional[Union[Node, list[Token], Token]]:
    # todo: fix bad hack
    backtrack: bool = len(body) > 1
    production_matches = {}
    for idx, expression_terms in enumerate(body):
      node: Node = Node(nonterminal, idx)
      good: bool = True
      save: int = parser.current
      for expression_term in expression_terms:
        match expression_term.multiplicity:
          # exactly 1 (default)
          case 1:
            child: Union[Node, Token] = parser.parse(expression_term.node_type)
            if child is None:
              good = False
              break

          # constant number > 1
          case _ if type(expression_term.multiplicity) is int and expression_term.multiplicity > 1:
            child: list[Node] = []

            for i in range(expression_term.multiplicity):
              child_node: Union[Node, Token] = parser.parse(expression_term.node_type)
              if child_node is None:
                good = False
                break
              child.append(child_node)

            if not good:
              break

          # optional
          case '?':
            child: list[Node] = []
            child_node: Union[Node, Token] = parser.parse(expression_term.node_type)
            if child_node is not None:
              child.append(child_node)

          # any number
          case '*':
            child: list[Node] = []

            while True:
              child_node: Union[Node, Token] = parser.parse(expression_term.node_type)
              if child_node is None:
                break
              child.append(child_node)

          # at least 1
          case '+':
            child: list[Node] = []

            child_node: Union[Node, Token] = parser.parse(expression_term.node_type)
            if child_node is None:
              good = False
              break
            child.append(child_node)

            while True:
              child_node: Union[Node, Token] = parser.parse(expression_term.node_type)

              if child_node is None:
                break

              child.append(child_node)


        if good:
          node.add(child)

      if good:
        production_matches[idx] = node

      # todo: fix bad hack
      parser.set_current(save)

    if len(production_matches) == 0:
      return None
    
    longest_match_idx = max(production_matches, key=lambda idx: len(production_matches[idx].tokens))

    for child in production_matches[longest_match_idx].children:
      if type(child) is list:
        for child_node in child:
          parser.parse(child_node.node_type)

      elif type(child) is Node:
        parser.parse(child.node_type)

      elif type(child) is Token:
        parser.parse(child.token_type)

      else:
        # todo
        raise ValueError('bad type')

    return production_matches[longest_match_idx]

  return nonterminal_parser

def generate_nonterminal_parser(nonterminal: str, rules: list[list[ExpressionTerm]]) -> Callable[[Parser], Optional[Union[Node, Token]]]:
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
