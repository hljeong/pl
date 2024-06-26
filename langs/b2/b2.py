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
    TerminalASTNode,
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
                "<block>": self._visit_block,
                "<statement>": self._visit_statement,
                "<expression>": self._visit_expression,
                "<mem_access>": self._visit_mem_access,
            },
            default_nonterminal_node_visitor=Visitor.visit_all(self, join),
            default_terminal_node_visitor=lambda n: n.lexeme,
        )

    def print(self, ast: ASTNode) -> str:
        return self.visit(ast)

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
                return join("{", tabbed(self.visit(n[1])), "}")

        assert False

    def _visit_statement(
        self,
        n: ChoiceNonterminalASTNode,
    ) -> str:
        match n.choice:
            # <statement> ::= <variable> "=" (<operand> | <expression> | <string> | <mem_access> | "alloc" "\(" <variable> "\)" | "free" "\(" <variable> "\)" | "stoi" "\(" <variable> "\)") ";";
            case 0:
                # todo: review cast
                match cast(ChoiceNonterminalASTNode, n[2]).choice:
                    # <operand> | <expression> | <string> | <mem_access>
                    case 0 | 1 | 2 | 3:
                        # todo: review cast
                        return f"{self.visit(n[0])} = {self.visit(cast(NonterminalASTNode, n[2])[0])};"

                    # "alloc" "\(" <variable> "\)" | "free" "\(" <variable> "\)" | "stoi" "\(" <variable> "\)"
                    case 4 | 5 | 6:
                        # todo: annotation
                        return f"{self.visit(n[0])} = {n[2][0].lexeme}({self.visit(n[2][2])});"

            # <statement> ::= ("print" | "printi" | "read") "\(" <variable> "\)" ";";
            case 1:
                # todo: review casts
                return f"{cast(TerminalASTNode, cast(NonterminalASTNode, n[0])[0]).lexeme}({self.visit(cast(NonterminalASTNode, n[2])[0])});"

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

            # <statement> ::= <mem_access> "=" <variable> ";";
            case 4:
                return f"{self.visit(n[0])} = {self.visit(n[2])};"

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

    def _visit_mem_access(
        self,
        n: ASTNode,
    ) -> str:
        return f"[{self.visit(n[1])} + {self.visit(n[3])}]"


class B2Allocator(Visitor):
    str_buffer_len = 32

    def __init__(self):
        super().__init__(
            {
                # magical default visitor machinery handles everything :DDD
                "<variable>": self._visit_variable,
            },
        )
        self._alloc: dict[str, int] = {}
        self._next_reg_alloc: int = 0

    def allocate(self, ast: ASTNode) -> dict[str, int]:
        self._alloc: dict[str, int] = {}
        self._next_reg_alloc: int = 0
        self.visit(ast)
        return self._alloc

    def _visit_b2(self, n: ASTNode) -> Any:
        self._builtin_visit_all(n)
        return self._alloc

    def _visit_variable(self, n: ASTNode) -> Any:
        varname: str = n[0].lexeme
        if varname not in self._alloc:
            self._alloc[varname] = self._next_reg_alloc
            self._next_reg_alloc += 1


class B2Compiler(Visitor):
    def __init__(self, symbol_table: dict[str, int]):
        super().__init__(
            {
                "<b2>": self._visit_b2,
                "<block>": self._visit_block,
                "<statement>": self._visit_statement,
                "<expression>": self._visit_expression,
                "<operand>": self._visit_operand,
            },
            default_nonterminal_node_visitor=Visitor.visit_all(join),
        )
        self._a: dict[str, int] = symbol_table

    def compile(self, ast: ASTNode) -> str:
        self._a: dict[str, int] = B2Allocator().allocate(ast)
        return join(self.visit(ast), "exitv 0")

    def _init(self, n: ASTNode) -> None:
        self._a: dict[str, int] = B2Allocator().allocate(n)

    def _visit_b2(self, n: ASTNode) -> str:
        return join(self.visit(n[0]), "exitv 0")

    def _visit_block(
        self,
        n: Node,
    ) -> Any:
        match n.choice:
            # <block> ::= <statement>*;
            case 0:
                return self(n[0])

            # <block> ::= "{" <statement>* "}";
            case 1:
                return tabbed(self.visit(n[1]))

    def _visit_statement(
        self,
        n: Node,
    ) -> Any:
        match n.choice:
            # <statement> ::= <variable> "=" (<operand> | <expression> | <string> | <mem_access> | "alloc" "\(" <variable> "\)" | "free" "\(" <variable> "\)" | "stoi" "\(" <variable> "\)") ";";
            case 0:
                varname: str = n[0][0].lexeme
                main_course: str = ""
                dessert: str = (
                    f"store t0 sp {self._a[varname]} # [sp + alloc[{varname}]] = t0"
                )
                match n[2].choice:
                    # <operand> ::= <variable> | decimal_integer;
                    case 0:
                        # todo: there has to be a better way...
                        match n[2][0].choice:
                            # <operand> ::= <variable>;
                            case 0:
                                main_course = f"{self.visit(n[2][0]).format('t0')} # t0 = [sp + alloc[{n[2][0][0][0].lexeme}]];"

                            # <operand> ::= decimal_interger;
                            case 1:
                                main_course = f"setv t0 {self.visit(n[2][0])} # t0 = {self.visit(n[2][0])}"

                    # <expression>
                    case 1:
                        main_course = self.visit(n[2][0])

                    # <string>
                    case 2:
                        literal: str = n[2][0][0].literal

                        # todo: so ugly...
                        # todo: cleanly combine code and comment
                        # todo: switch to using data segment
                        main_course = join(
                            f"setv a0 {len(literal) + 1} # a0 = {len(literal) + 1};",
                            "sysv 4 # a0 = alloc(a0);",
                            f"set t0 a0 # t0 = a0;",
                            join(
                                join(
                                    f"setv t1 {ord(literal[i])} # t1 = '{literal[i]}'",
                                    f"store t1 t0 {i} # [t0 + {i}] = t1;",
                                )
                                for i in range(len(literal))
                            ),
                            f"store r0 t0 {len(literal)} # [t0 + {len(literal)}] = 0;",
                        )

                    # <mem_access> ::= "\[" <variable> "+" decimal_integer "\]";
                    case 3:
                        main_course = join(
                            f"load t1 r1 {self._a[n[2][0][1][0].lexeme]} # t1 = [sp + alloc[{n[2][0][1][0].lexeme}]];",
                            f"load t0 t1 {n[2][0][3].lexeme} # t0 = [t1 + {n[2][0][3].lexeme}]",
                        )

                    # todo: wait free() does not belong here lol
                    # "alloc" "\(" <variable> "\)" | "free" "\(" <variable> "\)"
                    case 4 | 5:
                        # somehow n[2].choice works here...
                        main_course = join(
                            f"load a0 r1 {self._a[n[2][2][0].lexeme]} # a0 = [sp + alloc[{n[2][2][0].lexeme}]];",
                            f"sysv {n[2].choice} # a0 = {n[2][0].lexeme}(a0);",
                            f"set t0 a0 # t0 = a0;",
                        )

                    # "stoi" "\(" <variable> "\)"
                    case 6:
                        main_course = join(
                            f"load a0 r1 {self._a[n[2][2][0].lexeme]} # a0 = [sp + alloc[{n[2][2][0].lexeme}]];",
                            f"sysv 2 # a1 = {n[2][0].lexeme}(a0);",
                            f"set t0 a1 # t0 = a1;",
                        )

                return join(main_course, dessert)

            # <statement> ::= ("print" | "printi" | "read") "\(" <variable> "\)" ";";
            case 1:
                appetizer = f"load t0 r1 {self._a[n[2][0].lexeme]} # t0 = [sp + alloc[{n[2][0].lexeme}]];"
                main_course: str = ""
                # "print" | "printi" | "read"
                match n[0].choice:
                    # "print"
                    case 0:
                        main_course = join(
                            f"set a0 t0 # a0 = t0;",
                            "sysv 0 # print(a0);",
                        )

                    # "printi"
                    case 1:
                        main_course = join(
                            f"set a0 t0 # a0 = t0;",
                            "sysv 3 # printi(a0);",
                        )

                    # "read"
                    case 2:
                        main_course = join(
                            f"set a0 t0 # a0 = t0;",
                            "sysv 1 # a0 = read(a0);",
                        )

                return join(appetizer, main_course)

            # <statement> ::= "while" "\(" <expression> "\)" <block>;
            case 2:
                main_course: str = tabbed(self.visit(n[4]))
                appetizer: str = join(
                    self.visit(n[2]),
                    f"eqv t0 t0 0 # t0 = (t0 == 0);",
                    f"jumpifv {count_lines(main_course) + 2} t0 # if (t0) jumpv({count_lines(main_course) + 2});",
                )
                dessert: str = (
                    f"jumpv {-(count_lines(main_course) + count_lines(appetizer))} # jumpv({-(count_lines(main_course) + count_lines(appetizer))});"
                )

                return join(appetizer, main_course, dessert)

            # <statement> ::= "if" "\(" <expression> "\)" <block>;
            case 3:
                main_course: str = tabbed(self.visit(n[4]))
                appetizer: str = join(
                    self.visit(n[2]),
                    f"eqv t0 t0 0 # t0 = (t0 == 0);",
                    f"jumpifv {count_lines(main_course) + 1} t0 # if (t0) jumpv({count_lines(main_course) + 1});",
                )

                return join(appetizer, main_course)

            # <statement> ::= <mem_access> "=" <variable> ";";
            case 4:
                return join(
                    f"load t0 r1 {self._a[n[0][1][0].lexeme]} # t0 = [sp + alloc[{self._a[n[0][1][0].lexeme]}]];",
                    f"load t1 r1 {self._a[n[2][0].lexeme]} # t1 = [sp + alloc[{self._a[n[2][0].lexeme]}]];",
                    f"store t1 t0 {n[0][3].lexeme} # [t0 + {n[0][3].lexeme}] = t1;",
                )

    def _visit_expression(self, n: ASTNode) -> Any:
        match n.choice:
            # <unary_operator> <operand>
            case 0:
                # constant expression optimization
                if n[1].choice == 1:
                    val: int = int(self.visit(n[1]))
                    val = 1 if val == 0 else 0
                    return f"setv t0 {val}"

                else:
                    # todo: optimize constant
                    return join(self.visit(n[1]).format("t1"), f"neqv t0 t1 0")

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
                    return f"setv t0 {val} # t0 = {val};"

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

                # todo: fix lazy comment (print it as binary operation)
                # todo: constant optimizations
                # todo: very very sloppy
                return join(
                    (
                        f"{self.visit(lop).format('t1')} # t1 = [sp + alloc[{lop[0][0].lexeme}]]"
                        if lop.choice == 0
                        else f"setv t1 {self.visit(lop)} # t1 = {self.visit(lop)};"
                    ),
                    (
                        f"{self.visit(rop).format('t2')} # t2 = [sp + alloc[{rop[0][0].lexeme}]]"
                        if rop.choice == 0
                        else f"setv t2 {self.visit(rop)} # t2 = {self.visit(rop)};"
                    ),
                    f"{inst} t0 t1 t2 # t0 = {inst}(t1, t2);",
                )

    def _visit_operand(self, n: ASTNode) -> Any:
        # <operand> ::= <variable> | decimal_integer;
        match n.choice:
            # <operand> ::= <variable>;
            case 0:
                return f"load {{}} r1 {self._a[n[0][0].lexeme]}"

            # <operand> ::= decimal_integer;
            case 1:
                return n[0].lexeme
