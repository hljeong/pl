from __future__ import annotations
from typing import Callable, Union

from common import Log

# reorganize stuff not immediately concerning ar
RegFile = dict[str, int]
Memory = list[int]
SysCall = Callable[[], None]


# 2 "mb" mem
DEFAULT_MEM_SIZE: int = 2 * 1024 * 1024

# 16 "kb" stack
# what about a variable-sized stack?
DEFAULT_STACK_SIZE: int = 16 * 1024

USE_DEFAULT_SYSCALL: dict[int, SysCall] = {}


class Machine:
    _regs: list[str] = [
        "r0",
        "r1",
        "r2",
        "r3",
        "r4",
        "r5",
        "r6",
        "r7",
        "r8",
        "r9",
        "r10",
        "r11",
        "r12",
        "r13",
        "r14",
        "r15",
        "r16",
        "r17",
        "r18",
        "r19",
        "r20",
        "r21",
        "r22",
        "r23",
        "r24",
        "r25",
        "r26",
        "r27",
        "r28",
        "r29",
        "r30",
        "r31",
        "pc",
    ]

    _aliases: dict[str, str] = {
        "r1": "sp",
        "r2": "ra",
        "r3": "t0",
        "r4": "t1",
        "r5": "t2",
        "r6": "t3",
        "r7": "t4",
        "r8": "t5",
        "r9": "t6",
        "r10": "t7",
        "r11": "t8",
        "r12": "t9",
        "r13": "t10",
        "r14": "a0",
        "r15": "a1",
        "r16": "a2",
        "r17": "a3",
        "r18": "a4",
        "r19": "a5",
        "r20": "s0",
        "r21": "s1",
        "r22": "s2",
        "r23": "s3",
        "r24": "s4",
        "r25": "s5",
        "r26": "s6",
        "r27": "s7",
        "r28": "s8",
        "r29": "s9",
        "r30": "s10",
        "r31": "s11",
    }

    _aliases_inv: dict[str, str] = {reg: alias for alias, reg in _aliases.items()}

    # todo: clean aliasing up
    @staticmethod
    def _alias(reg: str) -> str:
        if reg not in Machine._regs:
            # todo
            raise RuntimeError(f"register '{reg}' does not exist")

        if reg not in Machine._aliases:
            # todo
            raise RuntimeError(f"register '{reg}' does not have an alias")

        return Machine._aliases[reg]

    @staticmethod
    def _unalias(alias: str) -> str:
        if alias not in Machine._aliases_inv:
            return alias

        return Machine._aliases_inv[alias]

    @staticmethod
    def temp_reg_to_byte(reg: str) -> int:
        return Machine._regs.index(Machine._unalias(reg)) + 128

    def __init__(
        self,
        mem_size: int = DEFAULT_MEM_SIZE,
        stack_size: int = DEFAULT_STACK_SIZE,
        syscall: dict[int, SysCall] = USE_DEFAULT_SYSCALL,
    ):
        self._r: RegFile = {reg: 0 for reg in Machine._regs}
        self._mem_size: int = mem_size
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
        self._stack_size: int = stack_size

        # self._tracking: set[Union[str, int]] = set(["sp"])

    def __call__(self, prog: list[int]) -> int:
        if len(prog) < 2:
            raise RuntimeError("invalid program header")

        header: list[int] = prog[:2]
        body: list[int] = prog[2:]

        data_size: int = header[0]
        code_size: int = header[1]
        if len(body) != data_size + code_size:
            raise RuntimeError("inconsistent program header")

        if data_size + code_size > self._mem_size - self._stack_size:
            raise RuntimeError(
                f"program too large: {data_size + code_size} > {self._mem_size + self._stack_size}"
            )

        data: list[int] = body[:data_size]
        code: list[int] = body[data_size:]

        self._code_loc = self._mem_size - code_size
        for i, e in enumerate(code):
            self._m[self._code_loc + i] = e

        self._data_loc = self._code_loc - data_size
        for i, e in enumerate(data):
            self._m[self._data_loc + i] = e

        # skip nullptr
        self["sp"] = 1

        self["pc"] = self._code_loc
        self._next_pc: int = self._code_loc + 4
        self._next_mem_alloc: int = self._mem_size - code_size - data_size
        while self._clk():
            pass

        return self["a0"]

    def _clk(self) -> bool:
        pc: int = self._r["pc"]

        # todo: clean this up
        reg1: str = ""
        reg2: str = ""
        reg3: str = ""
        ins, val1, val2, val3 = self._m[pc : pc + 4]
        # todo: need something a lot better than this
        Log.t(f"{pc}: {ins} {val1} {val2} {val3}")
        if val1 >= 128:
            reg1 = Machine._regs[val1 - 128]
        if val2 >= 128:
            reg2 = Machine._regs[val2 - 128]
        if val3 >= 128:
            reg3 = Machine._regs[val3 - 128]

        # todo: there has to be a better way...
        match ins:
            case 0:
                self._jump(reg1)

            case 1:
                self._jumpv(val1)

            case 2:
                self._sys(reg1)

            case 3:
                self._sysv(val1)

            case 4:
                self._exit(reg1)
                return False

            case 5:
                self._exitv(val1)
                return False

            case 6:
                self._not_(reg1, reg2)

            case 7:
                self._set_(reg1, reg2)

            case 8:
                self._setv(reg1, val2)

            case 9:
                self._jumpif(reg1, reg2)

            case 10:
                self._jumpifv(val1, reg2)

            case 11:
                self._load(reg1, reg2, val3)

            case 12:
                self._store(reg1, reg2, val3)

            case 13:
                self._storev(val1, reg2, val3)

            case 14:
                self._add(reg1, reg2, reg3)

            case 15:
                self._addv(reg1, reg2, val3)

            case 16:
                self._sub(reg1, reg2, reg3)

            case 17:
                self._subv(reg1, reg2, val3)

            case 18:
                self._mul(reg1, reg2, reg3)

            case 19:
                self._mulv(reg1, reg2, val3)

            case 20:
                self._div(reg1, reg2, reg3)

            case 21:
                self._divv(reg1, reg2, val3)

            case 22:
                self._mod(reg1, reg2, reg3)

            case 23:
                self._modv(reg1, reg2, val3)

            case 24:
                self._or_(reg1, reg2, reg3)

            case 25:
                self._orv(reg1, reg2, val3)

            case 26:
                self._and_(reg1, reg2, reg3)

            case 27:
                self._andv(reg1, reg2, val3)

            case 28:
                self._xor(reg1, reg2, reg3)

            case 29:
                self._xorv(reg1, reg2, val3)

            case 30:
                self._eq(reg1, reg2, reg3)

            case 31:
                self._eqv(reg1, reg2, val3)

            case 32:
                self._neq(reg1, reg2, reg3)

            case 33:
                self._neqv(reg1, reg2, val3)

            case 34:
                self._gt(reg1, reg2, reg3)

            case 35:
                self._gtv(reg1, reg2, val3)

            case 36:
                self._geq(reg1, reg2, reg3)

            case 37:
                self._geqv(reg1, reg2, val3)

            case 38:
                self._lt(reg1, reg2, reg3)

            case 39:
                self._ltv(reg1, reg2, val3)

            case 40:
                self._leq(reg1, reg2, reg3)

            case 41:
                self._leqv(reg1, reg2, val3)

        if self._r["r1"] >= self._stack_size:
            # todo
            raise RuntimeError("stack overflow")

        self["pc"] = self._next_pc
        self._next_pc += 4
        return True

    def _print(self) -> None:
        i: int = self._r["r14"]
        while i < len(self._m) and self._m[i] != 0:
            print(chr(self._m[i]), end="")
            i += 1

        if i == len(self._m) and self._m[-1] != 0:
            # error -> return 1
            self._r["r14"] = 1
            return

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
        print(self._r["r14"], end="")

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

    def _fmt(self, reg_or_addr: Union[str, int]) -> str:
        if type(reg_or_addr) is str:
            reg: str = self._unalias(reg_or_addr)

            if reg in self._aliases:
                return f"[bold][yellow]{self._alias(reg)}[/yellow][/bold] ([bold][yellow]{reg}[/yellow][/bold])"

            else:
                return f"[bold][yellow]{reg}[/yellow][/bold]"

        elif type(reg_or_addr) is int:
            addr: int = reg_or_addr

            return f"[bold][[blue]{addr}[/blue]][/bold]"

        assert False

    # todo: cleaner tracking
    def __getitem__(self, reg_or_addr: Union[str, int]) -> int:
        if type(reg_or_addr) is str:
            reg: str = self._unalias(reg_or_addr)
            val = self._r[reg]

        elif type(reg_or_addr) is int:
            addr: int = reg_or_addr
            val = self._m[addr]

        else:
            assert False

        Log.tf(f"{self._fmt(reg_or_addr)} = {val}")
        return val

    def __setitem__(self, reg_or_addr: Union[str, int], val: int) -> None:
        if type(reg_or_addr) is str:
            reg: str = self._unalias(reg_or_addr)
            old_val: int = self._r[reg]
            self._r[reg] = val

        elif type(reg_or_addr) is int:
            addr: int = reg_or_addr
            old_val: int = self._m[addr]
            self._m[addr] = val

        else:
            assert False

        Log.tf(
            f"{self._fmt(reg_or_addr)} = [red]{old_val}[/red] -> [green]{val}[/green]"
        )

    def _jump(self, delta_r: str) -> None:
        self._next_pc = self["pc"] + self[delta_r] * 4

    def _jumpv(self, delta_v: int) -> None:
        self._next_pc = self["pc"] + delta_v * 4

    def _sys(self, id_r: str) -> None:
        self._syscall[self[id_r]]()

    def _sysv(self, id_v: int) -> None:
        self._syscall[id_v]()

    def _exit(self, val_r: str) -> None:
        self["a0"] = self[val_r]

    def _exitv(self, val_v: int) -> None:
        self["a0"] = val_v

    def _not_(self, dst_r: str, op_r: str) -> None:
        self[dst_r] = 1 if self[op_r] else 0

    def _set_(self, dst_r: str, src_r: str) -> None:
        self[dst_r] = self[src_r]

    def _setv(self, dst_r: str, src_v: int) -> None:
        self[dst_r] = src_v

    def _jumpif(self, delta_r: str, cond_r: str) -> None:
        if self[cond_r] != 0:
            self._next_pc = self["pc"] + self[delta_r] * 4

    def _jumpifv(self, delta_v: int, cond_r: str) -> None:
        if self[cond_r] != 0:
            self._next_pc = self["pc"] + delta_v * 4

    def _load(self, dst_r: str, src_r: str, off_v: int) -> None:
        loc: int = self[src_r] + off_v
        if loc < 0 or loc >= len(self._m):
            # todo: better exceptions
            raise RuntimeError(f"segment fault: {loc}")
        self[dst_r] = self[loc]

    def _store(self, src_r: str, dst_r: str, off_v: int) -> None:
        loc: int = self[dst_r] + off_v
        if loc < 0 or loc >= len(self._m):
            # todo: better exceptions
            raise RuntimeError(f"segment fault: {loc}")
        self[loc] = self[src_r]

    def _storev(self, src_v: int, dst_r: str, off_v: int) -> None:
        loc: int = self[dst_r] + off_v
        if loc < 0 or loc >= len(self._m):
            # todo: better exceptions
            raise RuntimeError(f"segment fault: {loc}")
        self[loc] = src_v

    def _add(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = self[op1_r] + self[op2_r]

    def _addv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = self[op1_r] + op2_v

    def _sub(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = self[op1_r] - self[op2_r]

    def _subv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = self[op1_r] - op2_v

    def _mul(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = self[op1_r] * self[op2_r]

    def _mulv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = self[op1_r] * op2_v

    def _div(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = self[op1_r] // self[op2_r]

    def _divv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = self[op1_r] // op2_v

    def _mod(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = self[op1_r] % self[op2_r]

    def _modv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = self[op1_r] % op2_v

    def _or_(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = self[op1_r] | self[op2_r]

    def _orv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = self[op1_r] | op2_v

    def _and_(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = self[op1_r] & self[op2_r]

    def _andv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = self[op1_r] & op2_v

    def _xor(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = self[op1_r] ^ self[op2_r]

    def _xorv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = self[op1_r] ^ op2_v

    def _eq(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = 1 if self[op1_r] == self[op2_r] else 0

    def _eqv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = 1 if self[op1_r] == op2_v else 0

    def _neq(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = 1 if self[op1_r] != self[op2_r] else 0

    def _neqv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = 1 if self[op1_r] != op2_v else 0

    def _gt(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = 1 if self[op1_r] > self[op2_r] else 0

    def _gtv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = 1 if self[op1_r] > op2_v else 0

    def _geq(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = 1 if self[op1_r] >= self[op2_r] else 0

    def _geqv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = 1 if self[op1_r] >= op2_v else 0

    def _lt(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = 1 if self[op1_r] < self[op2_r] else 0

    def _ltv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = 1 if self[op1_r] < op2_v else 0

    def _leq(self, dst_r: str, op1_r: str, op2_r: str) -> None:
        self[dst_r] = 1 if self[op1_r] <= self[op2_r] else 0

    def _leqv(self, dst_r: str, op1_r: str, op2_v: int) -> None:
        self[dst_r] = 1 if self[op1_r] <= op2_v else 0


class AAssembler:
    def __init__(
        self,
        machine: Machine,
    ):
        self._m = machine

    def __call__(self, prog: str) -> int:
        self._cur: int = 0
        self._prog: str = prog
        self._len: int = len(self._prog)
        return self._m(self._load())

    # todo: ugly
    def _load(self) -> list[int]:
        tokens: list[str] = []
        self._consume_until_token()
        while not self._at_end():
            tokens.append(self._consume())

        ins_list: list[str] = [
            "jump",
            "jumpv",
            "sys",
            "sysv",
            "exit",
            "exitv",
            "not",
            "set",
            "setv",
            "jumpif",
            "jumpifv",
            "load",
            "store",
            "storev",
            "add",
            "addv",
            "sub",
            "subv",
            "mul",
            "mulv",
            "div",
            "divv",
            "mod",
            "modv",
            "or",
            "orv",
            "and",
            "andv",
            "xor",
            "xorv",
            "eq",
            "eqv",
            "neq",
            "neqv",
            "gt",
            "gtv",
            "geq",
            "geqv",
            "lt",
            "ltv",
            "leq",
            "leqv",
        ]

        code: list[int] = []
        label: dict[str, int] = {}
        idx: int = 0
        ins_num: int = 0
        to_link: dict[int, str] = {}
        section: str = "none"
        data: list[int] = []
        # todo: what even is this??
        string_constant_to_link: dict[tuple[int, int], int] = {}
        string_constant_map: list[int] = []

        def val(value_or_string_constant_link: str, loc: int) -> int:
            if value_or_string_constant_link.startswith("="):
                string_constant_to_link[(ins_num, loc)] = int(
                    value_or_string_constant_link[1:]
                )
                return 0

            else:
                return int(value_or_string_constant_link)

        while idx < len(tokens):
            if tokens[idx].startswith("."):
                section = tokens[idx][1:]
                idx += 1
                continue

            match section:
                case "code":
                    ins: str = tokens[idx]
                    match ins:
                        case "jump" | "jumpv" | "sys" | "sysv" | "exit" | "exitv":
                            if not Log.e(
                                f"expected 1 argument for {ins}, found {len(tokens) - idx - 1}",
                                len(tokens) - idx < 2,
                            ):
                                # todo
                                raise RuntimeError()

                            if ins == "jumpv":
                                delta_v: str = tokens[idx + 1]
                                if not (
                                    delta_v.isdigit()
                                    or delta_v.startswith("-")
                                    and delta_v[1:].isdigit()
                                ):
                                    to_link[ins_num] = delta_v
                                    code.extend(
                                        [
                                            ins_list.index(ins),
                                            0,
                                            0,
                                            0,
                                        ]
                                    )

                                else:
                                    # no string constant linking here...
                                    # as it shouldnt
                                    code.extend(
                                        [
                                            ins_list.index(ins),
                                            int(tokens[idx + 1]),
                                            0,
                                            0,
                                        ]
                                    )

                            elif ins.endswith("v"):
                                code.extend(
                                    [ins_list.index(ins), val(tokens[idx + 1], 1), 0, 0]
                                )

                            else:
                                code.extend(
                                    [
                                        ins_list.index(ins),
                                        Machine.temp_reg_to_byte(tokens[idx + 1]),
                                        0,
                                        0,
                                    ]
                                )

                            idx += 2
                            ins_num += 1

                        case "not" | "notv" | "set" | "setv" | "jumpif" | "jumpifv":
                            if not Log.e(
                                f"expected 2 argument for {ins}, found {len(tokens) - idx - 1}",
                                len(tokens) - idx < 3,
                            ):
                                # todo
                                raise RuntimeError()

                            if ins == "jumpifv":
                                delta_v: str = tokens[idx + 1]
                                if not (
                                    delta_v.isdigit()
                                    or delta_v.startswith("-")
                                    and delta_v[1:].isdigit()
                                ):
                                    to_link[ins_num] = delta_v
                                    code.extend(
                                        [
                                            ins_list.index(ins),
                                            0,
                                            Machine.temp_reg_to_byte(tokens[idx + 2]),
                                            0,
                                        ]
                                    )

                                else:
                                    code.extend(
                                        [
                                            ins_list.index(ins),
                                            val(tokens[idx + 1], 1),
                                            Machine.temp_reg_to_byte(tokens[idx + 2]),
                                            0,
                                        ]
                                    )

                            elif ins.endswith("v"):
                                code.extend(
                                    [
                                        ins_list.index(ins),
                                        Machine.temp_reg_to_byte(tokens[idx + 1]),
                                        val(tokens[idx + 2], 2),
                                        0,
                                    ]
                                )

                            else:
                                code.extend(
                                    [
                                        ins_list.index(ins),
                                        Machine.temp_reg_to_byte(tokens[idx + 1]),
                                        Machine.temp_reg_to_byte(tokens[idx + 2]),
                                        0,
                                    ]
                                )

                            idx += 3
                            ins_num += 1

                        case (
                            "load"
                            | "store"
                            | "storev"
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
                                f"expected 3 argument for {ins}, found {len(tokens) - idx - 1}",
                                len(tokens) - idx < 4,
                            ):
                                # todo
                                raise RuntimeError()

                            if ins == "load" or ins == "store":
                                code.extend(
                                    [
                                        ins_list.index(ins),
                                        Machine.temp_reg_to_byte(tokens[idx + 1]),
                                        Machine.temp_reg_to_byte(tokens[idx + 2]),
                                        val(tokens[idx + 3], 3),
                                    ]
                                )

                            elif ins == "storev":
                                code.extend(
                                    [
                                        ins_list.index(ins),
                                        val(tokens[idx + 1], 1),
                                        Machine.temp_reg_to_byte(tokens[idx + 2]),
                                        val(tokens[idx + 3], 3),
                                    ]
                                )

                            elif ins.endswith("v"):
                                code.extend(
                                    [
                                        ins_list.index(ins),
                                        Machine.temp_reg_to_byte(tokens[idx + 1]),
                                        Machine.temp_reg_to_byte(tokens[idx + 2]),
                                        val(tokens[idx + 3], 3),
                                    ]
                                )

                            else:
                                code.extend(
                                    [
                                        ins_list.index(ins),
                                        Machine.temp_reg_to_byte(tokens[idx + 1]),
                                        Machine.temp_reg_to_byte(tokens[idx + 2]),
                                        Machine.temp_reg_to_byte(tokens[idx + 3]),
                                    ]
                                )

                            idx += 4
                            ins_num += 1

                        case _:
                            # todo: this is bad, offload this to lexer and parser
                            if ins.endswith(":"):
                                if ins[:-1] in label:
                                    # todo
                                    Log.e(f"duplicate label '{ins[:-1]}'")
                                    raise RuntimeError()

                                label[ins[:-1]] = ins_num
                                idx += 1

                            elif len(tokens) - idx >= 2 and tokens[idx + 1] == ":":
                                if ins in label:
                                    # todo
                                    Log.e(f"duplicate label '{ins}'")
                                    raise RuntimeError()

                                label[ins] = ins_num
                                idx += 2

                            else:
                                # todo
                                Log.e(f"'{ins}' is not a valid instruction")
                                raise RuntimeError()

                case "data":
                    # todo: validate tokens to be escaped strings
                    #       -- probably defer this to lexer
                    # todo: why do i have to do this manually :(
                    # extremely inefficient lazy bum implementation btw
                    def valid_escaped_string(s: str) -> bool:
                        i = 1
                        while i < len(s):
                            if s[i] == "\\":
                                if i + 1 >= len(s):
                                    return False
                                i += 1

                            if s[i] == '"':
                                return i == len(s) - 1

                            i += 1
                        return False

                    s: str = tokens[idx]
                    idx += 1
                    while idx < len(tokens) and not valid_escaped_string(s):
                        # whitespace info is lost here...
                        s += " "
                        s += tokens[idx]
                        idx += 1
                    if idx == len(tokens) and not valid_escaped_string(s):
                        raise RuntimeError("escaped string parsed until end of file")
                    s = bytes(s[1:-1], "utf-8").decode("unicode_escape")
                    string_constant_map.append(len(data))
                    data.extend(list(map(ord, s)))
                    data.append(0)

                case _:
                    # todo
                    Log.e(f"invalid section '{section}'")

        for ins_num_to_link, label_to_link in to_link.items():
            if label_to_link not in label:
                # todo
                Log.e(f"label '{label_to_link}' does not exist")
                raise RuntimeError()

            code[4 * ins_num_to_link + 1] = label[label_to_link] - ins_num_to_link

        # todo: terrible variable naming
        for ins_num_and_loc, string_const_to_link in string_constant_to_link.items():
            if string_const_to_link >= len(string_constant_map):
                # todo:
                Log.e(f"string constant '={string_const_to_link}' does not exist")
                raise RuntimeError()

            ins_num_to_link: int
            loc_to_link: int
            ins_num_to_link, loc_to_link = ins_num_and_loc
            code[4 * ins_num_to_link + loc_to_link] = -(
                4 * ins_num_to_link
                + (len(data) - string_constant_map[string_const_to_link])
            )

        prog: list[int] = []
        prog.append(len(data))
        prog.append(len(code))
        prog.extend(data)
        prog.extend(code)

        Log.d("finished loading instructions")
        return prog

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
