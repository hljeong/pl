from __future__ import annotations

from lexer import Lexer
from grammar import Grammar
from ast import Parser, Visitor

DEFAULT_MEM = 16 * 1024 * 1024

with open('langs/a/spec/a.cbnf') as a_cbnf_f:
  a_cbnf = ''.join(a_cbnf_f.readlines())
a_grammar = Grammar(a_cbnf)

class AInterpreter:
  def __init__(self, prog: str, mem: int = DEFAULT_MEM):
    self._ast: Node = Parser(a_grammar, Lexer(prog).tokens).ast
    self._imem = Visitor(self._ast, a_loader_node_visitors).ret
    self._dmem = [0] * mem
    self._pc = 0

  def __at_end(self) -> bool:
    return self._pc >= len(self._imem)

  def __get(self) -> Instruction:
    return self._imem[self._pc]

  def __jump(self, line: int) -> None:
    self._pc = line

  def __advance(self) -> None:
    self._pc += 1

  def interpret(self) -> None:
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



def a_loader_visit_a(
  node: Node,
  visitor: Visitor,
) -> Any:
  instructions = [visitor.visit(node.get(0))]
  if node.production == 0:
    instructions.extend(visitor.visit(node.get(1)))
  return instructions

def a_loader_visit_instruction(
  node: Node,
  visitor: Visitor,
) -> Any:
  match node.production:
    # 3 operands
    case 0:
      return (
        node.get(0).get(0).literal,
        node.get(1).get(0).literal,
        node.get(2).get(0).literal,
        node.get(3).get(0).literal,
      )

    # 2 operands
    case 1:
      return (
        node.get(0).get(0).literal,
        node.get(1).get(0).literal,
        node.get(2).get(0).literal,
      )

    # 1 operand
    case 2:
      return (
        node.get(0).get(0).literal,
        node.get(1).get(0).literal,
      )

a_loader_node_visitors = {
  'a': a_loader_visit_a,
  'instruction': a_loader_visit_instruction,
}
