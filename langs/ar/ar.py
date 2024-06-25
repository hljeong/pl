from __future__ import annotations
from typing import Callable

from common import Log

# reorganize stuff not immediately concerning ar
RegFile = dict[str, int]
Memory = list[int]
SysCall = Callable[[], None]


DEFAULT_REGFILE_SIZE: int = 32
DEFAULT_MEM_SIZE: int = 2 * 1024 * 1024
DEFAULT_STACK_SIZE: int = 16 * 1024
USE_DEFAULT_SYSCALL: dict[int, SysCall] = {}


class Machine:
    def __init__(
        self,
        regfile_size: int = DEFAULT_REGFILE_SIZE,
        mem_size: int = DEFAULT_MEM_SIZE,
        stack_size: int = DEFAULT_STACK_SIZE,
        syscall: dict[int, SysCall] = USE_DEFAULT_SYSCALL,
    ):
        self._r: RegFile = {f"r{i}": 0 for i in range(regfile_size)}
        self._m: Memory = [0] * mem_size
        if syscall is USE_DEFAULT_SYSCALL:
            syscall = {
                0: self._print,
                1: self._read,
                2: self._stoi,
                3: self._printi,
                4: self._alloc,
                5: self._free,
            }
        self._syscall = syscall
        self._pc: int = 0
        self._next_pc: int = 1
        # skip nullptr
        self._r["r1"] = 1
        self._stack_limit: int = stack_size
        self._next_mem_alloc: int = mem_size

    def _print(self) -> None:
        i: int = self._r["r14"]
        while i < len(self._m) and self._m[i] != 0:
            print(chr(self._m[i]), end="")
            i += 1

        if i == len(self._m) and self._m[-1] != 0:
            # error -> return 1
            self._r["r14"] = 1
            return

        print()
        # success -> return 0
        self._r["r14"] = 0

    def _read(self) -> None:
        i: int = self._r["r14"]
        read = input()
        for j in range(len(read)):
            if i + j >= len(self._m):
                # error -> return 1
                self._r["r14"] = 1
                return

            self._m[i + j] = ord(read[j])

        if i + len(read) >= len(self._m):
            # error -> return 1
            self._r["r14"] = 1
            return

        # 0-terminate
        self._m[i + len(read)] = 0

        # success -> return 0
        self._r["r14"] = 0

    def _stoi(self) -> None:
        i: int = self._r["r14"]
        int_str: str = ""
        while i < len(self._m) and self._m[i] != 0:
            int_str += chr(self._m[i])
            i += 1

        if i == len(self._m) and self._m[-1] != 0:
            # error -> return 1
            self._r["r14"] = 1
            return

        # success -> return 0 and int value
        self._r["r14"] = 0
        self._r["r15"] = int(int_str)

    def _printi(self) -> None:
        print(self._r["r14"])

        # success -> return 0
        self._r["r14"] = 0

    # todo: need to put string constants somewhere else so it doesnt fight w dynamic allocation
    # todo: better allocator
    def _alloc(self) -> None:
        size: int = self._r["r14"]
        self._r["r14"] = self._next_mem_alloc - size
        self._next_mem_alloc -= size

    # no op for now
    # todo: better allocator
    def _free(self) -> None:
        self._r["r14"] = 0

    # todo: implement imem and keep pc internal
    def clk(self) -> int:
        if self._r["r1"] >= self._stack_limit:
            raise RuntimeError("stack overflow")
        self._pc = self._next_pc
        self._next_pc = self._pc + 1
        return self._pc

    def jump(self, delta_r: str) -> None:
        Log.t(f"{delta_r} = {self._r[delta_r]}")
        self._next_pc = self._pc + self._r[delta_r]

    def jumpv(self, delta_v: int) -> None:
        self._next_pc = self._pc + delta_v

    def sys(self, id_r: str) -> None:
        Log.t(f"{id_r} = {self._r[id_r]}")
        self._syscall[self._r[id_r]]()

    def sysv(self, id_v: int) -> None:
        self._syscall[id_v]()

    def exit(self, val_r: str) -> int:
        Log.t(f"{val_r} = {self._r[val_r]}")
        return self._r[val_r]

    def exitv(self, val_v: int) -> int:
        return val_v

    def not_(self, dst_r: str, op_r: str) -> None:
        Log.t(f"{op_r} = {self._r[op_r]}")
        self._r[dst_r] = 1 if self._r[op_r] else 0

    def set_(self, dst_r: str, src_r: str) -> None:
        Log.t(f"{src_r} = {self._r[src_r]}")
        self._r[dst_r] = self._r[src_r]

    def setv(self, dst_r: str, src_v: int) -> None:
        self._r[dst_r] = src_v

    def jumpif(self, delta_r: str, cond_r: str) -> None:
        Log.t(f"{delta_r} = {self._r[delta_r]}, {cond_r} = {self._r[cond_r]}")
        if self._r[cond_r] != 0:
            self._next_pc = self._pc + self._r[delta_r]

    def jumpifv(self, delta_v: int, cond_r: str) -> None:
        Log.t(f"{cond_r} = {self._r[cond_r]}")
        if self._r[cond_r] != 0:
            self._next_pc = self._pc + delta_v

    def load(self, dst_r: str, src_r: str, off_v: int) -> None:
        loc: int = self._r[src_r] + off_v
        if loc < 0 or loc >= len(self._m):
            # todo: better exceptions
            raise RuntimeError(f"segment fault: {loc}")
        Log.t(f"{src_r} = {self._r[src_r]}, [{src_r} + {off_v}] = {self._m[loc]}")
        self._r[dst_r] = self._m[loc]

    def store(self, src_r: str, dst_r: str, off_v: int) -> None:
        Log.t(f"{src_r} = {self._r[src_r]}, {dst_r} = {self._r[dst_r]}")
        loc: int = self._r[dst_r] + off_v
        if loc < 0 or loc >= len(self._m):
            # todo: better exceptions
            raise RuntimeError(f"segment fault: {loc}")
        self._m[loc] = self._r[src_r]

    def add(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = self._r[op1_r] + self._r[op2_r]

    def addv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = self._r[op1_r] + op2_v

    def sub(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = self._r[op1_r] - self._r[op2_r]

    def subv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = self._r[op1_r] - op2_v

    def mul(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = self._r[op1_r] * self._r[op2_r]

    def mulv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = self._r[op1_r] * op2_v

    def div(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = self._r[op1_r] // self._r[op2_r]

    def divv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = self._r[op1_r] // op2_v

    def mod(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = self._r[op1_r] % self._r[op2_r]

    def modv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = self._r[op1_r] % op2_v

    def or_(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = self._r[op1_r] | self._r[op2_r]

    def orv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = self._r[op1_r] | op2_v

    def and_(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = self._r[op1_r] & self._r[op2_r]

    def andv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = self._r[op1_r] & op2_v

    def xor(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = self._r[op1_r] ^ self._r[op2_r]

    def xorv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = self._r[op1_r] ^ op2_v

    def eq(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = 1 if self._r[op1_r] == self._r[op2_r] else 0

    def eqv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = 1 if self._r[op1_r] == op2_v else 0

    def neq(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = 1 if self._r[op1_r] != self._r[op2_r] else 0

    def neqv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = 1 if self._r[op1_r] != op2_v else 0

    def gt(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = 1 if self._r[op1_r] > self._r[op2_r] else 0

    def gtv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = 1 if self._r[op1_r] > op2_v else 0

    def geq(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = 1 if self._r[op1_r] >= self._r[op2_r] else 0

    def geqv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = 1 if self._r[op1_r] >= op2_v else 0

    def lt(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = 1 if self._r[op1_r] < self._r[op2_r] else 0

    def ltv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = 1 if self._r[op1_r] < op2_v else 0

    def leq(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}, {op2_r} = {self._r[op2_r]}")
        self._r[dst_r] = 1 if self._r[op1_r] <= self._r[op2_r] else 0

    def leqv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        Log.t(f"{op1_r} = {self._r[op1_r]}")
        self._r[dst_r] = 1 if self._r[op1_r] <= op2_v else 0


class ARInterpreter:
    def __init__(
        self,
        machine: Machine,
    ):
        self._m = machine

    def interpret(
        self,
        prog: str,
    ) -> int:
        self._cur: int = 0
        self._prog: str = prog
        self._len: int = len(self._prog)
        instructions: list[tuple] = self._load()
        pc: int = 0
        while True:
            if not Log.e(
                f"program counter out of bounds: {pc}",
                pc < 0 or pc >= len(instructions),
            ):
                # todo: better exceptions
                raise RuntimeError()
            i = instructions[pc]
            Log.begin_t()
            Log.t(f"executing instruction {pc}: {' '.join(i)}")
            match i[0]:
                case "jump":
                    self._m.jump(i[1])

                case "jumpv":
                    self._m.jumpv(int(i[1]))

                case "sys":
                    self._m.sys(i[1])

                case "sysv":
                    self._m.sysv(int(i[1]))

                case "exit":
                    return self._m.exit(i[1])

                case "exitv":
                    return self._m.exitv(int(i[1]))

                case "not":
                    self._m.not_(i[1], i[2])

                case "set":
                    self._m.set_(i[1], i[2])

                case "setv":
                    self._m.setv(i[1], int(i[2]))

                case "jumpif":
                    self._m.jumpif(i[1], i[2])

                case "jumpifv":
                    self._m.jumpifv(int(i[1]), i[2])

                case "load":
                    self._m.load(i[1], i[2], int(i[3]))

                case "store":
                    self._m.store(i[1], i[2], int(i[3]))

                case "add":
                    self._m.add(i[1], i[2], i[3])

                case "addv":
                    self._m.addv(i[1], i[2], int(i[3]))

                case "sub":
                    self._m.sub(i[1], i[2], i[3])

                case "subv":
                    self._m.subv(i[1], i[2], int(i[3]))

                case "mul":
                    self._m.mul(i[1], i[2], i[3])

                case "mulv":
                    self._m.mulv(i[1], i[2], int(i[3]))

                case "div":
                    self._m.div(i[1], i[2], i[3])

                case "divv":
                    self._m.divv(i[1], i[2], int(i[3]))

                case "mod":
                    self._m.mod(i[1], i[2], i[3])

                case "modv":
                    self._m.modv(i[1], i[2], int(i[3]))

                case "or":
                    self._m.or_(i[1], i[2], i[3])

                case "orv":
                    self._m.orv(i[1], i[2], int(i[3]))

                case "and":
                    self._m.and_(i[1], i[2], i[3])

                case "andv":
                    self._m.andv(i[1], i[2], int(i[3]))

                case "xor":
                    self._m.xor(i[1], i[2], i[3])

                case "xorv":
                    self._m.xorv(i[1], i[2], int(i[3]))

                case "eq":
                    self._m.eq(i[1], i[2], i[3])

                case "eqv":
                    self._m.eqv(i[1], i[2], int(i[3]))

                case "neq":
                    self._m.neq(i[1], i[2], i[3])

                case "neqv":
                    self._m.neqv(i[1], i[2], int(i[3]))

                case "gt":
                    self._m.gt(i[1], i[2], i[3])

                case "gtv":
                    self._m.gtv(i[1], i[2], int(i[3]))

                case "geq":
                    self._m.geq(i[1], i[2], i[3])

                case "geqv":
                    self._m.geqv(i[1], i[2], int(i[3]))

                case "lt":
                    self._m.lt(i[1], i[2], i[3])

                case "ltv":
                    self._m.ltv(i[1], i[2], int(i[3]))

                case "leq":
                    self._m.leq(i[1], i[2], i[3])

                case "leqv":
                    self._m.leqv(i[1], i[2], int(i[3]))

            # todo: see Machine.clk
            pc = self._m.clk()

            Log.end_t()

    # todo: ugly
    def _load(self) -> list[tuple]:
        tokens: list[str] = []
        self._consume_until_token()
        while not self._at_end():
            tokens.append(self._consume())

        instructions: list[tuple] = []
        idx: int = 0
        while idx < len(tokens):
            match tokens[idx]:
                case "jump" | "jumpv" | "sys" | "sysv" | "exit" | "exitv":
                    if not Log.e(
                        f"expected 1 argument for {tokens[idx]}, found {len(tokens) - idx - 1}",
                        len(tokens) - idx < 2,
                    ):
                        # todo
                        raise RuntimeError()
                    instructions.append((tokens[idx], tokens[idx + 1]))
                    idx += 2

                case "not" | "notv" | "set" | "setv" | "jumpif" | "jumpifv":
                    if not Log.e(
                        f"expected 2 argument for {tokens[idx]}, found {len(tokens) - idx - 1}",
                        len(tokens) - idx < 3,
                    ):
                        # todo
                        raise RuntimeError()
                    instructions.append((tokens[idx], tokens[idx + 1], tokens[idx + 2]))
                    idx += 3

                case (
                    "load"
                    | "store"
                    | "add"
                    | "addv"
                    | "sub"
                    | "subv"
                    | "mul"
                    | "mulv"
                    | "div"
                    | "divv"
                    | "mod"
                    | "modv"
                    | "or"
                    | "orv"
                    | "and"
                    | "andv"
                    | "xor"
                    | "xorv"
                    | "eq"
                    | "eqv"
                    | "neq"
                    | "neqv"
                    | "gt"
                    | "gtv"
                    | "geq"
                    | "geqv"
                    | "lt"
                    | "ltv"
                    | "leq"
                    | "leqv"
                ):
                    if not Log.e(
                        f"expected 3 argument for {tokens[idx]}, found {len(tokens) - idx - 1}",
                        len(tokens) - idx < 4,
                    ):
                        # todo
                        raise RuntimeError()
                    instructions.append(
                        (tokens[idx], tokens[idx + 1], tokens[idx + 2], tokens[idx + 3])
                    )
                    idx += 4

                case _:
                    Log.e(f"{tokens[idx]} is not a valid instruction")
                    # todo
                    raise RuntimeError()

        Log.d("finished loading instructions")
        return instructions

    def _at_end(self) -> bool:
        return self._cur >= self._len

    def _peek(self) -> str:
        return self._prog[self._cur]

    def _advance(self) -> None:
        self._cur += 1

    def _consume_until_token(self) -> None:
        while not self._at_end():
            # skip whitespace
            if self._peek().isspace():
                self._advance()

            # skip comment
            elif self._peek() == "#":
                while not self._at_end() and self._peek() != "\n":
                    self._advance()

                if not self._at_end():
                    self._advance()

            else:
                return

    # assumes self._cur already at token
    def _consume(self) -> str:
        start = self._cur
        while not self._at_end() and not self._peek().isspace():
            self._advance()
        end = self._cur
        self._consume_until_token()
        return self._prog[start:end]
