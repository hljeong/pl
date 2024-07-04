from __future__ import annotations
from dataclasses import dataclass

from common import Log, Bits

Reg = str

Addr = int


class RegFile(dict[Reg, int]):
    def __init__(self, regs: list[Reg]):
        super().__init__({reg: 0 for reg in regs})


class Mem(bytearray):
    def __init__(self, size: int):
        super().__init__([0] * size)


# i wonder if this much boilerplate is needed...
class Ins(bytearray):
    @dataclass(frozen=True)
    class Frag:
        value: int = 0
        bitwidth: int = 0
        signed: bool = False

        @property
        def nominal_value(self) -> int:
            return (
                (
                    (1 << (self.bitwidth - 1)) - self.value
                    if self.signed and self.value < 0
                    else self.value
                )
                if self.bitwidth > 0
                else 0
            )

        def __post_init__(self) -> None:
            if self.nominal_value < 0 or self.nominal_value >= (1 << self.bitwidth):
                raise ValueError(f"incompatible value and bitwidth: {self}")

        def __str__(self) -> str:
            if not self.bitwidth:
                return "Frag<0>"

            # https://stackoverflow.com/a/29044976
            return "Frag<{bitwidth}>[{nominal:^{fmt}} ({value}{suffix})]".format(
                bitwidth=self.bitwidth,
                nominal=self.nominal_value,
                fmt=f"0{self.bitwidth}b",
                value=self.value,
                suffix="" if self.signed else "u",
            )

        def __call__(self, n_bytes: int = 4) -> Ins:
            if self.bitwidth != 8 * n_bytes:
                raise ValueError(
                    f"invalid bitwidth: {self.bitwidth}, expected {8 * n_bytes}"
                )

            return Ins(self)

        def __add__(self, other: Ins.Frag) -> Ins.Frag:
            frag: Ins.Frag = Ins.Frag(
                (self.nominal_value << other.bitwidth) | other.nominal_value,
                self.bitwidth + other.bitwidth,
            )
            Log.w(
                f"fragment concatenation crosses byte boundary: {self} + {other} = {frag}",
                frag.bitwidth % 8 != 0 and (frag.bitwidth // 8) > (self.bitwidth // 8),
            )
            return frag

    def __init__(self, frag: Ins.Frag) -> None:
        if frag.bitwidth % 8 != 0:
            raise ValueError(f"fragment represents partial bytes: {frag}")
        super().__init__(
            [
                (frag.value >> (i * 8)) & ((1 << 8) - 1)
                for i in range(frag.bitwidth // 8)
            ]
        )
        self._frag: Ins.Frag = frag

    @property
    def bits(self) -> Bits:
        return Bits(
            self._frag.value,
            self._frag.bitwidth,
        )


Prog = bytearray
