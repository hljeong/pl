from __future__ import annotations

from common import Lexer
from grammar import Grammar, XBNFGrammar
from plast import Parser, Visitor, visit_it, telescope

with open('langs/b/spec/b.cbnf') as b_cbnf_f:
  b_cbnf = ''.join(b_cbnf_f.readlines())
b_grammar = Grammar('b', b_cbnf)

with open('langs/b/spec/b.xbnf') as b_xbnf_f:
  b_xbnf = ''.join(b_xbnf_f.readlines())
b_xbnfgrammar = XBNFGrammar('b', b_xbnf)

class BParser:
  def __init__(self, prog: str):
    lexer = Lexer(b_grammar, prog)
    parser = Parser(b_grammar, lexer.tokens)
    self._ast: Node = parser.ast

  @property
  def ast(self) -> Node:
    return self._ast



class XBParser:
  def __init__(self, prog: str):
    lexer = Lexer(b_xbnfgrammar, prog)
    parser = Parser(b_xbnfgrammar, lexer.tokens)
    self._ast: Node = parser.ast

  @property
  def ast(self) -> Node:
    return self._ast



class BPrinter:
  tab = '  '

  def __init__(self, ast: Node):
    node_visitors: dict[str, Callable[[Node, Visitor], Any]] = {
      'b': self.visit_b,
      'block': self.visit_block,
      'statements': self.visit_statements,
      'statement': self.visit_statement,
      'expression': self.visit_expression,
      'operand': self.visit_operand,
    }
    self._tab_stop = 0
    self._str: str = Visitor(
      ast,
      node_visitors,
    ).ret

  @property
  def str(self) -> str:
    return self._str

  def visit_b(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    prog: str = visitor.visit(node.get(0))
    if node.production == 0:
      prog = '\n'.join([prog, visitor.visit(node.get(1))])
    return prog

  def visit_block(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.production:
      # <block> ::= <statement>;
      case 0:
        return visitor.visit(node.get(0))

      # <block> ::= "{" <statements> "}";
      case 1:
        self._tab_stop += 1
        prog: str = '\n'.join(['{', visitor.visit(node.get(1)), f'{(self._tab_stop - 1) * BPrinter.tab}}}'])
        self._tab_stop -= 1
        return prog

  def visit_statements(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    prog: str = visitor.visit(node.get(0))
    if node.production == 0:
      prog = '\n'.join([prog, visitor.visit(node.get(1))])
    return prog

  def visit_statement(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.production:
      # <statement> ::= <variable> "=" <operand> ";";
      # <statement> ::= <variable> "=" <expression> ";";
      case 0 | 1:
        return f'{self._tab_stop * BPrinter.tab}{node.get(0).get(0).lexeme} = {visitor.visit(node.get(2))};'

      # <statement> ::= <variable> "=" <string> ";";
      case 2:
        return f'{self._tab_stop * BPrinter.tab}{node.get(0).get(0).lexeme} = {node.get(2).get(0).lexeme};'

      # <statement> ::= "print" "\(" <variable> "\)" ";";
      # <statement> ::= "printi" "\(" <variable> "\)" ";";
      # <statement> ::= "read" "\(" <variable> "\)" ";";
      # <statement> ::= "readi" "\(" <variable> "\)" ";";
      case 3 | 4 | 5 | 6:
        return f'{self._tab_stop * BPrinter.tab}{node.get(0).lexeme}({node.get(2).get(0).lexeme})'

      # <statement> ::= "while" "\(" <expression> "\)" <block>;
      # <statement> ::= "if" "\(" <expression> "\)" <block>;
      case 7 | 8:
        return f'{self._tab_stop * BPrinter.tab}while ({visitor.visit(node.get(2))}) {visitor.visit(node.get(4))}'

  def visit_expression(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.production:
      # <expression> ::= <unary_operator> <operand>;
      case 0:
        return f'{node.get(0).get(0).lexeme}{visitor.visit(node.get(1))}'

      # <expression> ::= <operand> <binary_operator> <operand>;
      case 1:
        return f'{visitor.visit(node.get(0))} {node.get(1).get(0).lexeme} {visitor.visit(node.get(2))}'

  def visit_operand(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.production:
      # <operand> ::= <variable>;
      case 0:
        return node.get(0).get(0).lexeme

      # <operand> ::= decimal_integer;
      case 1:
        return node.get(0).lexeme



class XBPrinter:
  tab = '  '

  def __init__(self, ast: Node):
    node_visitors: dict[str, Callable[[Node, Visitor], Any]] = {
      'b': self.visit_b,
      'block': self.visit_block,
      'statement': self.visit_statement,
      'expression': self.visit_expression,
      'operand': self.visit_operand,
      'unary_operator': self.visit_unary_operator,
      'binary_operator': self.visit_binary_operator,
      'variable': self.visit_variable,
      'string': self.visit_string,
    }
    self._tab_stop = 0
    self._str: str = Visitor(
      ast,
      node_visitors,
    ).ret

  @property
  def str(self) -> str:
    return self._str

  def visit_b(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    prog: str = '\n'.join(visitor.visit(child) for child in node.get(0))
    return prog

  def visit_block(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.production:
      # <block> ::= <statement>;
      case 0:
        return visitor.visit(node.get(0))

      # <block> ::= "{" <statements> "}";
      case 1:
        self._tab_stop += 1
        inner_prog: str = '\n'.join(visitor.visit(child) for child in node.get(0).get(1))
        self._tab_stop -= 1
        prog: str = '\n'.join(['{', inner_prog, f'{self._tab_stop * BPrinter.tab}}}'])
        return prog

  def visit_statement(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.production:
      case 0:
        return f'{self._tab_stop * BPrinter.tab}{visitor.visit(node[0][0])} = {visitor.visit(node[0][2])};'

      case 1:
        return f'{self._tab_stop * BPrinter.tab}{telescope(node[0][0]).lexeme}({visitor.visit(node[0][2])})'

      case 2:
        return f'{self._tab_stop * BPrinter.tab}while ({visitor.visit(node[0][2])}) {visitor.visit(node[0][4])}'

      case 3:
        return f'{self._tab_stop * BPrinter.tab}if ({visitor.visit(node[0][2])}) {visitor.visit(node[0][4])}'

  def visit_expression(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.production:
      # <expression> ::= <unary_operator> <operand>;
      case 0:
        return f'{visitor.visit(node[0])}{visitor.visit(node[0][1])}'

      # <expression> ::= <operand> <binary_operator> <operand>;
      case 1:
        return f'{visitor.visit(node[0][0])} {visitor.visit(node[0][1])} {visitor.visit(node[0][2])}'

  def visit_operand(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    return telescope(node).lexeme

  def visit_unary_operator(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    return telescope(node).lexeme

  def visit_binary_operator(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    return telescope(node).lexeme

  def visit_variable(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    return node[0].lexeme

  def visit_string(
    eslf,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    return node[0].lexeme



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
    visitor.visit(node.get(0))
    if node.production == 0:
      visitor.visit(node.get(1))

    return self._alloc

  def visit_block(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.production:
      # <block> ::= <statement>;
      case 0:
        return visitor.visit(node.get(0))

      # <block> ::= "{" <statements> "}";
      case 1:
        visitor.visit(node.get(1))

  def visit_statements(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    visitor.visit(node.get(0))
    if node.production == 0:
      visitor.visit(node.get(1))

  def visit_statement(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.production:
      # <statement> ::= <variable> "=" <operand> ";";
      # <statement> ::= <variable> "=" <expression> ";";
      case 0 | 1:
        varname: str = node.get(0).get(0).lexeme
        if varname not in self._alloc:
          self._alloc[varname] = self._next
          self._next += 1

      # <statement> ::= <variable> "=" <string> ";";
      case 2:
        varname: str = node.get(0).get(0).lexeme
        str_literal: str = node.get(2).get(0).literal
        if varname not in self._alloc:
          self._alloc[varname] = self._next
          self._next += len(str_literal) + 1

      # <statement> ::= "read" "\(" <variable> "\)" ";";
      case 5:
        varname: str = node.get(2).get(0).lexeme
        if varname not in self._alloc:
          self._alloc[varname] = self._next
          self._next += BAllocator.str_buffer_len + 1

      # <statement> ::= "readi" "\(" <variable> "\)" ";";
      case 6:
        varname: str = node.get(2).get(0).lexeme
        if varname not in self._alloc:
          self._alloc[varname] = self._next
          self._next += 1

  node_visitors = {
  }



# todo
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
    match node.production:
      # <b> ::= <block> <b>;
      case 0:
        a_ast_tail: Node = visitor.visit(node.get(1))
        a_ast: Node = visitor.visit(node.get(0))
        a_ast.add(a_ast_tail)

      # <b> ::= <block>;
      case 1:
        pass

  def visit_block(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.production:
      # <block> ::= <statement>;
      case 0:
        return visitor.visit(node.get(0))

      # <block> ::= "{" <statements> "}";
      case 1:
        self._tab_stop += 1
        prog: str = '\n'.join(['{', visitor.visit(node.get(1)), f'{(self._tab_stop - 1) * Bcompiler.tab}}}'])
        self._tab_stop -= 1
        return prog

  def visit_statements(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    prog: str = visitor.visit(node.get(0))
    if node.production == 0:
      prog = '\n'.join([prog, visitor.visit(node.get(1))])
    return prog

  def visit_statement(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.production:
      # <statement> ::= <variable> "=" <operand> ";";
      # <statement> ::= <variable> "=" <expression> ";";
      case 0 | 1:
        return f'{visitor.env["tab_stop"] * Bcompiler.tab}{node.get(0).get(0).lexeme} = {visitor.visit(node.get(2))};'

      # <statement> ::= <variable> "=" <string> ";";
      case 2:
        return f'{visitor.env["tab_stop"] * Bcompiler.tab}{node.get(0).get(0).lexeme} = {node.get(2).get(0).lexeme};'

      # <statement> ::= "print" "\(" <variable> "\)" ";";
      # <statement> ::= "printi" "\(" <variable> "\)" ";";
      # <statement> ::= "read" "\(" <variable> "\)" ";";
      # <statement> ::= "readi" "\(" <variable> "\)" ";";
      case 3 | 4 | 5 | 6:
        return f'{visitor.env["tab_stop"] * Bcompiler.tab}{node.get(0).lexeme}({telescope(node[2]).lexeme})'

      # <statement> ::= "while" "\(" <expression> "\)" <block>;
      # <statement> ::= "if" "\(" <expression> "\)" <block>;
      case 7 | 8:
        return f'{visitor.env["tab_stop"] * Bcompiler.tab}while ({visitor.visit(node.get(2))}) {visitor.visit(node.get(4))}'

  def visit_expression(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    match node.production:
      # <expression> ::= <unary_operator> <operand>;
      case 0:
        return f'{telescope(node[0]).lexeme}{visitor.visit(node.get(1))}'

      # <expression> ::= <operand> <binary_operator> <operand>;
      case 1:
        return f'{visitor.visit(node.get(0))} {telescpoe(node[1]).lexeme} {visitor.visit(node.get(2))}'

  def visit_operand(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    return telescope(node).lexeme
