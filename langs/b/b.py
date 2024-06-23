from __future__ import annotations
from platform import node
from typing import Generic, TypeVar, Any

from common import Monad, Log, tabbed, join, count_lines
from lexical import Lexer
from syntax import Grammar, Parser, Visitor, ASTNode
from syntax.ast import ChoiceNonterminalASTNode

with open("langs/b/spec/b.xbnf") as b_xbnf_f:
    b_xbnf = "".join(b_xbnf_f.readlines())
b_grammar = Grammar("b", b_xbnf)


class BParser:
    def parse(self, prog: str):
        return (
            Monad(prog).then(Lexer(b_grammar).lex).then(Parser(b_grammar).parse).value
        )


class BPrinter(Visitor):
    def __init__(self):
        super().__init__(
            {
                "<b>": self._visit_b,
                "<block>": self._visit_block,
                "<statement>": self._visit_statement,
                "<expression>": self._visit_expression,
            },
            default_terminal_node_visitor=lambda n: n.lexeme,
        )

    def print(self, ast: ASTNode) -> str:
        return self.visit(ast)

    def _visit_b(
        self,
        n: ASTNode,
    ) -> str:
        prog: str = join(self.visit(c) for c in n[0])
        return prog

    def _visit_block(
        self,
        n: ASTNode,
    ) -> str:
        match n.choice:
            # <block> ::= <statement>;
            case 0:
                return self.visit(n[0])

            # <block> ::= "{" <statements> "}";
            case 1:
                inner_prog: str = tabbed(join(self.visit(c) for c in n[1]))

                return join("{", inner_prog, "}")

        assert False

    def _visit_statement(
        self,
        n: ASTNode,
    ) -> str:
        match n.choice:
            # <statement> ::= <variable> "=" (<operand> | <expression> | <string>) ";" |
            case 0:
                return f"{self.visit(n[0])} = {self.visit(n[2][0])};"

            # <statement> ::= ("print" | "printi" | "read" | "readi") "\(" <variable> "\)" ";" |
            case 1:
                return f"{Visitor.telescope(n[0]).lexeme}({self.visit(n[2][0])})"

            # <statement> ::= "while" "\(" <expression> "\)" <block>;
            case 2:
                # <block> ::= <statement> | "{" <statement>* "}";
                match n[4].choice:
                    # <block> ::= <statement>;
                    case 0:
                        return join(
                            f"while ({self.visit(n[2])}) {{",
                            tabbed(self.visit(n[4])),
                            "}",
                        )

                    # <block> ::= "{" <statement>* "}";
                    case 1:
                        return f"while ({self.visit(n[2])}) {self.visit(n[4])}"

            # <statement> ::= "if" "\(" <expression> "\)" <block>;
            case 3:
                # <block> ::= <statement> | "{" <statement>* "}";
                match n[4].choice:
                    # <block> ::= <statement>;
                    case 0:
                        return join(
                            f"if ({self.visit(n[2])}) {{",
                            tabbed(self.visit(n[4])),
                            "}",
                        )

                    # <block> ::= "{" <statement>* "}";
                    case 1:
                        return f"if ({self.visit(n[2])}) {self.visit(n[4])}"

        assert False

    def _visit_expression(
        self,
        n: ASTNode,
    ) -> str:
        match n.choice:
            # <expression> ::= <unary_operator> <operand>;
            case 0:
                return f"{self.visit(n[0])}{self.visit(n[1])}"

            # <expression> ::= <operand> <binary_operator> <operand>;
            case 1:
                return f"{self.visit(n[0])} {self.visit(n[1])} {self.visit(n[2])}"

        assert False


class BAllocator(Visitor):
    str_buffer_len = 32

    def __init__(self):
        super().__init__(
            {
                "<b>": self._visit_b,
                "<block>": self._visit_block,
                "<statement>": self._visit_statement,
                "<expression>": self._visit_expression,
                "<variable>": self._visit_variable,
            },
        )
        self._reserve: dict[str, int] = {}

    def allocate(self, ast: ASTNode) -> dict[str, int]:
        self._reserve = {}
        self.visit(ast)
        self._var("#tmp")
        return self._allocate()

    def _allocate(self) -> dict[str, int]:
        alloc: dict[str, int] = {}
        next: int = 0
        for varname, size in self._reserve.items():
            alloc[varname] = next
            next += size
        return alloc

    def _var(self, varname: str, size: int = 1):
        if varname not in self._reserve or size > self._reserve[varname]:
            self._reserve[varname] = size

    def _visit_b(
        self,
        n: Node,
    ) -> Any:
        for c in n[0]:
            self.visit(c)

    def _visit_block(
        self,
        n: Node,
    ) -> Any:
        match n.choice:
            # <block> ::= <statement>;
            case 0:
                self.visit(n[0])

            # <block> ::= "{" <statements> "}";
            case 1:
                for c in n[1]:
                    self.visit(c)

    def _visit_statement(
        self,
        n: ASTNode,
    ) -> Any:
        match n.choice:
            # <statement> ::= <variable> "=" (<operand> | <expression> | <string>) ";";
            case 0:
                self.visit(n[0])

                match n[2].choice:
                    # <operand> | <expression>
                    case 0 | 1:
                        self.visit(n[2][0])

                    # <string>
                    case 2:
                        self._var(n[0][0].lexeme, BAllocator.str_buffer_len)

            # <statement> ::= ("print" | "printi" | "read" | "readi") "\(" <variable> "\)" ";";
            case 1:
                varname: str = n[2][0].lexeme

                match n[0].choice:
                    # "print" | "read"
                    case 0 | 2:
                        self._var(f"&{varname}")
                        self._var(varname, BAllocator.str_buffer_len)

                    # "printi" | "readi"
                    case 1 | 3:
                        self._var(f"&{varname}")
                        self._var(varname)

            # <statement> ::= "while" "\(" <expression> "\)" <block> | "if" "\(" <expression> "\)" <block>;
            case 2 | 3:
                self.visit(n[2])
                self.visit(n[4])

    def _visit_expression(self, n: ASTNode) -> Any:
        match n.choice:
            # <expression> ::= <unary_operator> <operand>;
            case 0:
                self.visit(n[1])

            # <expression> ::= <operand> <binary_operator> <operand>;
            case 1:
                self.visit(n[0])
                self.visit(n[2])

    def _visit_variable(self, n: ASTNode) -> Any:
        self._var(n[0].lexeme)


class BCompiler(Visitor):
    def __init__(self):
        super().__init__(
            {
                "<b>": self._visit_b,
                "<block>": self._visit_block,
                "<statement>": self._visit_statement,
                "<expression>": self._visit_expression,
                "<operand>": self._visit_operand,
            },
        )

    def compile(self, ast: ASTNode) -> str:
        self._a = BAllocator().allocate(ast)
        return self.visit(ast)

    def _visit_b(
        self,
        n: Node,
    ) -> Any:
        return join(self.visit(c) for c in n[0])

    def _visit_block(
        self,
        n: Node,
    ) -> Any:
        match n.choice:
            # <block> ::= <statement>;
            case 0:
                return self.visit(n[0])

            # <block> ::= "{" <statements> "}";
            case 1:
                return tabbed(join(self.visit(c) for c in n[1]))

    def _visit_statement(
        self,
        n: Node,
    ) -> Any:
        match n.choice:
            # <statement> ::= <variable> "=" (<operand> | <expression> | <string>) ";"
            case 0:
                varname: str = n[0][0].lexeme
                match n[2].choice:
                    # <operand>
                    case 0:
                        return f"set{'' if n[2][0].choice == 0 else 'v'} {self._a[varname]} {self.visit(n[2][0])}"

                    # <expression>
                    case 1:
                        return self.visit(n[2][0]).format(self._a[varname])

                    # <string>
                    case 2:
                        literal: str = n[2][0][0].literal[
                            : BAllocator.str_buffer_len - 1
                        ]
                        Log.d(
                            join(
                                f"setv {self._a[varname] + i} {ord(literal[i])}"
                                for i in range(len(literal))
                            )
                        )

                        return join(
                            f"setv {self._a[varname] + i} {ord(literal[i])}"
                            for i in range(len(literal))
                        )

            # <statement> ::= ("print" | "printi" | "read" | "readi") "\(" <variable> "\)" ";";
            case 1:
                # "print" | "printi" | "read" | "readi"
                match n[0].choice:
                    # "print" | "printi"
                    case 0 | 1:
                        return join(
                            f"setv {self._a[f'&{n[2][0].lexeme}']} {self._a[n[2][0].lexeme]}",
                            f"{n[0][0].lexeme} {self._a[f'&{n[2][0].lexeme}']}",
                        )

                    # "read" | "readi"
                    case 2 | 3:
                        return join(
                            f"setv {self._a[f'&{n[2][0].lexeme}']} {self._a[n[2][0].lexeme]}",
                            f"{n[0][0].lexeme} {self._a[f'&{n[2][0].lexeme}']}",
                        )

            # <statement> ::= "while" "\(" <expression> "\)" <block>;
            case 2:
                payload: str = tabbed(self.visit(n[4]))
                preamble: str = join(
                    self.visit(n[2]).format(self._a["#tmp"]),
                    f"eqv {self._a['#tmp']} {self._a['#tmp']} 0",
                    f"jumpvif {count_lines(payload) + 2} {self._a['#tmp' ]}",
                )
                epilogue: str = f"jumpv {-(count_lines(payload) + 3)}"

                return join(preamble, payload, epilogue)

            # <statement> ::= "if" "\(" <expression> "\)" <block>;
            case 3:
                payload: str = tabbed(self.visit(n[4]))
                preamble: str = join(
                    self.visit(n[2]).format(self._a["#tmp"]),
                    f"eqv {self._a['#tmp']} {self._a['#tmp']} 0",
                    f"jumpvif {count_lines(payload) + 1} {self._a['#tmp' ]}",
                )

                return join(preamble, payload)

    def _visit_expression(self, n: ASTNode) -> Any:
        match n.choice:
            # <unary_operator> <operand>
            case 0:
                # constant expression optimization
                if n[1].choice == 1:
                    val: int = int(self.visit(n[1]))
                    val = 1 if val == 0 else 0
                    return f"setv {{}} {val}"

                # minimize instructions
                else:
                    return f"neqv {{}} {self.visit(n[1])} 0"

            # <operand> <binary_operator> <operand>
            case 1:
                lop: ASTNode = n[0]
                lop_choice: int = lop.choice
                rop: ASTNode = n[2]
                rop_choice: int = rop.choice

                # constant expression optimization
                if lop_choice == 1 and rop_choice == 1:
                    binop = {
                        # <binary_operator> ::= "\+";
                        0: lambda x, y: x + y,
                        # <binary_operator> ::= "-";
                        1: lambda x, y: x - y,
                        # <binary_operator> ::= "\*";
                        2: lambda x, y: x * y,
                        # <binary_operator> ::= "\|";
                        3: lambda x, y: x | y,
                        # <binary_operator> ::= "&";
                        4: lambda x, y: x & y,
                        # <binary_operator> ::= "==";
                        5: lambda x, y: x == y,
                        # <binary_operator> ::= "!=";
                        6: lambda x, y: x != y,
                        # <binary_operator> ::= ">";
                        7: lambda x, y: x > y,
                        # <binary_operator> ::= ">=";
                        8: lambda x, y: x >= y,
                        # <binary_operator> ::= "<";
                        9: lambda x, y: x < y,
                        # <binary_operator> ::= "<=";
                        10: lambda x, y: x <= y,
                    }[n[1].choice]

                    lop_val: int = int(self.visit(lop))
                    rop_val: int = int(self.visit(rop))
                    val: int = binop(lop_val, rop_val)
                    return f"setv {{}} {val}"

                inst = {
                    # <binary_operator> ::= "\+";
                    0: "add",
                    # <binary_operator> ::= "-";
                    1: "sub",
                    # <binary_operator> ::= "\*";
                    2: "mul",
                    # <binary_operator> ::= "\|";
                    3: "or",
                    # <binary_operator> ::= "&";
                    4: "and",
                    # <binary_operator> ::= "==";
                    5: "eq",
                    # <binary_operator> ::= "!=";
                    6: "neq",
                    # <binary_operator> ::= ">";
                    7: "gt",
                    # <binary_operator> ::= ">=";
                    8: "geq",
                    # <binary_operator> ::= "<";
                    9: "lt",
                    # <binary_operator> ::= "<=";
                    10: "leq",
                }[n[1].choice]

                # mixed operands
                if lop_choice != rop_choice:
                    # make rop constant
                    if lop_choice == 1:
                        lop, rop = rop, lop

                    return f"{inst}v {{}} {self.visit(lop)} {self.visit(rop)}"

                # both operands are variables
                else:
                    return f"{inst} {{}} {self.visit(lop)} {self.visit(rop)}"

    def _visit_operand(self, n: ASTNode) -> Any:
        # <operand> ::= <variable> | decimal_integer;
        match n.choice:
            # <operand> ::= <variable>;
            case 0:
                return self._a[n[0][0].lexeme]

            # <operand> ::= decimal_integer;
            case 1:
                return n[0].lexeme
