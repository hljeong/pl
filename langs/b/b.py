from __future__ import annotations

from common import Lexer
from grammar import Grammar
from plast import Parser, Visitor

with open('langs/b/spec/b.cbnf') as b_cbnf_f:
  b_cbnf = ''.join(b_cbnf_f.readlines())
b_grammar = Grammar('b', b_cbnf)

class BParser:
  def __init__(self, prog: str):
    lexer = Lexer(b_grammar, prog)
    parser = Parser(b_grammar, lexer.tokens)
    self._ast: Node = parser.ast

  @property
  def ast(self) -> Node:
    return self._ast
