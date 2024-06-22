from __future__ import annotations
from typing import Callable

from common import Log

regfile = dict[str, int]
memory = list[int]


def _syscall_print(r: regfile, m: memory) -> None:
    i: int = r["r14"]
    while i < len(m) and m[i] != 0:
        print(chr(m[i]), end="")
        i += 1

    if i == len(m) and m[-1] != 0:
        # error -> return 1
        r["r14"] = 1
        return

    print()
    # success -> return 0
    r["r14"] = 0


def _syscall_read(r: regfile, m: memory) -> None:
    i: int = r["r14"]
    read = input()
    for j in range(len(read)):
        if i + j >= len(m):
            # error -> return 1
            r["r14"] = 1
            return

        m[i + j] = ord(read[j])

    if i + len(read) >= len(m):
        # error -> return 1
        r["r14"] = 1
        return

    # 0-terminate
    m[i + len(read)] = 0

    # success -> return 0
    r["r14"] = 0


def _stoi(r: regfile, m: memory) -> None:
    i: int = r["r14"]
    int_str: str = ""
    while i < len(m) and m[i] != 0:
        int_str += chr(m[i])
        i += 1

    if i == len(m) and m[-1] != 0:
        # error -> return 1
        r["r14"] = 1
        return

    # success -> return 0 and int value
    r["r14"] = 0
    r["r15"] = int(int_str)


def _printi(r: regfile, m: memory) -> None:
    print(r["r14"])

    # success -> return 0
    r["r14"] = 0


DEFAULT_REGFILE_SIZE: int = 32
DEFAULT_MEM_SIZE: int = 2 * 1024 * 1024
# todo: create ProgramState class
DEFAULT_SYSCALL: dict[int, Callable[[regfile, memory], None]] = {
    0: _syscall_print,
    1: _syscall_read,
    2: _stoi,
    3: _printi,
}


class ARInterpreter:
    def __init__(
        self,
        regfile_size: int = DEFAULT_REGFILE_SIZE,
        mem_size: int = DEFAULT_MEM_SIZE,
        syscall: dict[int, Callable[[regfile, memory], None]] = DEFAULT_SYSCALL,
    ):
        self._regfile_size = regfile_size
        self._mem_size = mem_size
        self._syscall = syscall

    def interpret(
        self,
        prog: str,
    ) -> int:
        self._cur: int = 0
        self._prog: str = prog
        self._len: int = len(self._prog)
        instructions: list[tuple] = self._load()
        # program counter
        pc: int = 0
        # register file
        r: dict[str, int] = {f"r{i}": 0 for i in range(self._regfile_size)}
        # memory
        m: list[int] = [0] * self._mem_size
        while True:
            if not Log.e(
                f"program counter out of bounds: {pc}",
                pc < 0 or pc >= len(instructions),
            ):
                # todo
                raise RuntimeError()
            advance: bool = True
            i = instructions[pc]
            Log.t(f"executing instruction {pc}: {' '.join(i)}")
            match i[0]:
                case "jump":
                    pc += r[i[1]]
                    advance = False

                case "jumpv":
                    pc += int(i[1])
                    advance = False

                case "sys":
                    self._syscall[r[i[1]]](r, m)

                case "sysv":
                    self._syscall[int(i[1])](r, m)

                case "exit":
                    return r[i[1]]

                case "exitv":
                    return int(i[1])

                case "not":
                    r[i[1]] = 1 if r[i[2]] else 0

                # why does this exist...
                case "notv":
                    r[i[1]] = 1 if int(i[2]) else 0

                case "set":
                    r[i[1]] = r[i[2]]

                case "setv":
                    r[i[1]] = int(i[2])

                case "jumpif":
                    if r[i[2]] != 0:
                        pc += r[i[1]]
                        advance = False

                case "jumpifv":
                    if r[i[2]] != 0:
                        pc += int(i[1])
                        advance = False

                case "load":
                    r[i[1]] = m[r[i[2]] + int(i[3])]

                case "store":
                    m[r[i[2]] + int(i[3])] = r[i[1]]

                case "add":
                    r[i[1]] = r[i[2]] + r[i[3]]

                case "addv":
                    r[i[1]] = r[i[2]] + int(i[3])

                case "sub":
                    r[i[1]] = r[i[2]] - r[i[3]]

                case "subv":
                    r[i[1]] = r[i[2]] - int(i[3])

                case "mul":
                    r[i[1]] = r[i[2]] * r[i[3]]

                case "mulv":
                    r[i[1]] = r[i[2]] * int(i[3])

                case "div":
                    r[i[1]] = r[i[2]] // r[i[3]]

                case "divv":
                    r[i[1]] = r[i[2]] // int(i[3])

                case "mod":
                    r[i[1]] = r[i[2]] % r[i[3]]

                case "modv":
                    r[i[1]] = r[i[2]] % int(i[3])

                case "or":
                    r[i[1]] = r[i[2]] | r[i[3]]

                case "orv":
                    r[i[1]] = r[i[2]] | int(i[3])

                case "and":
                    r[i[1]] = r[i[2]] & r[i[3]]

                case "andv":
                    r[i[1]] = r[i[2]] & int(i[3])

                case "xor":
                    r[i[1]] = r[i[2]] ^ r[i[3]]

                case "xorv":
                    r[i[1]] = r[i[2]] ^ int(i[3])

                case "eq":
                    r[i[1]] = 1 if r[i[2]] == r[i[3]] else 0

                case "eqv":
                    r[i[1]] = 1 if r[i[2]] == int(i[3]) else 0

                case "neq":
                    r[i[1]] = 1 if r[i[2]] != r[i[3]] else 0

                case "neqv":
                    r[i[1]] = 1 if r[i[2]] != int(i[3]) else 0

                case "gt":
                    r[i[1]] = 1 if r[i[2]] > r[i[3]] else 0

                case "gtv":
                    r[i[1]] = 1 if r[i[2]] > int(i[3]) else 0

                case "geq":
                    r[i[1]] = 1 if r[i[2]] >= r[i[3]] else 0

                case "geqv":
                    r[i[1]] = 1 if r[i[2]] >= int(i[3]) else 0

                case "lt":
                    r[i[1]] = 1 if r[i[2]] < r[i[3]] else 0

                case "ltv":
                    r[i[1]] = 1 if r[i[2]] < int(i[3]) else 0

                case "leq":
                    r[i[1]] = 1 if r[i[2]] <= r[i[3]] else 0

                case "leqv":
                    r[i[1]] = 1 if r[i[2]] <= int(i[3]) else 0

            if advance:
                pc += 1

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
