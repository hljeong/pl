from __future__ import annotations
from typing import Generic, TypeVar

from common import Monad, Log, log_time
from lexical import Lexer
from syntax import Grammar, Parser, Visitor

with open('langs/b/spec/b.xbnf') as b_xbnf_f:
  b_xbnf = ''.join(b_xbnf_f.readlines())
b_grammar = Grammar('b', b_xbnf)

class BParser:
  def parse(self, prog: str):
    return Monad(prog) \
      .then(Lexer(b_grammar.vocabulary).lex) \
      .then(Parser(b_grammar).parse) \
      .value



class BPrinter(Visitor):
  _tab = '  '

  def __init__(self):
    super().__init__(
      {
        '<b>': self._visit_b,
        '<block>': self._visit_block,
        '<statement>': self._visit_statement,
        '<expression>': self._visit_expression,
      },
      default_nonterminal_node_visitor=Visitor.visit_telescope,
      default_terminal_node_visitor=lambda terminal_node, _: terminal_node.lexeme,
    )
    self._tab_stop = 0

  def print(self, ast: ASTNode) -> str:
    return self.visit(ast)

  def _visit_b(
    self,
    node: ASTNode,
    visitor: Visitor,
  ) -> str:
    prog: str = '\n'.join(visitor.visit(child) for child in node[0])
    return prog

  def _visit_block(
    self,
    node: ASTNode,
    visitor: Visitor,
  ) -> str:
    match node.choice:
      # <block> ::= <statement>;
      case 0:
        return visitor.visit(node[0])

      # <block> ::= "{" <statements> "}";
      case 1:
        self._tab_stop += 1

        inner_prog: str = '\n'.join(visitor.visit(child) for child in node[1])

        self._tab_stop -= 1

        return '\n'.join(['{', inner_prog, f'{self._tab_stop * BPrinter._tab}}}'])

  def _visit_statement(
    self,
    node: ASTNode,
    visitor: Visitor,
  ) -> str:
    match node.choice:
      # <statement> ::= <variable> "=" (<operand> | <expression> | <string>) ";" |
      case 0:
        return f'{self._tab_stop * BPrinter._tab}{visitor.visit(node[0])} = {visitor.visit(node[2][0])};'

      # <statement> ::= ("print" | "printi" | "read" | "readi") "\(" <variable> "\)" ";" |
      case 1:
        return f'{self._tab_stop * BPrinter._tab}{Visitor.telescope(node[0]).lexeme}({visitor.visit(node[2][0])})'

      # <statement> ::= "while" "\(" <expression> "\)" <block> |
      case 2:
        return f'{self._tab_stop * BPrinter._tab}while ({visitor.visit(node[2])}) {visitor.visit(node[4])}'

      # <statement> ::= "if" "\(" <expression> "\)" <block>;
      case 3:
        return f'{self._tab_stop * BPrinter._tab}if ({visitor.visit(node[2])}) {visitor.visit(node[4])}'

  def _visit_expression(
    self,
    node: ASTNode,
    visitor: Visitor,
  ) -> str:
    match node.choice:
      # <expression> ::= <unary_operator> <operand>;
      case 0:
        return f'{visitor.visit(node[0])}{visitor.visit(node[1])}'

      # <expression> ::= <operand> <binary_operator> <operand>;
      case 1:
        return f'{visitor.visit(node[0])} {visitor.visit(node[1])} {visitor.visit(node[2])}'



# todo: use ast generated from xbnf grammar
class BAllocator:
  str_buffer_len = 32

  def __init__(self, ast: Node):
    node_visitors: dict[str, Callable[[Node, Visitor], Any]] = {
      'b': self.visit_b,
      'block': self.visit_block,
      'statements': self.visit_statements,
      'statement': self.visit_statement,
    }
    self._alloc: dict[str, int] = {}
    self._next: int = 0
    Visitor(node_visitors).visit(ast)

  @property
  def alloc(self) -> dict[str, int]:
    return self._alloc

  def visit_b(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    visitor.visit(node[0])
    if node.choice == 0:
      visitor.visit(node[1])

    return self._alloc

  def visit_block(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.choice:
      # <block> ::= <statement>;
      case 0:
        return visitor.visit(node[0])

      # <block> ::= "{" <statements> "}";
      case 1:
        visitor.visit(node[1])

  def visit_statements(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    visitor.visit(node[0])
    if node.choice == 0:
      visitor.visit(node[1])

  def visit_statement(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.choice:
      # <statement> ::= <variable> "=" <operand> ";";
      # <statement> ::= <variable> "=" <expression> ";";
      case 0 | 1:
        varname: str = node[0][0].lexeme
        if varname not in self._alloc:
          self._alloc[varname] = self._next
          self._next += 1

      # <statement> ::= <variable> "=" <string> ";";
      case 2:
        varname: str = node[0][0].lexeme
        str_literal: str = node[2][0].literal
        if varname not in self._alloc:
          self._alloc[varname] = self._next
          self._next += len(str_literal) + 1

      # <statement> ::= "read" "\(" <variable> "\)" ";";
      case 5:
        varname: str = node[2][0].lexeme
        if varname not in self._alloc:
          self._alloc[varname] = self._next
          self._next += BAllocator.str_buffer_len + 1

      # <statement> ::= "readi" "\(" <variable> "\)" ";";
      case 6:
        varname: str = node[2][0].lexeme
        if varname not in self._alloc:
          self._alloc[varname] = self._next
          self._next += 1

  node_visitors = {
  }



# todo: finish + also switch to using ast generated from xbnf grammar
class BCompiler:
  def __init__(self, ast: Node, alloc: dict[str, int]):
    node_visitors: dict[str, Callable[[Node, Visitor], Any]] = {
      'b': self.visit_b,
      'block': self.visit_block,
      'statements': self.visit_statements,
      'statement': self.visit_statement,
      'expression': self.visit_expression,
      'operand': self.visit_operand,
    }
    self._alloc = alloc
    self._a_ast: Node = Visitor(
      ast,
      node_visitors,
    ).ret

  @property
  def a_ast(self) -> Node:
    return self._a_ast

  def visit_b(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.choice:
      # <b> ::= <block> <b>;
      case 0:
        a_ast_tail: Node = visitor.visit(node[1])
        a_ast: Node = visitor.visit(node[0])
        a_ast.add(a_ast_tail)

      # <b> ::= <block>;
      case 1:
        pass

  def visit_block(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.choice:
      # <block> ::= <statement>;
      case 0:
        return visitor.visit(node[0])

      # <block> ::= "{" <statements> "}";
      case 1:
        self._tab_stop += 1
        prog: str = '\n'.join(['{', visitor.visit(node[1]), f'{(self._tab_stop - 1) * Bcompiler.tab}}}'])
        self._tab_stop -= 1
        return prog

  def visit_statements(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    prog: str = visitor.visit(node[0])
    if node.choice == 0:
      prog = '\n'.join([prog, visitor.visit(node[1])])
    return prog

  def visit_statement(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.choice:
      # <statement> ::= <variable> "=" <operand> ";";
      # <statement> ::= <variable> "=" <expression> ";";
      case 0 | 1:
        return f'{visitor.env["tab_stop"] * Bcompiler.tab}{node[0][0].lexeme} = {visitor.visit(node[2])};'

      # <statement> ::= <variable> "=" <string> ";";
      case 2:
        return f'{visitor.env["tab_stop"] * Bcompiler.tab}{node[0][0].lexeme} = {node[2][0].lexeme};'

      # <statement> ::= "print" "\(" <variable> "\)" ";";
      # <statement> ::= "printi" "\(" <variable> "\)" ";";
      # <statement> ::= "read" "\(" <variable> "\)" ";";
      # <statement> ::= "readi" "\(" <variable> "\)" ";";
      case 3 | 4 | 5 | 6:
        return f'{visitor.env["tab_stop"] * Bcompiler.tab}{node[0].lexeme}({Visitor.telescope(node[2]).lexeme})'

      # <statement> ::= "while" "\(" <expression> "\)" <block>;
      # <statement> ::= "if" "\(" <expression> "\)" <block>;
      case 7 | 8:
        return f'{visitor.env["tab_stop"] * Bcompiler.tab}while ({visitor.visit(node[2])}) {visitor.visit(node[4])}'

  def visit_expression(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.choice:
      # <expression> ::= <unary_operator> <operand>;
      case 0:
        return f'{Visitor.telescope(node[0]).lexeme}{visitor.visit(node[1])}'

      # <expression> ::= <operand> <binary_operator> <operand>;
      case 1:
        return f'{visitor.visit(node[0])} {Visitor.telescope(node[1]).lexeme} {visitor.visit(node[2])}'

  def visit_operand(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    return Visitor.telescope(node).lexeme
