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

with open("langs/b/spec/b.xbnf") as b_xbnf_f:
    b_xbnf = "".join(b_xbnf_f.readlines())

b_grammar = Grammar("b", b_xbnf)


class BParser:
    def __call__(self, prog) -> ASTNode:
        return Monad(prog).then(Lexer(b_grammar)).then(Parser(b_grammar)).value


class BPrinter(Visitor):
    def __init__(self):
        super().__init__(
            default_nonterminal_node_visitor=Visitor.visit_all(join),
            default_terminal_node_visitor=lambda _, n: n.lexeme,
        )

    def _visit_block(
        self,
        n: ChoiceNonterminalASTNode,
    ) -> str:
        match n.choice:
            # <block> ::= <statement>;
            case 0:
                return self(n[0])

            # <block> ::= "{" <statements> "}";
            case 1:
                return join("{", tabbed(self(n[1])), "}")

        assert False

    def _visit_statement(
        self,
        n: ChoiceNonterminalASTNode,
    ) -> str:
        match n.choice:
            # <statement> ::= <variable> "=" (<operand> | <expression> | <mem_access> | "alloc" "\(" <variable> "\)" | "free" "\(" <variable> "\)" | "stoi" "\(" <variable> "\)") ";";
            case 0:
                # todo: review cast
                match cast(ChoiceNonterminalASTNode, n[2]).choice:
                    # <operand> | <expression> | <mem_access>
                    case 0 | 1 | 2:
                        # todo: review cast
                        return (
                            f"{self(n[0])} = {self(cast(NonterminalASTNode, n[2])[0])};"
                        )

                    # "alloc" "\(" <variable> "\)" | "free" "\(" <variable> "\)" | "stoi" "\(" <variable> "\)"
                    case 3 | 4 | 5:
                        # todo: annotation
                        return f"{self(n[0])} = {n[2][0].lexeme}({self(n[2][2])});"

            # <statement> ::= ("print" | "printi" | "read") "\(" <variable> "\)" ";";
            case 1:
                # todo: review casts
                return f"{cast(TerminalASTNode, cast(NonterminalASTNode, n[0])[0]).lexeme}({self(cast(NonterminalASTNode, n[2])[0])});"

            # <statement> ::= "while" "\(" <expression> "\)" <block>;
            case 2:
                # todo: review cast
                # <block> ::= <statement> | "{" <statement>* "}";
                match cast(ChoiceNonterminalASTNode, n[4]).choice:
                    # <block> ::= <statement>;
                    case 0:
                        return join(
                            f"while ({self(n[2])}) {{",
                            tabbed(self(n[4])),
                            "}",
                        )

                    # <block> ::= "{" <statement>* "}";
                    case 1:
                        return f"while ({self(n[2])}) {self(n[4])}"

            # <statement> ::= "if" "\(" <expression> "\)" <block>;
            case 3:
                # todo: review cast
                # <block> ::= <statement> | "{" <statement>* "}";
                match cast(ChoiceNonterminalASTNode, n[4]).choice:
                    # <block> ::= <statement>;
                    case 0:
                        return join(
                            f"if ({self(n[2])}) {{",
                            tabbed(self(n[4])),
                            "}",
                        )

                    # <block> ::= "{" <statement>* "}";
                    case 1:
                        return f"if ({self(n[2])}) {self(n[4])}"

            # <statement> ::= <mem_access> "=" <variable> ";";
            case 4:
                return f"{self(n[0])} = {self(n[2])};"

        assert False

    # todo: casting from here down
    def _visit_expression(
        self,
        n: ASTNode,
    ) -> str:
        match n.choice:
            # <expression> ::= <unary_operator> <operand>;
            case 0:
                return f"{self(n[0])}{self(n[1])}"

            # <expression> ::= <operand> <binary_operator> <operand>;
            case 1:
                return f"{self(n[0])} {self(n[1])} {self(n[2])}"

        assert False

    def _visit_mem_access(
        self,
        n: ASTNode,
    ) -> str:
        return f"[{self(n[1])} + {self(n[3])}]"


# pass for aggregating string constants...
# might just be a construct created by myself
class BAggregator(Visitor):
    def __init__(self):
        super().__init__()

    def _visit_b(self, n: ASTNode) -> dict[str, int]:
        self._constant_aggregate: dict[str, int] = {}
        self._constant_idx: int = 0
        self(n[0])
        return self._constant_aggregate

    def _visit_string(self, n: ASTNode) -> Any:
        self._constant_aggregate[n[0].literal] = self._constant_idx
        self._constant_idx += 1


class BAllocator(Visitor):
    str_buffer_len = 32

    def __init__(self):
        super().__init__()
        self._alloc: dict[str, int] = {}
        self._next_reg_alloc: int = 0

    def _visit_b(self, n: ASTNode) -> Any:
        self._builtin_visit_all(n)
        return self._alloc

    def _visit_variable(self, n: ASTNode) -> Any:
        varname: str = n[0].lexeme
        if varname not in self._alloc:
            self._alloc[varname] = self._next_reg_alloc
            self._next_reg_alloc += 1


class BCompiler(Visitor):
    def __init__(
        self, constant_aggregate: dict[str, int], symbol_table: dict[str, int]
    ):
        super().__init__(
            default_nonterminal_node_visitor=Visitor.visit_all(join),
        )
        self._c: dict[str, int] = constant_aggregate
        self._a: dict[str, int] = symbol_table

    # todo: incredibly ugly
    def _generate_data_section(self) -> str:
        constant_string: list[str] = [""] * len(self._c)
        for s in self._c:
            constant_string[self._c[s]] = f'"{s}"'

        return join(".data", tabbed(join(constant_string)))

    def _label(self) -> str:
        label = f"l{self._label_num}"
        self._label_num += 1
        return label

    def _visit_b(self, n: ASTNode) -> str:
        self._label_num: int = 0
        return join(
            self._generate_data_section(),
            join(".code", tabbed(join(self(n[0]), "exitv 0"))),
        )

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
                return tabbed(self(n[1]))

    def _visit_statement(
        self,
        n: Node,
    ) -> Any:
        match n.choice:
            # <statement> ::= <variable> "=" (<operand> | <expression> | <mem_access> | "alloc" "\(" <variable> "\)" | "free" "\(" <variable> "\)" | "stoi" "\(" <variable> "\)") ";";
            case 0:
                varname: str = n[0][0].lexeme
                main_course: str = ""
                dessert: str = (
                    f"store t0 sp {self._a[varname]} # [sp + alloc[{varname}]] = t0"
                )
                match n[2].choice:
                    # <operand> ::= <variable> | <string> | decimal_integer;
                    case 0:
                        # todo: there has to be a better way...
                        match n[2][0].choice:
                            # <operand> ::= <variable>;
                            case 0:
                                main_course = f"{self(n[2][0]).format('t0')} # t0 = [sp + alloc[{n[2][0][0][0].lexeme}]];"

                            # <operand> ::= <string>;
                            case 1:
                                main_course = f"{self(n[2][0]).format('t0')} # t0 = {n[2][0][0][0].lexeme};"

                            # <operand> ::= decimal_interger;
                            case 2:
                                main_course = (
                                    f"setv t0 {self(n[2][0])} # t0 = {self(n[2][0])};"
                                )

                    # <expression>
                    case 1:
                        main_course = self(n[2][0])

                    # <mem_access> ::= "\[" <variable> "+" decimal_integer "\]";
                    case 2:
                        main_course = join(
                            f"load t1 r1 {self._a[n[2][0][1][0].lexeme]} # t1 = [sp + alloc[{n[2][0][1][0].lexeme}]];",
                            f"load t0 t1 {n[2][0][3].lexeme} # t0 = [t1 + {n[2][0][3].lexeme}]",
                        )

                    # todo: wait free() does not belong here lol
                    # "alloc" "\(" <variable> "\)" | "free" "\(" <variable> "\)"
                    case 3 | 4:
                        # somehow n[2].choice works here...
                        # ^ no longer true but only shifted by 1
                        main_course = join(
                            f"load a0 r1 {self._a[n[2][2][0].lexeme]} # a0 = [sp + alloc[{n[2][2][0].lexeme}]];",
                            f"sysv {n[2].choice + 1} # a0 = {n[2][0].lexeme}(a0);",
                            f"set t0 a0 # t0 = a0;",
                        )

                    # "stoi" "\(" <variable> "\)"
                    case 5:
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
                start_label: str = self._label()
                end_label: str = self._label()
                main_course: str = tabbed(self(n[4]))
                appetizer: str = join(
                    f"{start_label}:",
                    self(n[2]),
                    f"eqv t0 t0 0 # t0 = (t0 == 0);",
                    f"jumpifv {end_label} t0 # if (t0) goto {end_label};",
                )
                dessert: str = join(
                    f"jumpv {start_label} # goto {start_label};",
                    f"{end_label}:",
                )

                return join(appetizer, main_course, dessert)

            # <statement> ::= "if" "\(" <expression> "\)" <block>;
            case 3:
                label: str = self._label()
                main_course: str = tabbed(self(n[4]))
                appetizer: str = join(
                    self(n[2]),
                    f"eqv t0 t0 0 # t0 = (t0 == 0);",
                    f"jumpifv {label} t0 # if (t0) goto {label};",
                )
                dessert: str = f"{label}:"

                return join(appetizer, main_course, dessert)

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
                    val: int = int(self(n[1]))
                    val = 1 if val == 0 else 0
                    return f"setv t0 {val}"

                else:
                    # todo: optimize constant
                    return join(self(n[1]).format("t1"), f"neqv t0 t1 0")

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

                    lop_val: int = int(self(lop))
                    rop_val: int = int(self(rop))
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
                        f"{self(lop).format('t1')} # t1 = [sp + alloc[{lop[0][0].lexeme}]]"
                        if lop.choice == 0
                        else f"setv t1 {self(lop)} # t1 = {self(lop)};"
                    ),
                    (
                        f"{self(rop).format('t2')} # t2 = [sp + alloc[{rop[0][0].lexeme}]]"
                        if rop.choice == 0
                        else f"setv t2 {self(rop)} # t2 = {self(rop)};"
                    ),
                    f"{inst} t0 t1 t2 # t0 = {inst}(t1, t2);",
                )

    def _visit_operand(self, n: ASTNode) -> Any:
        # <operand> ::= <variable> | decimal_integer;
        match n.choice:
            # <operand> ::= <variable>;
            case 0:
                return f"load {{}} r1 {self._a[n[0][0].lexeme]}"

            # <operand> ::= <string>;
            case 1:
                return f"addv {{}} pc ={self._c[n[0][0].literal]}"

            # <operand> ::= decimal_integer;
            case 2:
                return n[0].lexeme
