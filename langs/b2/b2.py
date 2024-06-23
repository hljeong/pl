from __future__ import annotations
from typing import cast, Any

from common import Monad, Log, tabbed, join, count_lines
from lexical import Lexer
from syntax import (
    Grammar,
    Parser,
    Visitor,
    ASTNode,
    NonterminalASTNode,
    ChoiceNonterminalASTNode,
)
from syntax.visitor import NonterminalASTNodeVisitor

with open("langs/b2/spec/b2.xbnf") as b2_xbnf_f:
    b2_xbnf = "".join(b2_xbnf_f.readlines())

b2_grammar = Grammar("b2", b2_xbnf)


class B2Parser:
    def parse(self, prog: str):
        return (
            Monad(prog).then(Lexer(b2_grammar).lex).then(Parser(b2_grammar).parse).value
        )


class B2Printer(Visitor):
    def __init__(self):
        super().__init__(
            {
                "<b2>": self._visit_b2,
                "<block>": self._visit_block,
                "<statement>": self._visit_statement,
                "<expression>": self._visit_expression,
            },
            default_terminal_node_visitor=lambda n: n.lexeme,
        )

    def print(self, ast: ASTNode) -> str:
        return self.visit(ast)

    def _visit_b2(
        self,
        n: NonterminalASTNode,
    ) -> str:
        # todo: review cast
        prog: str = join(self.visit(c) for c in cast(NonterminalASTNode, n[0]))
        return prog

    def _visit_block(
        self,
        n: ChoiceNonterminalASTNode,
    ) -> str:
        match n.choice:
            # <block> ::= <statement>;
            case 0:
                return self.visit(n[0])

            # <block> ::= "{" <statements> "}";
            case 1:
                inner_prog: str = tabbed(
                    # todo: review cast
                    join(self.visit(child) for child in cast(NonterminalASTNode, n[1]))
                )

                return join("{", inner_prog, "}")

        assert False

    def _visit_statement(
        self,
        n: ChoiceNonterminalASTNode,
    ) -> str:
        match n.choice:
            # <statement> ::= <variable> "=" (<operand> | <expression> | <string>) ";" |
            case 0:
                # todo: review cast
                return f"{self.visit(n[0])} = {self.visit(cast(NonterminalASTNode, n[2])[0])};"

            # <statement> ::= ("print" | "printi" | "read" | "readi") "\(" <variable> "\)" ";" |
            case 1:
                # todo: review casts
                return f"{cast(TerminalASTNode, cast(NonterminalASTNode, n[0])[0]).lexeme}({self.visit(cast(NonterminalASTNode, n[2])[0])})"

            # <statement> ::= "while" "\(" <expression> "\)" <block>;
            case 2:
                # todo: review cast
                # <block> ::= <statement> | "{" <statement>* "}";
                match cast(ChoiceNonterminalASTNode, n[4]).choice:
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
                # todo: review cast
                # <block> ::= <statement> | "{" <statement>* "}";
                match cast(ChoiceNonterminalASTNode, n[4]).choice:
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

    # todo: casting from here down
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


class B2Allocator(Visitor):
    str_buffer_len = 32

    def __init__(self):
        super().__init__(
            {
                "<b2>": self._visit_b2,
                "<block>": self._visit_block,
                "<statement>": self._visit_statement,
                "<expression>": self._visit_expression,
                "<variable>": self._visit_variable,
            },
        )
        self._reserve: dict[str, int] = {}

    def allocate(self, ast: ASTNode) -> tuple[dict[str, int], dict[int, int]]:
        self._reserve = {}
        self.visit(ast)
        self._var("#tmp")
        # todo: clean up
        a = self._allocate()
        Log.d(a)
        return a

    def _allocate(self) -> tuple[dict[str, int], dict[int, int]]:
        reg_alloc: dict[str, int] = {}
        mem_alloc: dict[int, int] = {}
        next_reg: int = 32
        next_mem_loc: int = 1
        for varname, vartype in self._reserve.items():
            reg_alloc[varname] = next_reg
            Log.d(f"variable {varname} has type {vartype}")
            if vartype == 1:
                mem_alloc[next_reg] = next_mem_loc
                next_mem_loc += B2Allocator.str_buffer_len
            next_reg += 1
        return (reg_alloc, mem_alloc)

    def _var(self, varname: str, vartype: int = 0):
        if varname not in self._reserve or vartype > self._reserve[varname]:
            self._reserve[varname] = vartype

    def _visit_b2(
        self,
        n: Node,
    ) -> Any:
        for child in n[0]:
            self.visit(child)

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
                for child in n[1]:
                    self.visit(child)

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
                        self._var(n[0][0].lexeme, vartype=1)

            # <statement> ::= ("print" | "printi" | "read" | "readi") "\(" <variable> "\)" ";";
            case 1:
                varname: str = n[2][0].lexeme

                match n[0].choice:
                    # "print" | "read"
                    case 0 | 2:
                        self._var(varname, 1)

                    # "printi" | "readi"
                    case 1 | 3:
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


class B2Compiler(Visitor):
    def __init__(self):
        super().__init__(
            {
                "<b2>": self._visit_b2,
                "<block>": self._visit_block,
                "<statement>": self._visit_statement,
                "<expression>": self._visit_expression,
                "<operand>": self._visit_operand,
            },
        )

    def compile(self, ast: ASTNode) -> str:
        # todo: type annotate this or fix this ugly thing
        self._ra, self._ma = B2Allocator().allocate(ast)
        self._a = {}
        for varname in self._ra:
            self._a[varname] = f"r{self._ra[varname]}"
        preamble: str = join(f"setv r{i} {self._ma[i]}" for i in self._ma)
        return join(preamble, self.visit(ast), "exitv 0")

    def _visit_b2(
        self,
        n: Node,
    ) -> Any:
        return join(self.visit(child) for child in n[0])

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
                return tabbed(join(self.visit(child) for child in n[1]))

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
                            : B2Allocator.str_buffer_len - 1
                        ]

                        # todo: so ugly...
                        # todo: cleanly combine code and comment
                        return join(
                            join(
                                join(
                                    f"setv {self._a['#tmp']} {ord(literal[i])} # store '{literal[i]}' in temp var",
                                    f"store {self._a['#tmp']} {self._a[varname]} {i} # store it at ({varname} + {i})",
                                )
                                for i in range(len(literal))
                            ),
                            f"store r0 {self._a[varname]} {len(literal)}",
                        )

            # <statement> ::= ("print" | "printi" | "read" | "readi") "\(" <variable> "\)" ";";
            case 1:
                # "print" | "printi" | "read" | "readi"
                match n[0].choice:
                    # "print"
                    case 0:
                        return join(
                            f"set r14 {self._a[n[2][0].lexeme]}",
                            "sysv 0",
                        )

                    # "printi"
                    case 1:
                        return join(
                            f"set r14 {self._a[n[2][0].lexeme]}",
                            "sysv 3",
                        )

                    # "read"
                    case 2:
                        return join(
                            f"set r14 {self._a[n[2][0].lexeme]}",
                            "sysv 1",
                        )

                    # todo: incredibly sloppy... and unsafe
                    # "readi"
                    case 3:
                        return join(
                            "setv r14 727",
                            "sysv 1",
                            "setv r14 727",
                            "sysv 2",
                            f"set {self._a[n[2][0].lexeme]} r15",
                        )

            # <statement> ::= "while" "\(" <expression> "\)" <block>;
            case 2:
                payload: str = tabbed(self.visit(n[4]))
                preamble: str = join(
                    f"{self.visit(n[2]).format(self._a['#tmp'])}        # while ({B2Printer().visit(n[2])})",
                    f"eqv {self._a['#tmp']} {self._a['#tmp']} 0",
                    f"jumpifv {count_lines(payload) + 2} {self._a['#tmp' ]}",
                )
                epilogue: str = (
                    f"jumpv {-(count_lines(payload) + 3)}        # end while ({B2Printer().visit(n[2])})"
                )

                return join(preamble, payload, epilogue)

            # <statement> ::= "if" "\(" <expression> "\)" <block>;
            case 3:
                payload: str = tabbed(self.visit(n[4]))
                preamble: str = join(
                    f"{self.visit(n[2]).format(self._a['#tmp'])}        # if ({B2Printer().visit(n[2])})",
                    f"eqv {self._a['#tmp']} {self._a['#tmp']} 0",
                    f"jumpifv {count_lines(payload) + 1} {self._a['#tmp' ]}",
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
