from __future__ import annotations
from typing import Union, cast, Callable

from common import Log, Bits, Monad, Placeholder

from .common import Reg, Addr, RegFile, Mem, Ins, Prog

# 2 mb mem
DEFAULT_MEM_SIZE: int = 2 * 1024 * 1024

# 16 kb stack
DEFAULT_STACK_SIZE: int = 16 * 1024

BTypeDispatch = Callable[[Reg, Reg, Addr], None]
OITypeDispatch = Callable[[Reg, Reg, Addr], None]
MTypeDispatch = Callable[[Reg, Reg, Addr], None]
OTypeDispatch = Callable[[Reg, Reg, Reg], None]
JTypeDispatch = Callable[[Addr], None]
ETypeDispatch = Callable[[], None]
Dispatch = Union[
    BTypeDispatch,
    OITypeDispatch,
    MTypeDispatch,
    OTypeDispatch,
    JTypeDispatch,
    ETypeDispatch,
]
Decode = Callable[[Bits], tuple[Dispatch, dict[str, Union[Reg, int]]]]


class MP0:
    _reg_to_alias: dict[Reg, Reg] = {
        "r0": "zr",
        "r1": "pc",
        "r2": "sp",
        "r3": "ra",
        "r4": "t0",
        "r5": "t1",
        "r6": "t2",
        "r7": "t3",
        "r8": "t4",
        "r9": "t5",
        "r10": "t6",
        "r11": "t7",
        "r12": "t8",
        "r13": "t9",
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

    _alias_to_reg: dict[Reg, Reg] = {alias: reg for reg, alias in _reg_to_alias.items()}

    _regs: list[Reg] = list(_reg_to_alias.keys())

    _aliases: list[Reg] = list(_alias_to_reg.keys())

    @staticmethod
    def _is_reg_or_alias(reg_or_alias: Reg) -> bool:
        return reg_or_alias in MP0._regs or reg_or_alias in MP0._aliases

    @staticmethod
    def _alias(reg: Reg) -> Reg:
        if not MP0._is_reg_or_alias(reg):
            # todo
            raise RuntimeError(f"register '{reg}' does not exist")

        return MP0._reg_to_alias[reg] if reg in MP0._regs else reg

    @staticmethod
    def _unalias(alias: Reg) -> Reg:
        if not MP0._is_reg_or_alias(alias):
            # todo
            raise RuntimeError(f"register '{alias}' does not exist")

        return MP0._alias_to_reg[alias] if alias in MP0._aliases else alias

    @staticmethod
    def reg(reg: Reg) -> Ins.Frag:
        return Ins.Frag(MP0._regs.index(MP0._unalias(reg)), 5)

    @staticmethod
    def count_instructions_executed(prog: Prog) -> int:
        m: MP0 = MP0()
        m(prog)
        return m.ins_count

    def __init__(
        self,
        mem_size: int = DEFAULT_MEM_SIZE,
        stack_size: int = DEFAULT_STACK_SIZE,
    ):
        self._r: RegFile = RegFile(MP0._regs)
        self._mem_size: int = mem_size
        self._m: Mem = Mem(self._mem_size)
        self._stack_size: int = stack_size
        self._ins_count: int = 0

    @property
    def ins_count(self) -> int:
        return self._ins_count

    # todo: this is not great...
    def _decode_type(self, frag: Bits) -> tuple[Decode, Bits]:
        if ((frag.value >> 31) & 0b1) == 0b0:
            return self._decode_b_type, Bits.of(frag[:-1])

        elif ((frag.value >> 30) & 0b11) == 0b10:
            return self._decode_oi_type, Bits.of(frag[:-2])

        elif ((frag.value >> 29) & 0b111) == 0b110:
            return self._decode_m_type, Bits.of(frag[:-3])

        elif ((frag.value >> 28) & 0b1111) == 0b1110:
            return self._decode_o_type, Bits.of(frag[:-4])

        elif ((frag.value >> 27) & 0b11111) == 0b11110:
            return self._decode_j_type, Bits.of(frag[:-5])

        elif ((frag.value >> 26) & 0b111111) == 0b111110:
            return self._decode_e_type, Bits.of(frag[:-6])

        else:
            # todo
            raise ValueError(f"cannot decode type of instruction: {frag}")

    def _decode_b_type(self, frag: Bits) -> tuple[Dispatch, dict[str, Union[Reg, int]]]:
        opcode, src1, src2, off = frag.split(1, 5, 5, 20)
        dispatch: BTypeDispatch = [
            self._beq,
            self._bne,
        ][opcode.value]
        return (
            dispatch,
            {
                "src1": MP0._regs[src1.value],
                "src2": MP0._regs[src2.value],
                "off": off.svalue,
            },
        )

    def _decode_oi_type(
        self, frag: Bits
    ) -> tuple[OITypeDispatch, dict[str, Union[Reg, int]]]:
        opcode, dst, src, imm = frag.split(4, 5, 5, 16)
        dispatch: OITypeDispatch = [
            self._addi,
            self._subi,
            self._muli,
            self._divi,
            self._modi,
            self._ori,
            self._andi,
            self._xori,
            self._eqi,
            self._gti,
            self._gei,
            self._lti,
            self._lei,
            self._lsi,
            self._rsi,
        ][opcode.value]
        return (
            dispatch,
            {
                "dst": MP0._regs[dst.value],
                "src": MP0._regs[src.value],
                "imm": imm.svalue,
            },
        )

    def _decode_m_type(
        self, frag: Bits
    ) -> tuple[MTypeDispatch, dict[str, Union[Reg, int]]]:
        opcode, reg, base, off = frag.split(1, 5, 5, 18)
        match opcode.value:
            case 0:
                return (
                    self._l,
                    {
                        "dst": MP0._regs[reg.value],
                        "base": MP0._regs[base.value],
                        "off": off.svalue,
                    },
                )

            case 1:
                return (
                    self._s,
                    {
                        "src": MP0._regs[reg.value],
                        "base": MP0._regs[base.value],
                        "off": off.svalue,
                    },
                )

            case _:  # pragma: no cover
                # todo
                raise ValueError(f"invalid m type opcode: {opcode.value}")

    def _decode_o_type(
        self, frag: Bits
    ) -> tuple[OTypeDispatch, dict[str, Union[Reg, int]]]:
        opcode, dst, src1, src2, _ = frag.split(4, 5, 5, 5, 9)
        dispatch: OTypeDispatch = [
            self._add,
            self._sub,
            self._mul,
            self._div,
            self._mod,
            self._or,
            self._and,
            self._xor,
            self._eq,
            self._gt,
            self._ge,
            self._lt,
            self._le,
            self._ls,
            self._rs,
        ][opcode.value]
        return (
            dispatch,
            {
                "dst": MP0._regs[dst.value],
                "src1": MP0._regs[src1.value],
                "src2": MP0._regs[src2.value],
            },
        )

    def _decode_j_type(
        self, frag: Bits
    ) -> tuple[JTypeDispatch, dict[str, Union[Reg, int]]]:
        return (
            self._j,
            {
                "base": frag.value,
            },
        )

    def _decode_e_type(
        self, frag: Bits
    ) -> tuple[ETypeDispatch, dict[str, Union[Reg, int]]]:
        opcode, _ = frag.split(1, 25)
        dispatch: ETypeDispatch = [self._e, self._eb][opcode.value]
        return (dispatch, {})

    def __call__(self, prog: Prog) -> int:
        if len(prog) > self._mem_size - self._stack_size:
            raise RuntimeError(
                f"program too large: {len(prog)} > {self._mem_size - self._stack_size}"
            )

        # load program, skip 4 bytes over nullptr
        self._m[4 : 4 + len(prog)] = prog

        self._r[MP0._unalias("sp")] = self._mem_size
        self._r[MP0._unalias("pc")] = 4
        self._next_pc: int = self._r[MP0._unalias("pc")] + 4
        self._next_mem_alloc: int = 4 + len(prog)

        # exit condition is pc == nullptr
        while self._r[MP0._unalias("pc")] != 0:
            self._clk()
            Log.t("", tag="Runtime")
            # input()

        return self._r[MP0._unalias("a0")]

    def _clk(self) -> None:
        pc: int = self._r[MP0._unalias("pc")]
        dispatch: Dispatch
        operands: dict[str, Union[Reg, int]]
        dispatch, operands = cast(
            tuple[Dispatch, dict[str, Union[Reg, int]]],
            Monad(Bits(self[pc], 32))
            .then_and_keep(self._decode_type, returns=("decode", "value"))
            .then(Placeholder("decode"))
            .value,
        )
        dispatch(**operands)  # type: ignore

        self._r[MP0._unalias("pc")] = self._next_pc
        self._next_pc = self._r[MP0._unalias("pc")] + 4
        self._ins_count += 1

    def _fmt(self, reg_or_addr: Union[Reg, Addr]) -> str:
        if type(reg_or_addr) is Reg:
            reg: Reg = MP0._unalias(reg_or_addr)

            if reg == MP0._alias(reg):
                return f"[bold][yellow]{reg}[/yellow][/bold]"

            else:
                return f"[bold][yellow]{MP0._alias(reg)}[/yellow][/bold]"

                # tired of seeing the unaliased version when debugging...
                # return f"[bold][yellow]{MP0._alias(reg)}[/yellow][/bold] ([bold][yellow]{reg}[/yellow][/bold])"

        elif type(reg_or_addr) is Addr:
            addr: Addr = reg_or_addr

            return f"[bold][[blue]{addr}[/blue]][/bold]"

        assert False  # pragma: no cover

    def _fmtv(self, val: int, color: str = "blue") -> str:
        val_bytes: list[int] = list(
            (val >> (i * 8)) & ((1 << 8) - 1) for i in range(4)
        )[::-1]
        return f"[bold][{color}]{val}[/{color}] ([white]{' '.join(map(lambda byte: f'{byte:02x}', val_bytes))}[/white])[/bold]"

    # todo: cleaner tracking
    def __getitem__(self, reg_or_addr: Union[Reg, Addr]) -> int:
        if type(reg_or_addr) is Reg:
            reg: Reg = self._unalias(reg_or_addr)
            # hard wired 0
            if reg == "r0":
                return 0
            val = self._r[reg]
            if val > (1 << 31):
                val -= 1 << 32

        elif type(reg_or_addr) is Addr:
            addr: Addr = reg_or_addr
            if addr < 0 or addr + 4 > self._mem_size:
                raise RuntimeError(f"segment fault: 0x{addr:08x}")

            val = sum(self._m[addr + i] << (i * 8) for i in range(4))

        else:  # pragma: no cover
            assert False

        Log.tf(f"{self._fmt(reg_or_addr)} = {self._fmtv(val)}", tag="Runtime")
        return val

    def __setitem__(self, reg_or_addr: Union[Reg, Addr], val: int) -> None:
        if type(reg_or_addr) is Reg:
            reg: Reg = self._unalias(reg_or_addr)
            old_val: int = self._r[reg]
            # hard wired 0
            if reg == "r0":
                return
            elif self._alias(reg) == "pc":
                self._next_pc = val
            else:
                self._r[reg] = val

        elif type(reg_or_addr) is Addr:
            addr: Addr = reg_or_addr
            if addr < 0 or addr + 4 > self._mem_size:
                raise RuntimeError(f"segment fault: 0x{addr:08x}")

            old_val: int = sum(self._m[addr + i] << (i * 8) for i in range(4))
            for i in range(4):
                self._m[addr + i] = (val >> (i * 8)) & 0xFF

        else:  # pragma: no cover
            assert False

        Log.tf(
            f"{self._fmt(reg_or_addr)} = [red]{old_val}[/red] -> {self._fmtv(val, 'green')}",
            tag="Runtime",
        )

    def _beq(self, src1: Reg, src2: Reg, off: Addr) -> None:
        if self[src1] == self[src2]:
            self._next_pc = self["pc"] + off

    def _bne(self, src1: Reg, src2: Reg, off: Addr) -> None:
        if self[src1] != self[src2]:
            self._next_pc = self["pc"] + off

    def _addi(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = self[src] + imm

    def _subi(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = self[src] - imm

    # todo: fact.a runs fine on n = 100... need to validate regs
    def _muli(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = self[src] * imm

    def _divi(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = self[src] // imm

    def _modi(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = self[src] % imm

    def _ori(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = self[src] | imm

    def _andi(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = self[src] & imm

    def _xori(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = self[src] ^ imm

    def _eqi(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = 1 if self[src] == imm else 0

    def _gti(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = 1 if self[src] > imm else 0

    def _gei(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = 1 if self[src] >= imm else 0

    def _lti(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = 1 if self[src] < imm else 0

    def _lei(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = 1 if self[src] <= imm else 0

    def _lsi(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = self[src] << imm

    def _rsi(self, dst: Reg, src: Reg, imm: int) -> None:
        self[dst] = self[src] >> imm

    def _l(self, dst: Reg, base: Reg, off: Addr) -> None:
        self[dst] = self[self[base] + off]

    def _s(self, src: Reg, base: Reg, off: Addr) -> None:
        self[self[base] + off] = self[src]

    def _add(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = self[src1] + self[src2]

    def _sub(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = self[src1] - self[src2]

    def _mul(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = self[src1] * self[src2]

    def _div(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = self[src1] // self[src2]

    def _mod(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = self[src1] % self[src2]

    def _or(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = self[src1] | self[src2]

    def _and(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = self[src1] & self[src2]

    def _xor(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = self[src1] ^ self[src2]

    def _eq(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = 1 if self[src1] == self[src2] else 0

    def _gt(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = 1 if self[src1] > self[src2] else 0

    def _ge(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = 1 if self[src1] >= self[src2] else 0

    def _lt(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = 1 if self[src1] < self[src2] else 0

    def _le(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = 1 if self[src1] <= self[src2] else 0

    def _ls(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = self[src1] << self[src2]

    def _rs(self, dst: Reg, src1: Reg, src2: Reg) -> None:
        self[dst] = self[src1] >> self[src2]

    def _j(self, off: Addr) -> None:
        self._next_pc = self["pc"] + off

    def _e(self) -> None:
        match self["a0"]:
            # print
            case 0:
                addr: Addr = self._r[MP0._unalias("a1")]
                while addr < len(self._m) and self._m[addr] != 0:
                    print(chr(self._m[addr]), end="")
                    addr += 1

                if addr == len(self._m) and self._m[-1] != 0:
                    # todo
                    raise RuntimeError(f"segment fault: 0x{addr:08x}")

            # read
            case 1:
                base: Addr = self._r[MP0._unalias("a1")]
                read: str = input()
                for off, c in enumerate(read):
                    if base + off >= len(self._m):
                        # todo
                        raise RuntimeError(f"segment fault: 0x{base:08x}")

                    self._m[base + off] = ord(c)

                if base + len(read) >= len(self._m):
                    # todo
                    raise RuntimeError(f"segment fault: 0x{base:08x}")

                # 0-terminate
                self._m[base + len(read)] = 0

            # stoi
            case 2:
                addr: Addr = self._r[MP0._unalias("a1")]
                int_str: str = ""
                while addr < len(self._m) and self._m[addr] != 0:
                    int_str += chr(self._m[addr])
                    addr += 1

                if addr == len(self._m) and self._m[-1] != 0:
                    # todo
                    raise RuntimeError(f"segment fault: 0x{addr:08x}")

                self["a0"] = int(int_str)

            # printi
            case 3:
                val: int = self._r[MP0._unalias("a1")]
                if val > (1 << 31):
                    val -= 1 << 32
                print(val, end="")

            # alloc
            # todo: better allocator
            case 4:
                size: int = self._r[MP0._unalias("a1")]
                if self._next_mem_alloc + size + self._stack_size >= self._mem_size:
                    # todo
                    raise RuntimeError("out of memory")

                self._r[MP0._unalias("a0")] = self._next_mem_alloc
                self._next_mem_alloc += size

            # free
            # no op for now
            # todo: better allocator
            case 5:
                # todo
                pass

            case _:
                # todo
                raise RuntimeError(f"invalid env call: {self['a0']}")

    def _eb(self) -> None:
        print(f"env break unimplemented")
