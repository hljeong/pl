from __future__ import annotations
from enum import Enum

from ast import AVisitor

DEFAULT_MEM = 16 * 1024 * 1024

class Ins(Enum):
  ADD = 0
  ADDV = 1
  SUB = 2
  SUBV = 3
  MUL = 4
  MULV = 5
  OR = 6
  ORV = 7
  AND = 8
  ANDV = 9
  NOT = 10
  EQ = 11
  EQV = 12
  NEQ = 13
  NEQV = 14
  GT = 15
  GTV = 16
  GEQ = 17
  GEQV = 18
  LT = 19
  LTV = 20
  LEQ = 21
  LEQV = 22
  SET = 23
  SETV = 24
  JUMP = 25
  JUMPIF = 26
  PRINT = 27
  READ = 28
  LOAD = 29
  PRINTI = 30
  READI = 31
  JUMPV = 32
  JUMPVIF = 33

class AInterpreter(AVisitor):
  def __init__(self, root: A, mem: int = DEFAULT_MEM):
    self._root = root
    self._imem = []
    self._dmem = [0] * mem
    self._pc = 0
    self.__load()

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
      i = self.__get()
      match i.ins:
        case Ins.ADD:
          self._dmem[i.args.dst] = self._dmem[i.args.src1] + self._dmem[i.args.src2]
          self.__advance()
        case Ins.ADDV:
          self._dmem[i.args.dst] = self._dmem[i.args.src] + i.args.val
          self.__advance()
        case Ins.SUB:
          self._dmem[i.args.dst] = self._dmem[i.args.src1] - self._dmem[i.args.src2]
          self.__advance()
        case Ins.SUBV:
          self._dmem[i.args.dst] = self._dmem[i.args.src] - i.args.val
          self.__advance()
        case Ins.MUL:
          self._dmem[i.args.dst] = self._dmem[i.args.src1] * self._dmem[i.args.src2]
          self.__advance()
        case Ins.MULV:
          self._dmem[i.args.dst] = self._dmem[i.args.src] * i.args.val
          self.__advance()
        case Ins.OR:
          self._dmem[i.args.dst] = self._dmem[i.args.src1] | self._dmem[i.args.src2]
          self.__advance()
        case Ins.ORV:
          self._dmem[i.args.dst] = self._dmem[i.args.src] | i.args.val
          self.__advance()
        case Ins.AND:
          self._dmem[i.args.dst] = self._dmem[i.args.src1] & self._dmem[i.args.src2]
          self.__advance()
        case Ins.ANDV:
          self._dmem[i.args.dst] = self._dmem[i.args.src] & i.args.val
          self.__advance()
        case Ins.NOT:
          self._dmem[i.args.dst] = 1 if self._dmem[i.args.src] == 0 else 0
          self.__advance()
        case Ins.EQ:
          self._dmem[i.args.dst] = 1 if self._dmem[i.args.src1] == self._dmem[i.args.src2] else 0
          self.__advance()
        case Ins.EQV:
          self._dmem[i.args.dst] = 1 if self._dmem[i.args.src] == i.args.val else 0
          self.__advance()
        case Ins.NEQ:
          self._dmem[i.args.dst] = 1 if self._dmem[i.args.src1] != self._dmem[i.args.src2] else 0
          self.__advance()
        case Ins.NEQV:
          self._dmem[i.args.dst] = 1 if self._dmem[i.args.src] != i.args.val else 0
          self.__advance()
        case Ins.GT:
          self._dmem[i.args.dst] = 1 if self._dmem[i.args.src1] > self._dmem[i.args.src2] else 0
          self.__advance()
        case Ins.GTV:
          self._dmem[i.args.dst] = 1 if self._dmem[i.args.src] > i.args.val else 0
          self.__advance()
        case Ins.GEQ:
          self._dmem[i.args.dst] = 1 if self._dmem[i.args.src1] >= self._dmem[i.args.src2] else 0
          self.__advance()
        case Ins.GEQV:
          self._dmem[i.args.dst] = 1 if self._dmem[i.args.src] >= i.args.val else 0
          self.__advance()
        case Ins.LT:
          self._dmem[i.args.dst] = 1 if self._dmem[i.args.src1] < self._dmem[i.args.src2] else 0
          self.__advance()
        case Ins.LTV:
          self._dmem[i.args.dst] = 1 if self._dmem[i.args.src] < i.args.val else 0
          self.__advance()
        case Ins.LEQ:
          self._dmem[i.args.dst] = 1 if self._dmem[i.args.src1] <= self._dmem[i.args.src2] else 0
          self.__advance()
        case Ins.LEQV:
          self._dmem[i.args.dst] = 1 if self._dmem[i.args.src] <= i.args.val else 0
          self.__advance()
        case Ins.SET:
          self._dmem[i.args.dst] = self._dmem[i.args.src]
          self.__advance()
        case Ins.SETV:
          self._dmem[i.args.dst] = i.args.val
          self.__advance()
        case Ins.JUMP:
          self.__jump(self._dmem[i.args.src])
        case Ins.JUMPIF:
          if self._dmem[i.args.src1] != 0:
            self.__jump(self._dmem[i.args.src2])
          else:
            self.__advance()
        case Ins.PRINT:
          idx = self._dmem[i.args.src]
          while self._dmem[idx] != 0:
            print(chr(self._dmem[idx]), end='')
            idx += 1
          print()
          self.__advance()
        case Ins.READ:
          idx = self._dmem[i.args.src]
          read = input()
          for j in range(len(read)):
            self._dmem[idx + j] = ord(read[j])
          # 0-terminated
          self._dmem[idx + len(read)] = 0
          self.__advance()
        case Ins.LOAD:
          self._dmem[i.args.dst] = self._dmem[self._dmem[i.args.src]]
          self.__advance()
        case Ins.PRINTI:
          idx = self._dmem[i.args.src]
          print(self._dmem[idx])
          self.__advance()
        case Ins.READI:
          idx = self._dmem[i.args.src]
          self._dmem[idx] = int(input())
          self.__advance()
        case Ins.JUMPV:
          self.__jump(i.args.val)
        case Ins.JUMPVIF:
          if self._dmem[i.args.src] != 0:
            self.__jump(i.args.val)
          else:
            self.__advance()
          
      # print(i.ins.name)
      # print(self._dmem[:10])
      # input()

  def __load(self) -> None:
    self.visit_a(self._root)

  def visit_a(self, node: A):
    for instruction in node.instructions:
      instruction.accept(self)

  def visit_instruction(self, node: Instruction):
    self._imem.append(node)
    # node.instruction.accept(self)

  def visit_add_instruction(self, node: AddInstruction):
    self._imem.append(Ins.ADD)
    self._imem.append(node.dst)
    self._imem.append(node.src1)
    self._imem.append(node.src2)

  def visit_addv_instruction(self, node: AddvInstruction):
    self._imem.append(Ins.ADDV)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(node.val)

  def visit_sub_instruction(self, node: SubInstruction):
    self._imem.append(Ins.SUB)
    self._imem.append(node.dst)
    self._imem.append(node.src1)
    self._imem.append(node.src2)

  def visit_subv_instruction(self, node: SubvInstruction):
    self._imem.append(Ins.SUBV)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(node.val)

  def visit_mul_instruction(self, node: MulInstruction):
    self._imem.append(Ins.MUL)
    self._imem.append(node.dst)
    self._imem.append(node.src1)
    self._imem.append(node.src2)

  def visit_mulv_instruction(self, node: MulvInstruction):
    self._imem.append(Ins.MULV)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(node.val)

  def visit_or_instruction(self, node: OrInstruction):
    self._imem.append(Ins.OR)
    self._imem.append(node.dst)
    self._imem.append(node.src1)
    self._imem.append(node.src2)

  def visit_orv_instruction(self, node: OrvInstruction):
    self._imem.append(Ins.ORV)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(node.val)

  def visit_and_instruction(self, node: AndInstruction):
    self._imem.append(Ins.AND)
    self._imem.append(node.dst)
    self._imem.append(node.src1)
    self._imem.append(node.src2)

  def visit_andv_instruction(self, node: AndvInstruction):
    self._imem.append(Ins.ANDV)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(node.val)

  def visit_not_instruction(self, node: NotInstruction):
    self._imem.append(Ins.NOT)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(-1)

  def visit_eq_instruction(self, node: EqInstruction):
    self._imem.append(Ins.EQ)
    self._imem.append(node.dst)
    self._imem.append(node.src1)
    self._imem.append(node.src2)

  def visit_eqv_instruction(self, node: EqvInstruction):
    self._imem.append(Ins.EQV)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(node.val)

  def visit_neq_instruction(self, node: NeqInstruction):
    self._imem.append(Ins.NEQ)
    self._imem.append(node.dst)
    self._imem.append(node.src1)
    self._imem.append(node.src2)

  def visit_neqv_instruction(self, node: NeqvInstruction):
    self._imem.append(Ins.NEQV)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(node.val)

  def visit_gt_instruction(self, node: GtInstruction):
    self._imem.append(Ins.GT)
    self._imem.append(node.dst)
    self._imem.append(node.src1)
    self._imem.append(node.src2)

  def visit_gtv_instruction(self, node: GtvInstruction):
    self._imem.append(Ins.GTV)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(node.val)

  def visit_geq_instruction(self, node: GeqInstruction):
    self._imem.append(Ins.GEQ)
    self._imem.append(node.dst)
    self._imem.append(node.src1)
    self._imem.append(node.src2)

  def visit_geqv_instruction(self, node: GeqvInstruction):
    self._imem.append(Ins.GEQV)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(node.val)

  def visit_lt_instruction(self, node: LtInstruction):
    self._imem.append(Ins.LT)
    self._imem.append(node.dst)
    self._imem.append(node.src1)
    self._imem.append(node.src2)

  def visit_ltv_instruction(self, node: LtvInstruction):
    self._imem.append(Ins.LTV)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(node.val)

  def visit_leq_instruction(self, node: LeqInstruction):
    self._imem.append(Ins.LEQ)
    self._imem.append(node.dst)
    self._imem.append(node.src1)
    self._imem.append(node.src2)

  def visit_leqv_instruction(self, node: LeqvInstruction):
    self._imem.append(Ins.LEQV)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(node.val)

  def visit_set_instruction(self, node: SetInstruction):
    self._imem.append(Ins.SET)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(-1)

  def visit_setv_instruction(self, node: SetvInstruction):
    self._imem.append(Ins.SETV)
    self._imem.append(node.dst)
    self._imem.append(node.val)
    self._imem.append(-1)

  def visit_jump_instruction(self, node: JumpInstruction):
    self._imem.append(Ins.JUMP)
    self._imem.append(node.src)
    self._imem.append(-1)
    self._imem.append(-1)

  def visit_jumpif_instruction(self, node: JumpifInstruction):
    self._imem.append(Ins.JUMPIF)
    self._imem.append(node.src1)
    self._imem.append(node.src2)
    self._imem.append(-1)

  def visit_print_instruction(self, node: PrintInstruction):
    self._imem.append(Ins.PRINT)
    self._imem.append(node.src)
    self._imem.append(-1)
    self._imem.append(-1)

  def visit_read_instruction(self, node: ReadInstruction):
    self._imem.append(Ins.READ)
    self._imem.append(node.src)
    self._imem.append(-1)
    self._imem.append(-1)

  def visit_load_instruction(self, node: Loadnstruction):
    self._imem.append(Ins.LOAD)
    self._imem.append(node.dst)
    self._imem.append(node.src)
    self._imem.append(-1)

  def visit_printi_instruction(self, node: PrintiInstruction):
    self._imem.append(Ins.PRINTI)
    self._imem.append(node.src)
    self._imem.append(-1)
    self._imem.append(-1)

  def visit_readi_instruction(self, node: ReadiInstruction):
    self._imem.append(Ins.READI)
    self._imem.append(node.src)
    self._imem.append(-1)
    self._imem.append(-1)

  def visit_jumpv_instruction(self, node: JumpvInstruction):
    self._imem.append(Ins.JUMPV)
    self._imem.append(node.val)
    self._imem.append(-1)
    self._imem.append(-1)

  def visit_jumpvif_instruction(self, node: JumpvifInstruction):
    self._imem.append(Ins.JUMPVIF)
    self._imem.append(node.src)
    self._imem.append(node.val)
    self._imem.append(-1)
