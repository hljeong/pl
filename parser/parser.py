from __future__ import annotations
from typing import TypeVar

from common import Cursor, CursorRange, Token
from ast import ANode, AVisitor
from .visitor import Ins

class Parser:
  class A(ANode):
    def __init__(self, instructions: list[Instruction]):
      self.instructions = instructions

    def accept(self, visitor: AVisitor):
      visitor.visit_a(self)

  class Instruction(ANode):
    def __init__(self, ins: Ins, args: Instruction):
      self.ins = ins
      self.args = args

    def accept(self, visitor: AVisitor):
      visitor.visit_instruction(self)

  class AddInstruction(Instruction):
    def __init__(self, dst: Token, src1: Token, src2: Token):
      self.dst: int = dst.literal
      self.src1: int = src1.literal
      self.src2: int = src2.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_add_instruction(self)

  class AddvInstruction(Instruction):
    def __init__(self, dst: Token, src: Token, val: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_addv_instruction(self)

  class SubInstruction(Instruction):
    def __init__(self, dst: Token, src1: Token, src2: Token):
      self.dst: int = dst.literal
      self.src1: int = src1.literal
      self.src2: int = src2.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_sub_instruction(self)

  class SubvInstruction(Instruction):
    def __init__(self, dst: Token, src: Token, val: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_subv_instruction(self)

  class MulInstruction(Instruction):
    def __init__(self, dst: Token, src1: Token, src2: Token):
      self.dst: int = dst.literal
      self.src1: int = src1.literal
      self.src2: int = src2.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_mul_instruction(self)

  class MulvInstruction(Instruction):
    def __init__(self, dst: Token, src: Token, val: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_mulv_instruction(self)

  class OrInstruction(Instruction):
    def __init__(self, dst: Token, src1: Token, src2: Token):
      self.dst: int = dst.literal
      self.src1: int = src1.literal
      self.src2: int = src2.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_or_instruction(self)

  class OrvInstruction(Instruction):
    def __init__(self, dst: Token, src: Token, val: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_orv_instruction(self)

  class AndInstruction(Instruction):
    def __init__(self, dst: Token, src1: Token, src2: Token):
      self.dst: int = dst.literal
      self.src1: int = src1.literal
      self.src2: int = src2.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_and_instruction(self)

  class AndvInstruction(Instruction):
    def __init__(self, dst: Token, src: Token, val: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_andv_instruction(self)

  class NotInstruction(Instruction):
    def __init__(self, dst: Token, src: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_not_instruction(self)

  class EqInstruction(Instruction):
    def __init__(self, dst: Token, src1: Token, src2: Token):
      self.dst: int = dst.literal
      self.src1: int = src1.literal
      self.src2: int = src2.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_eq_instruction(self)

  class EqvInstruction(Instruction):
    def __init__(self, dst: Token, src: Token, val: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_eqv_instruction(self)

  class NeqInstruction(Instruction):
    def __init__(self, dst: Token, src1: Token, src2: Token):
      self.dst: int = dst.literal
      self.src1: int = src1.literal
      self.src2: int = src2.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_neq_instruction(self)

  class NeqvInstruction(Instruction):
    def __init__(self, dst: Token, src: Token, val: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_neqv_instruction(self)

  class GtInstruction(Instruction):
    def __init__(self, dst: Token, src1: Token, src2: Token):
      self.dst: int = dst.literal
      self.src1: int = src1.literal
      self.src2: int = src2.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_gt_instruction(self)

  class GtvInstruction(Instruction):
    def __init__(self, dst: Token, src: Token, val: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_gtv_instruction(self)

  class GeqInstruction(Instruction):
    def __init__(self, dst: Token, src1: Token, src2: Token):
      self.dst: int = dst.literal
      self.src1: int = src1.literal
      self.src2: int = src2.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_geq_instruction(self)

  class GeqvInstruction(Instruction):
    def __init__(self, dst: Token, src: Token, val: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_geqv_instruction(self)

  class LtInstruction(Instruction):
    def __init__(self, dst: Token, src1: Token, src2: Token):
      self.dst: int = dst.literal
      self.src1: int = src1.literal
      self.src2: int = src2.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_lt_instruction(self)

  class LtvInstruction(Instruction):
    def __init__(self, dst: Token, src: Token, val: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_ltv_instruction(self)

  class LeqInstruction(Instruction):
    def __init__(self, dst: Token, src1: Token, src2: Token):
      self.dst: int = dst.literal
      self.src1: int = src1.literal
      self.src2: int = src2.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_leq_instruction(self)

  class LeqvInstruction(Instruction):
    def __init__(self, dst: Token, src: Token, val: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_leqv_instruction(self)

  class SetInstruction(Instruction):
    def __init__(self, dst: Token, src: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_set_instruction(self)

  class SetvInstruction(Instruction):
    def __init__(self, dst: Token, val: Token):
      self.dst: int = dst.literal
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_setv_instruction(self)

  class JumpInstruction(Instruction):
    def __init__(self, src: Token):
      self.src: int = src.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_jump_instruction(self)

  class JumpifInstruction(Instruction):
    def __init__(self, src1: Token, src2: Token):
      self.src1: int = src1.literal
      self.src2: int = src2.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_jumpif_instruction(self)

  class PrintInstruction(Instruction):
    def __init__(self, src: Token):
      self.src: int = src.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_print_instruction(self)

  class ReadInstruction(Instruction):
    def __init__(self, src: Token):
      self.src: int = src.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_read_instruction(self)

  class LoadInstruction(Instruction):
    def __init__(self, dst: Token, src: Token):
      self.dst: int = dst.literal
      self.src: int = src.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_read_instruction(self)

  class PrintiInstruction(Instruction):
    def __init__(self, src: Token):
      self.src: int = src.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_printi_instruction(self)

  class ReadiInstruction(Instruction):
    def __init__(self, src: Token):
      self.src: int = src.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_readi_instruction(self)

  class JumpvInstruction(Instruction):
    def __init__(self, val: Token):
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_jumpv_instruction(self)

  class JumpvifInstruction(Instruction):
    def __init__(self, src: Token, val: Token):
      self.src: int = src.literal
      self.val: int = val.literal

    def accept(self, visitor: AVisitor):
      visitor.visit_jumpvif_instruction(self)


  def __init__(
    self,
    tokens: list[Token],
  ):
    self._tokens = tokens
    self._current = 0
    self._root = self.__parse_a()

  def __at_end(self) -> bool:
    return self._current >= len(self._tokens)

  def __peek(self) -> Token:
    return self._tokens[self._current]

  def __expect(self, token_type: Token.Type) -> Token:
    token = self.__peek()
    if token.token_type != token_type:
      raise ValueError(f'expected token type {token_type.name}, found {token.token_type} at {token.position.to_string(True)}')
    self._current += 1
    return token
  
  def __parse_a(self) -> A:
    instructions = []
    while not self.__at_end():
      instructions.append(self.__parse_instruction())
    return self.A(instructions)

  def __parse_instruction(self) -> Instruction:
    instruction = self.__expect(Token.Type.IDENTIFIER)
    match instruction.literal:
      case 'add':
        return self.Instruction(Ins.ADD, self.__parse_add_instruction())
      case 'addv':
        return self.Instruction(Ins.ADDV, self.__parse_addv_instruction())
      case 'sub':
        return self.Instruction(Ins.SUB, self.__parse_sub_instruction())
      case 'subv':
        return self.Instruction(Ins.SUBV, self.__parse_subv_instruction())
      case 'mul':
        return self.Instruction(Ins.MUL, self.__parse_mul_instruction())
      case 'mulv':
        return self.Instruction(Ins.MULV, self.__parse_mulv_instruction())
      case 'or':
        return self.Instruction(Ins.OR, self.__parse_or_instruction())
      case 'orv':
        return self.Instruction(Ins.ORV, self.__parse_orv_instruction())
      case 'and':
        return self.Instruction(Ins.AND, self.__parse_and_instruction())
      case 'andv':
        return self.Instruction(Ins.ANDV, self.__parse_andv_instruction())
      case 'not':
        return self.Instruction(Ins.NOT, self.__parse_not_instruction())
      case 'eq':
        return self.Instruction(Ins.EQ, self.__parse_eq_instruction())
      case 'eqv':
        return self.Instruction(Ins.EQV, self.__parse_eqv_instruction())
      case 'neq':
        return self.Instruction(Ins.NEQ, self.__parse_neq_instruction())
      case 'neqv':
        return self.Instruction(Ins.NEQV, self.__parse_neqv_instruction())
      case 'gt':
        return self.Instruction(Ins.GT, self.__parse_gt_instruction())
      case 'gtv':
        return self.Instruction(Ins.GTV, self.__parse_gtv_instruction())
      case 'geq':
        return self.Instruction(Ins.GEQ, self.__parse_geq_instruction())
      case 'geqv':
        return self.Instruction(Ins.GEQV, self.__parse_geqv_instruction())
      case 'lt':
        return self.Instruction(Ins.LT, self.__parse_lt_instruction())
      case 'ltv':
        return self.Instruction(Ins.LTV, self.__parse_ltv_instruction())
      case 'leq':
        return self.Instruction(Ins.LEQ, self.__parse_leq_instruction())
      case 'leqv':
        return self.Instruction(Ins.LEQV, self.__parse_leqv_instruction())
      case 'set':
        return self.Instruction(Ins.SET, self.__parse_set_instruction())
      case 'setv':
        return self.Instruction(Ins.SETV, self.__parse_setv_instruction())
      case 'jump':
        return self.Instruction(Ins.JUMP, self.__parse_jump_instruction())
      case 'jumpif':
        return self.Instruction(Ins.JUMPIF, self.__parse_jumpif_instruction())
      case 'print':
        return self.Instruction(Ins.PRINT, self.__parse_print_instruction())
      case 'read':
        return self.Instruction(Ins.READ, self.__parse_read_instruction())
      case 'load':
        return self.Instruction(Ins.LOAD, self.__parse_load_instruction())
      case 'printi':
        return self.Instruction(Ins.PRINTI, self.__parse_printi_instruction())
      case 'readi':
        return self.Instruction(Ins.READI, self.__parse_readi_instruction())
      case 'jumpv':
        return self.Instruction(Ins.JUMPV, self.__parse_jumpv_instruction())
      case 'jumpvif':
        return self.Instruction(Ins.JUMPVIF, self.__parse_jumpvif_instruction())
      case _:
        raise ValueError(f'invalid instruction ({instruction.literal}) at {instruction.position.to_string(True)}')

  def __parse_add_instruction(self) -> AddInstruction:
    return self.AddInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )
    
  def __parse_addv_instruction(self) -> AddvInstruction:
    return self.AddvInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_sub_instruction(self) -> SubInstruction:
    return self.SubInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_subv_instruction(self) -> SubvInstruction:
    return self.SubvInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_mul_instruction(self) -> MulInstruction:
    return self.MulInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_mulv_instruction(self) -> MulvInstruction:
    return self.MulvInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_or_instruction(self) -> OrInstruction:
    return self.OrInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_orv_instruction(self) -> OrvInstruction:
    return self.OrvInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_and_instruction(self) -> AndInstruction:
    return self.AndInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_andv_instruction(self) -> AndvInstruction:
    return self.AndvInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_not_instruction(self) -> NotInstruction:
    return self.NotInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_eq_instruction(self) -> EqInstruction:
    return self.EqInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_eqv_instruction(self) -> EqvInstruction:
    return self.EqvInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_neq_instruction(self) -> NeqInstruction:
    return self.NeqInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_neqv_instruction(self) -> NeqvInstruction:
    return self.NeqvInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_gt_instruction(self) -> GtInstruction:
    return self.GtInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_gtv_instruction(self) -> GtvInstruction:
    return self.GtvInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_geq_instruction(self) -> GeqInstruction:
    return self.GeqInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_geqv_instruction(self) -> GeqvInstruction:
    return self.GeqvInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_lt_instruction(self) -> LtInstruction:
    return self.LtInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_ltv_instruction(self) -> LtvInstruction:
    return self.LtvInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_leq_instruction(self) -> LeqInstruction:
    return self.LeqInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_leqv_instruction(self) -> LeqvInstruction:
    return self.LeqvInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_set_instruction(self) -> SetInstruction:
    return self.SetInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_setv_instruction(self) -> SetvInstruction:
    return self.SetvInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_jump_instruction(self) -> JumpInstruction:
    return self.JumpInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_jumpif_instruction(self) -> JumpifInstruction:
    return self.JumpifInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_print_instruction(self) -> PrintInstruction:
    return self.PrintInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_read_instruction(self) -> ReadInstruction:
    return self.ReadInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_load_instruction(self) -> LoadInstruction:
    return self.LoadInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_printi_instruction(self) -> PrintiInstruction:
    return self.PrintiInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_readi_instruction(self) -> ReadiInstruction:
    return self.ReadiInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_jumpv_instruction(self) -> JumpvInstruction:
    return self.JumpvInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  def __parse_jumpvif_instruction(self) -> JumpvifInstruction:
    return self.JumpvifInstruction(
      self.__expect(Token.Type.DECIMAL_INTEGER),
      self.__expect(Token.Type.DECIMAL_INTEGER),
    )

  @property
  def root(self) -> A:
    return self._root
