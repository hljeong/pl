from __future__ import annotations
from typing import Callable

from common import Cursor, CursorRange, Token
from ast import ASTNode
from .parser import ASTParser

def generate_nonterminal_parser(nonterminal: str, rules: list[list[str]]) -> Callable[[ASTParser], Optional[Union[ASTNode, Token]]]:
  def term_parser(parser: ASTParser, entry_point = False) -> Optional[Union[ASTNode, Token]]:
    for idx, rule in enumerate(rules):
      node: ASTNode = ASTNode(nonterminal, idx)
      good: bool = True
      for term in rule:
        subnode: Optional[Union[ASTNode, Token]] = parser.parse(term)
        if subnode is None:
          parser.backtrack(len(node.tokens))
          good = False
          break
        node.add(subnode)
      if good:
        return node
    return None
  return term_parser

def generate_terminal_parser(terminal: Token.Type) -> Callable[[ASTParser], Optional[Union[ASTNode, Token]]]:
  def token_parser(parser: ASTParser) -> Optional[Union[ASTNode, Token]]:
    return parser.expect(terminal)
  return token_parser
