from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias
import re


def regularize(code: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", code)


def join(statements: list[Statement]) -> str:
    return regularize("\n".join([str(statement) for statement in statements]))


def sep_join(statements: list[Statement]) -> str:
    return regularize("\n\n".join([str(statement) for statement in statements]))


def block(statements: list[Statement]) -> str:
    return indent(join(statements) if statements else "pass")


def indent(code: str) -> str:
    return join(
        ["" if line.strip() == "" else f"    {line}" for line in code.split("\n")]
    )


@dataclass
class Statements:
    statements: list[Statement] = field(default_factory=list)

    def __str__(self) -> str:
        return join(self.statements)

    def __iadd__(self, statement: Statement):
        self.statements.append(statement)
        return self


@dataclass
class If:
    cond: str
    statements: list[Statement] = field(default_factory=list)

    def __str__(self) -> str:
        return join(
            [
                f"if {self.cond}:",
                block(self.statements),
            ]
        )

    def __iadd__(self, statement: Statement):
        self.statements.append(statement)
        return self


@dataclass
class For:
    item: str
    collection: str
    statements: list[Statement] = field(default_factory=list)

    def __str__(self) -> str:
        return join(
            [
                f"for {self.item} in {self.collection}:",
                block(self.statements),
            ]
        )

    def __iadd__(self, statement: Statement):
        self.statements.append(statement)
        return self


@dataclass
class While:
    cond: str
    statements: list[Statement] = field(default_factory=list)

    def __str__(self) -> str:
        return join(
            [
                f"while {self.cond}:",
                block(self.statements),
            ]
        )

    def __iadd__(self, statement: Statement):
        self.statements.append(statement)
        return self


@dataclass
class Class:
    name: str
    dataclass: bool = False
    base: str | None = None
    statements: list[Statement] = field(default_factory=list)

    def __str__(self) -> str:
        lines: list[str] = []

        if self.dataclass:
            lines.append("@dataclass")

        if self.base:
            lines.append(f"class {self.name}({self.base}):")
        else:
            lines.append(f"class {self.name}:")

        lines.append(block(self.statements))

        return "\n".join(lines)

    def __iadd__(self, statement: Statement):
        self.statements.append(statement)
        return self


@dataclass
class Try:
    statements: list[Statement] = field(default_factory=list)

    def __str__(self) -> str:
        lines: list[str] = ["try:"]
        lines.append(block(self.statements))
        return "\n".join(lines)

    def __iadd__(self, statement: Statement):
        self.statements.append(statement)
        return self


@dataclass
class Except:
    exc_type: str
    statements: list[Statement] = field(default_factory=list)

    def __str__(self) -> str:
        lines: list[str] = [f"except {self.exc_type}:"]
        lines.append(block(self.statements))
        return "\n".join(lines)

    def __iadd__(self, statement: Statement):
        self.statements.append(statement)
        return self


@dataclass
class Function:
    name: str
    arguments: str = ""
    return_type: str | None = None
    statements: list[Statement] = field(default_factory=list)

    def __str__(self) -> str:
        lines: list[str] = []

        if self.return_type:
            lines.append(f"def {self.name}({self.arguments}) -> {self.return_type}:")
        else:
            lines.append(f"def {self.name}({self.arguments}):")

        lines.append(block(self.statements))

        return "\n".join(lines)

    def __iadd__(self, statement: Statement):
        self.statements.append(statement)
        return self


@dataclass
class Python:
    statements: list[Statement] = field(default_factory=list)

    def __str__(self) -> str:
        return join(self.statements)

    def __iadd__(self, statement: Statement):
        self.statements.append(statement)
        return self


Statement: TypeAlias = (
    str | Statements | Class | Function | If | For | While | Try | Except
)
