from __future__ import annotations
from typing import Any

from common import Monad, Log
from lexical import Lexer
from syntax import Grammar, Parser, Visitor, ASTNode

DEFAULT_MEM = 16 * 1024 * 1024

with open('langs/a/spec/a.xbnf') as a_xbnf_f:
  a_xbnf = ''.join(a_xbnf_f.readlines())

# todo: gotta define comments somewhere else... this is ugly
a_grammar = Grammar('a', a_xbnf, ignore=[r'#[^\n]*'])

class AParser:
  def parse(self, prog: str):
    return Monad(prog) \
      .then(Lexer(a_grammar).lex) \
      .then(Parser(a_grammar).parse) \
      .value



class APrinter(Visitor):
  def __init__(self):
    super().__init__(
      {
        '<a>': self._visit_a,
        '<instruction>': self._visit_instruction,
      },
      default_nonterminal_node_visitor=Visitor.visit_telescope,
      default_terminal_node_visitor=lambda terminal_node, _: terminal_node.lexeme,
    )

  def print(self, ast: ASTNode) -> str:
    return self.visit(ast)

  def _visit_a(
    self,
    node: ASTNode,
    visitor: Visitor,
  ):
    prog: str = '\n'.join(visitor.visit(child) for child in node[0])
    return prog

  def _visit_instruction(
    self,
    node: ASTNode,
    visitor: Visitor
  ) -> str:
    return ' '.join(visitor.visit(child) for child in node)

class AInterpreter:
  def __init__(self, mem_size: int = DEFAULT_MEM):
    self._mem_size = mem_size
    self._imem = []
    self._dmem = [0] * self._mem_size
    self._pc = 0

  def __at_end(self) -> bool:
    return self._pc >= len(self._imem)

  def __get(self) -> Instruction:
    return self._imem[self._pc]

  def __jump(self, line: int) -> None:
    self._pc = line

  def __advance(self) -> None:
    self._pc += 1

  def interpret(self, ast: ASTNode) -> None:
    self._imem = ALoader().load(ast)
    self._dmem = [0] * self._mem_size
    self._pc = 0

    while not self.__at_end():
      ins: tuple = self.__get()
      advance: bool = True
      match ins[0]:
        case 'add':
          self._dmem[ins[1]] = self._dmem[ins[2]] + self._dmem[ins[3]]

        case 'sub':
          self._dmem[ins[1]] = self._dmem[ins[2]] - self._dmem[ins[3]]

        case 'mul':
          self._dmem[ins[1]] = self._dmem[ins[2]] * self._dmem[ins[3]]

        case 'or':
          self._dmem[ins[1]] = self._dmem[ins[2]] | self._dmem[ins[3]]

        case 'and':
          self._dmem[ins[1]] = self._dmem[ins[2]] & self._dmem[ins[3]]

        case 'not':
          self._dmem[ins[1]] = 1 if self._dmem[ins[2]] == 0 else 0

        case 'eq':
          self._dmem[ins[1]] = 1 if self._dmem[ins[2]] == self._dmem[ins[3]] else 0

        case 'neq':
          self._dmem[ins[1]] = 1 if self._dmem[ins[2]] != self._dmem[ins[3]] else 0

        case 'gt':
          self._dmem[ins[1]] = 1 if self._dmem[ins[2]] > self._dmem[ins[3]] else 0

        case 'geq':
          self._dmem[ins[1]] = 1 if self._dmem[ins[2]] >= self._dmem[ins[3]] else 0

        case 'lt':
          self._dmem[ins[1]] = 1 if self._dmem[ins[2]] < self._dmem[ins[3]] else 0

        case 'leq':
          self._dmem[ins[1]] = 1 if self._dmem[ins[2]] <= self._dmem[ins[3]] else 0

        case 'set':
          self._dmem[ins[1]] = self._dmem[ins[2]]

        case 'jump':
          self.__jump(self._dmem[ins[1]])
          advance = False

        case 'jumpif':
          if self._dmem[ins[2]] != 0:
            self.__jump(self._dmem[ins[1]])
            advance = False

        case 'addv':
          self._dmem[ins[1]] = self._dmem[ins[2]] + ins[3]

        case 'subv':
          self._dmem[ins[1]] = self._dmem[ins[2]] - ins[3]

        case 'mulv':
          self._dmem[ins[1]] = self._dmem[ins[2]] * ins[3]

        case 'orv':
          self._dmem[ins[1]] = self._dmem[ins[2]] | ins[3]

        case 'andv':
          self._dmem[ins[1]] = self._dmem[ins[2]] & ins[3]

        case 'eqv':
          self._dmem[ins[1]] = 1 if self._dmem[ins[2]] == ins[3] else 0

        case 'neqv':
          self._dmem[ins[1]] = 1 if self._dmem[ins[2]] != ins[3] else 0

        case 'gtv':
          self._dmem[ins[1]] = 1 if self._dmem[ins[2]] > ins[3] else 0

        case 'geqv':
          self._dmem[ins[1]] = 1 if self._dmem[ins[2]] >= ins[3] else 0

        case 'ltv':
          self._dmem[ins[1]] = 1 if self._dmem[ins[2]] < ins[3] else 0

        case 'leqv':
          self._dmem[ins[1]] = 1 if self._dmem[ins[2]] <= ins[3] else 0

        case 'setv':
          self._dmem[ins[1]] = ins[2]

        case 'jumpv':
          self.__jump(ins[1])
          advance = False

        case 'jumpvif':
          if self._dmem[ins[2]] != 0:
            self.__jump(ins[1])
            advance = False

        case 'print':
          idx = self._dmem[ins[1]]
          while self._dmem[idx] != 0:
            print(chr(self._dmem[idx]), end='')
            idx += 1
          print()

        case 'printi':
          print(self._dmem[self._dmem[ins[1]]])

        case 'read':
          idx = self._dmem[ins[1]]
          read = input()
          for i in range(len(read)):
            self._dmem[idx + i] = ord(read[i])

          # 0-terminated
          self._dmem[idx + len(read)] = 0

        case 'readi':
          self._dmem[self._dmem[ins[1]]] = int(input())

        case 'load':
          self._dmem[ins[1]] = self._dmem[self._dmem[ins[2]]]

      if advance:
        self.__advance()



class ALoader(Visitor):
  def __init__(self):
    super().__init__(
      {
        '<a>': self._visit_a,
        '<instruction>': self._visit_instruction,
      },
      default_nonterminal_node_visitor=Visitor.visit_telescope,
      default_terminal_node_visitor=lambda terminal_node, _: terminal_node.literal,
    )

  def load(self, ast: ASTNode) -> list[tuple]:
    return self.visit(ast)

  def _visit_a(
    self,
    node: ASTNode,
    visitor: Visitor,
  ) -> Any:
    return [visitor.visit(child) for child in node[0]]

  def _visit_instruction(
    self,
    node: ASTNode,
    visitor: Visitor,
  ) -> Any:
    return tuple(visitor.visit(child) for child in node)
