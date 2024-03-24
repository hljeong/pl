from __future__ import annotations
from copy import copy
from typing import NamedTuple

from common import Log, slowdown
from lexical import Token

from .ast import ASTNode, NonterminalASTNode, ChoiceNonterminalASTNode, TerminalASTNode

# todo: use dataclass?
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

  class Result(NamedTuple):
    node: ASTNode
    n_tokens_consumed: int

  def __init__(
    self,
    grammar: Grammar,
    tokens: list[Token],
  ):
    self._grammar: Grammar = grammar
    self._tokens: list[Token] = tokens
    self._current: int = 0
    self._root: ASTNode = self.__parse()

  def __parse(self) -> ASTNode:
    parse_result: Parser.Result = self._grammar.entry_point_parser(self)

    # todo: ParseError
    if parse_result is None:
      raise ValueError('failed to parse')

    elif not self.at_end():
      raise ValueError('did not parse to end of file')

    return parse_result.node

  def parse(self, node_type: str, backtrack: bool = False) -> Optional[Parser.Result]:
    Log.t(f'parsing {node_type}, next token (index {self._current}) is {self.__safe_peek()}')

    # todo: type annotation
    parser: Any = self._grammar.get_parser(node_type)
    parse_result: Optional[Parser.Result] = parser(self, False)

    Log.begin_t()
    if parse_result is None:
      Log.t(f'unable to parse {node_type}')
    else:
      Log.t(f'parsed {node_type}')

    Log.t(f'next token (index {self._current}) is {self.__safe_peek()}')
    Log.end_t()

    return parse_result

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
    Log.t(f'expecting {token_type}')

    if self.at_end():
      Log.t(f'got EOF')
      return None

    token: Token = self.__peek()
    Log.t(f'got {token.token_type}')
    if token.token_type != token_type:
      return None

    self.__advance(1)
    return token

  def __advance(self, n_tokens: int) -> None:
    self._current += n_tokens

  def __save(self) -> int:
    return self._current

  def __backtrack(self, to: int) -> None:
    self._current = to

  @property
  def ast(self) -> ASTNode:
    return self._root

  def generate_nonterminal_parser(
    nonterminal: str,
    body: list[list[ExpressionTerm]]
  ) -> Callable[[Parser], Optional[ChoiceNonterminalASTNode]]:

    def nonterminal_parser(parser: Parser, entry_point = True) -> Optional[ChoiceNonterminalASTNode]:

      choices = {}

      for idx, expression_terms in enumerate(body):

        node: ChoiceNonterminalASTNode = ChoiceNonterminalASTNode(nonterminal, idx)
        good: bool = True
        save: int = parser.__save()
        n_tokens_consumed: int = 0

        for expression_term_idx, expression_term in enumerate(expression_terms):
          match expression_term.multiplicity:
            # exactly 1 (default)
            case 1:
              child_parse_result: Parser.Result = parser.parse(expression_term.node_type)

              if child_parse_result is not None:
                child_node: ASTNode
                child_n_tokens_consumed: int
                child_node, child_n_tokens_consumed = child_parse_result

                node.add(child_node)
                n_tokens_consumed += child_n_tokens_consumed

              else:
                good = False
                break

            # constant number > 1
            case _ if type(expression_term.multiplicity) is int and expression_term.multiplicity > 1:
              child: NonterminalASTNode = NonterminalASTNode(f'{nonterminal}:{expression_term_idx}{expression_term.multiplicity}')

              for _ in range(expression_term.multiplicity):
                grandchild_parse_result: Parser.Result = parser.parse(expression_term.node_type)

                if grandchild_parse_result is not None:
                  grandchild_node: ASTNode
                  grandchild_n_tokens_consumed: int
                  grandchild_node, grandchild_n_tokens_consumed = grandchild_parse_result

                  child.add(grandchild_node)
                  n_tokens_consumed += grandchild_n_tokens_consumed

                else:
                  good = False
                  break

              if good:
                node.add(child)

              else:
                break

            # optional
            case '?':
              child: NonterminalASTNode = NonterminalASTNode(f'{nonterminal}:{expression_term_idx}{expression_term.multiplicity}')
              grandchild_parse_result: Parser.Result = parser.parse(expression_term.node_type)

              if grandchild_parse_result is not None:
                grandchild_node: ASTNode
                grandchild_n_tokens_consumed: int
                grandchild_node, grandchild_n_tokens_consumed = grandchild_parse_result

                child.add(grandchild_node)
                n_tokens_consumed += grandchild_n_tokens_consumed

              node.add(child)

            # any number
            case '*':
              child: NonterminalASTNode = NonterminalASTNode(f'{nonterminal}:{expression_term_idx}{expression_term.multiplicity}')

              while True:
                grandchild_parse_result: Parser.Result = parser.parse(expression_term.node_type)

                if grandchild_parse_result is not None:
                  grandchild_node: ASTNode
                  grandchild_n_tokens_consumed: int
                  grandchild_node, grandchild_n_tokens_consumed = grandchild_parse_result

                  child.add(grandchild_node)
                  n_tokens_consumed += grandchild_n_tokens_consumed

                else:
                  break

              node.add(child)

            # at least 1
            case '+':
              child: NonterminalASTNode = NonterminalASTNode(f'{nonterminal}:{expression_term_idx}{expression_term.multiplicity}')

              grandchild_parse_result: Parser.Result = parser.parse(expression_term.node_type)
              if grandchild_parse_result is not None:
                grandchild_node: ASTNode
                grandchild_n_tokens_consumed: int
                grandchild_node, grandchild_n_tokens_consumed = grandchild_parse_result

                child.add(grandchild_node)
                n_tokens_consumed += grandchild_n_tokens_consumed
              
              else:
                good = False
                break

              while True:
                grandchild_parse_result: Parser.Result = parser.parse(expression_term.node_type)

                if grandchild_parse_result is not None:
                  grandchild_node: ASTNode
                  grandchild_n_tokens_consumed: int
                  grandchild_node, grandchild_n_tokens_consumed = grandchild_parse_result

                  child.add(grandchild_node)
                  n_tokens_consumed += grandchild_n_tokens_consumed
                
                else:
                  break

              node.add(child)

        if good:
          choices[idx] = Parser.Result(node, n_tokens_consumed)
        parser.__backtrack(save)

      if len(choices) == 0:
        return None
      
      longest_match_idx = max(choices, key=lambda idx: choices[idx].n_tokens_consumed)

      parser.__advance(choices[longest_match_idx].n_tokens_consumed)

      return choices[longest_match_idx]

    return nonterminal_parser



  def generate_terminal_parser(terminal: str) -> Callable[[Parser], Optional[TerminalASTNode]]:

    def terminal_parser(parser: Parser, entry_point: bool = False) -> Optional[Union[Node, Token]]:
      token: Token = parser.expect(terminal)
      if token is None:
        return None
      return Parser.Result(TerminalASTNode(terminal, token), 1)

    return terminal_parser
