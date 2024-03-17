from __future__ import annotations
from abc import ABC, abstractmethod
import typing

class A:
  def __init__(self, instructions: list[Instruction]):
    self.instructions = []

class Instruction:
  pass

class AddInstruction(Instruction):
  def __init__(self, dst: Reg, src1: Reg, src2: Reg):
    self.dst = dst
    self.src1 = src1
    self.src2 = src2

class AddvInstruction(Instruction):
  def __init__(self, dst: Reg, src: Reg, val: Val):
    self.dst = dst
    self.src = src
    self.val = val

class SubInstruction(Instruction):
  def __init__(self, dst: Reg, src1: Reg, src2: Reg):
    self.dst = dst
    self.src1 = src1
    self.src2 = src2

class SubvInstruction(Instruction):
  def __init__(self, dst: Reg, src: Reg, val: Val):
    self.dst = dst
    self.src = src
    self.val = val

class MulInstruction(Instruction):
  def __init__(self, dst: Reg, src1: Reg, src2: Reg):
    self.dst = dst
    self.src1 = src1
    self.src2 = src2

class MulvInstruction(Instruction):
  def __init__(self, dst: Reg, src: Reg, val: Val):
    self.dst = dst
    self.src = src
    self.val = val

class OrInstruction(Instruction):
  def __init__(self, dst: Reg, src1: Reg, src2: Reg):
    self.dst = dst
    self.src1 = src1
    self.src2 = src2

class OrvInstruction(Instruction):
  def __init__(self, dst: Reg, src: Reg, val: Val):
    self.dst = dst
    self.src = src
    self.val = val

class AndInstruction(Instruction):
  def __init__(self, dst: Reg, src1: Reg, src2: Reg):
    self.dst = dst
    self.src1 = src1
    self.src2 = src2

class AndvInstruction(Instruction):
  def __init__(self, dst: Reg, src: Reg, val: Val):
    self.dst = dst
    self.src = src
    self.val = val

class NotInstruction(Instruction):
  def __init__(self, dst: Reg, src: Reg):
    self.dst = dst
    self.src = src

class EqInstruction(Instruction):
  def __init__(self, dst: Reg, src1: Reg, src2: Reg):
    self.dst = dst
    self.src1 = src1
    self.src2 = src2

class EqvInstruction(Instruction):
  def __init__(self, dst: Reg, src: Reg, val: Val):
    self.dst = dst
    self.src = src
    self.val = val

class NeqInstruction(Instruction):
  def __init__(self, dst: Reg, src1: Reg, src2: Reg):
    self.dst = dst
    self.src1 = src1
    self.src2 = src2

class NeqvInstruction(Instruction):
  def __init__(self, dst: Reg, src: Reg, val: Val):
    self.dst = dst
    self.src = src
    self.val = val

class GtInstruction(Instruction):
  def __init__(self, dst: Reg, src1: Reg, src2: Reg):
    self.dst = dst
    self.src1 = src1
    self.src2 = src2

class GtvInstruction(Instruction):
  def __init__(self, dst: Reg, src: Reg, val: Val):
    self.dst = dst
    self.src = src
    self.val = val

class GeqInstruction(Instruction):
  def __init__(self, dst: Reg, src1: Reg, src2: Reg):
    self.dst = dst
    self.src1 = src1
    self.src2 = src2

class GeqvInstruction(Instruction):
  def __init__(self, dst: Reg, src: Reg, val: Val):
    self.dst = dst
    self.src = src
    self.val = val

class LtInstruction(Instruction):
  def __init__(self, dst: Reg, src1: Reg, src2: Reg):
    self.dst = dst
    self.src1 = src1
    self.src2 = src2

class LtvInstruction(Instruction):
  def __init__(self, dst: Reg, src: Reg, val: Val):
    self.dst = dst
    self.src = src
    self.val = val

class LeqInstruction(Instruction):
  def __init__(self, dst: Reg, src1: Reg, src2: Reg):
    self.dst = dst
    self.src1 = src1
    self.src2 = src2

class LeqvInstruction(Instruction):
  def __init__(self, dst: Reg, src: Reg, val: Val):
    self.dst = dst
    self.src = src
    self.val = val

class SetInstruction(Instruction):
  def __init__(self, dst: Reg, src: Reg):
    self.dst = dst
    self.src = src

class SetvInstruction(Instruction):
  def __init__(self, dst: Reg, val: Val):
    self.dst = dst
    self.val = val

class JumpInstruction(Instruction):
  def __init__(self, loc: Val):
    self.loc = loc

class JumpIfInstruction(Instruction):
  def __init__(self, src: Reg, loc: Val):
    self.src = src
    self.loc = loc

class PrintInstruction(Instruction):
  def __init__(self, src: Reg):
    self.src = src

class ReadInstruction(Instruction):
  def __init__(self, dst: Reg):
    self.dst = dst
