from __future__ import annotations
from abc import ABC, abstractmethod

class ANode(ABC):
  @abstractmethod
  def accept(self, visitor: AVisitor) -> None:
    pass

class AVisitor(ABC):
  @abstractmethod
  def visit_a(self, node: A):
    pass

  @abstractmethod
  def visit_instruction(self, node: Instruction):
    pass

  @abstractmethod
  def visit_add_instruction(self, node: AddInstruction):
    pass

  @abstractmethod
  def visit_addv_instruction(self, node: AddvInstruction):
    pass

  @abstractmethod
  def visit_sub_instruction(self, node: SubInstruction):
    pass

  @abstractmethod
  def visit_subv_instruction(self, node: SubvInstruction):
    pass

  @abstractmethod
  def visit_mul_instruction(self, node: MulInstruction):
    pass

  @abstractmethod
  def visit_mulv_instruction(self, node: MulvInstruction):
    pass

  @abstractmethod
  def visit_or_instruction(self, node: OrInstruction):
    pass

  @abstractmethod
  def visit_orv_instruction(self, node: OrvInstruction):
    pass

  @abstractmethod
  def visit_and_instruction(self, node: AndInstruction):
    pass

  @abstractmethod
  def visit_andv_instruction(self, node: AndvInstruction):
    pass

  @abstractmethod
  def visit_not_instruction(self, node: NotInstruction):
    pass

  @abstractmethod
  def visit_eq_instruction(self, node: EqInstruction):
    pass

  @abstractmethod
  def visit_eqv_instruction(self, node: EqvInstruction):
    pass

  @abstractmethod
  def visit_neq_instruction(self, node: NeqInstruction):
    pass

  @abstractmethod
  def visit_neqv_instruction(self, node: NeqvInstruction):
    pass

  @abstractmethod
  def visit_gt_instruction(self, node: GtInstruction):
    pass

  @abstractmethod
  def visit_gtv_instruction(self, node: GtvInstruction):
    pass

  @abstractmethod
  def visit_geq_instruction(self, node: GeqInstruction):
    pass

  @abstractmethod
  def visit_geqv_instruction(self, node: GeqvInstruction):
    pass

  @abstractmethod
  def visit_lt_instruction(self, node: LtInstruction):
    pass

  @abstractmethod
  def visit_ltv_instruction(self, node: LtvInstruction):
    pass

  @abstractmethod
  def visit_leq_instruction(self, node: LeqInstruction):
    pass

  @abstractmethod
  def visit_leqv_instruction(self, node: LeqvInstruction):
    pass

  @abstractmethod
  def visit_set_instruction(self, node: SetInstruction):
    pass

  @abstractmethod
  def visit_setv_instruction(self, node: SetvInstruction):
    pass

  @abstractmethod
  def visit_jump_instruction(self, node: JumpInstruction):
    pass

  @abstractmethod
  def visit_jumpif_instruction(self, node: JumpifInstruction):
    pass

  @abstractmethod
  def visit_print_instruction(self, node: PrintInstruction):
    pass

  @abstractmethod
  def visit_read_instruction(self, node: ReadInstruction):
    pass

  @abstractmethod
  def visit_load_instruction(self, node: LoadInstruction):
    pass

  @abstractmethod
  def visit_printi_instruction(self, node: PrintiInstruction):
    pass

  @abstractmethod
  def visit_readi_instruction(self, node: ReadiInstruction):
    pass

  @abstractmethod
  def visit_jumpv_instruction(self, node: JumpvInstruction):
    pass

  @abstractmethod
  def visit_jumpvif_instruction(self, node: JumpvifInstruction):
    pass
