from __future__ import annotations
from copy import copy

from plast import Node

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

  def parse(self, node_type: str, backtrack: bool = False) -> Optional[Union[Node, list[Node], Token]]:
    save: int = self._current
    # todo: type annotation
    parser: Any = self._grammar.get_parser(node_type)
    node: Optional[Union[Node, list[Node], Token]] = parser(self)
    if node is None or backtrack:
      self._current = save
    return node
    # return self._grammar.get_parser(node_type)(self)

  def at_end(self) -> bool:
    return self._current >= len(self._tokens)

  def __peek(self) -> Token:
    return self._tokens[self._current]

  # todo: delete
  def peek(self) -> Token:
    if self.at_end():
      return 'EOF'
    else:
      return self.__peek()

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

  def print_parsed_tokens(self):
    print(' '.join(map(str, self._tokens[:self._current])))



def generate_extended_nonterminal_parser(
  nonterminal: str,
  body: list[list[ExpressionTerm]]
) -> Callable[[Parser], Optional[Union[Node, list[Token], Token]]]:
  def nonterminal_parser(parser: Parser, entry_point = False) -> Optional[Union[Node, list[Token], Token]]:
    parser.print_parsed_tokens()
    print(f'now parsing <{nonterminal}> (next token is {parser.peek()})')
    print()
    # fix: bad hack
    backtrack: bool = len(body) > 1
    production_matches = {}
    for idx, expression_terms in enumerate(body):
      node: Node = Node(nonterminal, idx)
      good: bool = True
      for expression_term in expression_terms:
        match expression_term.multiplicity:
          # exactly 1 (default)
          case 1:
            child: Union[Node, Token] = parser.parse(expression_term.node_type, backtrack=backtrack)
            if child is None:
              good = False
              break

          # constant number > 1
          case _ if type(expression_term.multiplicity) is int and expression_term.multiplicity > 1:
            child: list[Node] = []
            for i in range(expression_term.multiplicity):
              child_node: Union[Node, Token] = parser.parse(expression_term.node_type, backtrack=backtrack)
              if child_node is None:
                good = False
                break
              child.append(child_node)
            if not good:
              break

          # optional
          case '?':
            child: list[Node] = []
            child_node: Union[Node, Token] = parser.parse(expression_term.node_type, backtrack=backtrack)
            if child_node is not None:
              child.append(child_node)

          # any number
          case '*':
            child: list[Node] = []
            while True:
              child_node: Union[Node, Token] = parser.parse(expression_term.node_type, backtrack=backtrack)
              if child_node is None:
                break
              child.append(child_node)

          # at least 1
          case '+':
            child: list[Node] = []
            child_node: Union[Node, Token] = parser.parse(expression_term.node_type, backtrack=backtrack)
            if child_node is None:
              good = False
              break
            child.append(child_node)
            while True:
              child_node: Union[Node, Token] = parser.parse(expression_term.node_type, backtrack=backtrack)
              if child_node is None:
                break
              child.append(child_node)

        if good:
          node.add(child)

      if good:
        production_matches[idx] = node

    if len(production_matches) == 0:
      return None
    
    longest_match_idx = max(production_matches, key=lambda idx: len(production_matches[idx].tokens))
    if backtrack:
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

    print(production_matches[longest_match_idx])
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
    parser.print_parsed_tokens()
    print(f'now parsing {terminal} (next token is {parser.peek()})')
    print()
    return parser.expect(terminal)
  return terminal_parser
