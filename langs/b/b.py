from __future__ import annotations

from common import Log, log_time
from lexical import Lexer
from syntax import Grammar, Parser, Visitor, visit_it, telescope

with open('langs/b/spec/b.xbnf') as b_xbnf_f:
  b_xbnf = ''.join(b_xbnf_f.readlines())
b_grammar = Grammar('b', b_xbnf)

class BParser:
  @log_time
  def __init__(self, prog: str):
    lexer = Lexer(b_grammar, prog)
    parser = Parser(b_grammar, lexer.tokens)
    self._ast: Node = parser.ast

  @property
  def ast(self) -> Node:
    return self._ast



class BPrinter:
  tab = '  '

  def __init__(self, ast: Node):
    node_visitors: dict[str, Callable[[Node, Visitor], Any]] = {
      '<b>': self.visit_b,
      '<block>': self.visit_block,
      '<statement>': self.visit_statement,
      '<expression>': self.visit_expression,
    }
    self._tab_stop = 0
    self._str: str = Visitor(
      ast,
      node_visitors,
      lambda terminal_node, _: terminal_node.lexeme
    ).ret

  @property
  def str(self) -> str:
    return self._str

  def visit_b(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    prog: str = '\n'.join(visitor.visit(child) for child in node[0])
    return prog

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

        inner_prog: str = '\n'.join(visitor.visit(child) for child in node[1])

        self._tab_stop -= 1

        return '\n'.join(['{', inner_prog, f'{self._tab_stop * BPrinter.tab}}}'])

  def visit_statement(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.choice:
      # <statement> ::= <variable> "=" (<operand> | <expression> | <string>) ";" |
      case 0:
        return f'{self._tab_stop * BPrinter.tab}{visitor.visit(node[0])} = {visitor.visit(node[2][0])};'

      # <statement> ::= ("print" | "printi" | "read" | "readi") "\(" <variable> "\)" ";" |
      case 1:
        return f'{self._tab_stop * BPrinter.tab}{telescope(node[0]).lexeme}({visitor.visit(node[2][0])})'

      # <statement> ::= "while" "\(" <expression> "\)" <block> |
      case 2:
        return f'{self._tab_stop * BPrinter.tab}while ({visitor.visit(node[2])}) {visitor.visit(node[4])}'

      # <statement> ::= "if" "\(" <expression> "\)" <block>;
      case 3:
        return f'{self._tab_stop * BPrinter.tab}if ({visitor.visit(node[2])}) {visitor.visit(node[4])}'

  def visit_expression(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
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
    Visitor(
      ast,
      node_visitors,
    ).ret

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
        return f'{visitor.env["tab_stop"] * Bcompiler.tab}{node[0].lexeme}({telescope(node[2]).lexeme})'

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
        return f'{telescope(node[0]).lexeme}{visitor.visit(node[1])}'

      # <expression> ::= <operand> <binary_operator> <operand>;
      case 1:
        return f'{visitor.visit(node[0])} {telescpoe(node[1]).lexeme} {visitor.visit(node[2])}'

  def visit_operand(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    return telescope(node).lexeme
