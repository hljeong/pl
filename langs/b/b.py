from __future__ import annotations
from typing import Any

from common import (
    Monad,
    tabbed,
    join,
    joini,
    sjoin,
    sjoini,
    opt_p,
)
from lexical import Lexer
from syntax import (
    Grammar,
    Parser,
    Visitor,
    ASTNode,
    NonterminalASTNode,
    ChoiceNonterminalASTNode,
)


class B:
    with open("langs/b/spec/b.xbnf") as xbnf_f:
        xbnf: str = xbnf_f.read()

    grammar: Grammar = Grammar.from_xbnf("b", xbnf, ignore=["#[^\n]*"])

    class Parse:
        def __call__(self, prog) -> ASTNode:
            return Monad(prog).then(Lexer(B.grammar)).then(Parser.for_lang(B)).value

    class BuildInternalAST(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.rebuild,
                default_terminal_node_visitor=lambda _, n: n,
            )

        def _visit_b(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<b>")
            main_fn_declared: bool = False
            declarations: dict[str, NonterminalASTNode] = {}
            for c in n[0]:
                declaration: NonterminalASTNode = self(c)
                fn_name: str = declaration[1].lexeme

                if fn_name in declarations:
                    # todo: log error
                    raise RuntimeError(f"function '{fn_name}' declared multiple times")

                if fn_name == "main":
                    if main_fn_declared:
                        # todo: log error
                        raise RuntimeError(
                            f"function '{fn_name}' declared multiple times"
                        )

                    n_.add(declaration)
                    main_fn_declared = True

                else:
                    declarations[fn_name] = declaration

            if not main_fn_declared:
                # todo: log error
                raise RuntimeError("main function not declared")

            for fn_name in declarations:
                n_.add(declarations[fn_name])

            return n_

        def _visit_argument_list(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<flattened_argument_list>")
            n_.add(self(n[0]))
            for c in n[1]:
                n_.add(self(c[1]))
            return n_

        def _visit_parameter_list(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<flattened_parameter_list>")
            n_.add(self(n[0]))
            for c in n[1]:
                n_.add(self(c[1]))
            return n_

    class Print(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.visit_all(joini),
                default_terminal_node_visitor=lambda _, n: n.lexeme,
            )

        def _visit_b(self, n: ASTNode) -> str:
            return sjoini(self(c) for c in n)

        def _visit_declaration(self, n: ASTNode) -> str:
            return f"fn {self(n[1])}({self(n[3])}) {self(n[5])}"

        def _visit_flattened_argument_list(self, n: ASTNode) -> str:
            return ", ".join(self(c) for c in n)

        def _visit_flattened_parameter_list(self, n: ASTNode) -> str:
            return ", ".join(self(c) for c in n)

        def _visit_block(
            self,
            n: ChoiceNonterminalASTNode,
        ) -> str:
            match n.choice:
                # <block> ::= <statement>;
                case 0:
                    return self(n[0])

                # <block> ::= "{" <statement>* "}";
                case 1:
                    inner: str = self(n[1])
                    if len(inner) == 0:
                        return "{}"

                    else:
                        return join("{", tabbed(inner), "}")

                case _:  # pragma: no cover
                    assert False

        def _visit_statement(
            self,
            n: ChoiceNonterminalASTNode,
        ) -> str:
            match n.choice:
                # <statement> ::= (<variable> | <array_access>) "=" (<operand> | <expression> | <mem_access> | "alloc" "\(" <operand> "\)" | "free" "\(" <operand> "\)" | "stoi" "\(" <operand> "\)" | <function> "\(" <flattened_parameter_list>? "\)") ";";
                case 0:
                    match n[2].choice:
                        # <operand> | <expression> | <mem_access>
                        case 0 | 1 | 2:
                            return f"{self(n[0])} = {self(n[2])};"

                        # "alloc" "\(" <operand> "\)" | "free" "\(" <operand> "\)" | "stoi" "\(" <operand> "\)" | <function> "\(" <flattened_parameter_list>? "\)"
                        case 3 | 4 | 5 | 6:
                            return f"{self(n[0])} = {self(n[2][0])}({self(n[2][2])});"

                        case _:  # pragma: no cover
                            assert False

                # <statement> ::= ("print" | "printi" | "read") "\(" <operand> "\)" ";" | <function> "\(" <flattened_argument_list>? "\)" ";";
                case 1 | 6:
                    return f"{self(n[0])}({self(n[2])});"

                # <statement> ::= "while" "\(" <expression> "\)" <block>;
                case 2:
                    return f"while ({self(n[2])}) {self(n[4])}"

                # <statement> ::= "if" "\(" <expression> "\)" <block>;
                case 3:
                    return f"if ({self(n[2])}) {self(n[4])}"

                # <statement> ::= <mem_access> "=" <variable> ";";
                case 4:
                    return f"{self(n[0])} = {self(n[2])};"

                # <statement> ::= "return" <operand>? ";";
                case 5:
                    return f"return{opt_p(' ', self(n[1]))};"

                case _:  # pragma: no cover
                    assert False

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

                case _:  # pragma: no cover
                    assert False

        def _visit_mem_access(
            self,
            n: ASTNode,
        ) -> str:
            return f"[{self(n[1])} + {self(n[3])}]"

        def _visit_array_access(
            self,
            n: ASTNode,
        ) -> str:
            return f"{self(n[0])}[{self(n[2])}]"

    # pass for aggregating string constants...
    # might just be a construct created by myself
    class Aggregate(Visitor):
        def __init__(self):
            super().__init__()

        def _visit_b(self, n: ASTNode) -> dict[str, str]:
            self._constant_aggregate: dict[str, str] = {}
            self._constant_idx: int = 0
            self._builtin_visit_all(n)
            return self._constant_aggregate

        def _visit_string(self, n: ASTNode) -> Any:
            if n.literal not in self._constant_aggregate:
                self._constant_aggregate[n.literal] = f"s{self._constant_idx}"
                self._constant_idx += 1

    class GenerateSymbolTable(Visitor):
        def __init__(self):
            super().__init__()

        def _fn_label(self) -> str:
            fn_label: str = f"f{self._fn_label_idx}"
            self._fn_label_idx += 1
            return fn_label

        def _visit_b(self, n: ASTNode) -> dict[str, dict[str, Any]]:
            self._symbol_table: dict[str, dict[str, Any]] = {}
            self._fn_label_idx: int = 0
            self._builtin_visit_all(n)
            return self._symbol_table

        def _visit_declaration(self, n: ASTNode) -> None:
            fn_name: str = n[1].lexeme
            # todo: no bueno, maybe implement visitor context
            self._current_locals: dict[str, int] = {}
            self._current_var_loc: int = 0
            self._current_extra_args: int = 0
            self._builtin_visit_all(n)

            saved: dict[str, int] = {}
            saved["ra"] = self._var()

            # todo: this shifting is kinda bad
            # allocate slots for extra arguments at on the bottom
            self._current_locals = {
                var_name: self._current_extra_args * 4 + var_loc
                for var_name, var_loc in self._current_locals.items()
            }
            saved = {
                reg: self._current_extra_args * 4 + var_loc
                for reg, var_loc in saved.items()
            }
            for i in range(self._current_extra_args):
                self._current_locals[f"#a{6 + i}"] = i * 4

            self._symbol_table[fn_name] = {
                "label": self._fn_label(),
                "locals": self._current_locals,
                "saved": saved,
                "stack_frame": (len(self._current_locals) + len(saved)) * 4,
            }

        def _var(self) -> int:
            var_loc: int = self._current_var_loc
            self._current_var_loc += 4
            return var_loc

        def _local(self, var_name: str) -> None:
            if var_name not in self._current_locals:
                self._current_locals[var_name] = self._var()

        def _visit_flattened_argument_list(self, n: ASTNode) -> None:
            self._builtin_visit_all(n)
            if len(n) > 6 + self._current_extra_args:
                self._current_extra_args = len(n) - 6

        def _visit_variable(self, n: ASTNode) -> None:
            self._local(n.lexeme)

    class Compile(Visitor):
        def __init__(
            self,
            constant_aggregate: dict[str, str],
            symbol_table: dict[str, dict[str, Any]],
        ):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.visit_all(joini),
            )
            self._c: dict[str, str] = constant_aggregate
            self._s: dict[str, dict[str, Any]] = symbol_table

        # todo: incredibly ugly
        def _generate_data_section(self) -> str:
            return join("[data]", joini(f'{self._c[s]}: "{s}"' for s in self._c))

        def _label(self) -> str:
            label = f"l{self._label_num}"
            self._label_num += 1
            return label

        def _visit_b(self, n: ASTNode) -> str:
            self._label_num: int = 0
            return sjoin(
                self._generate_data_section(),
                join("[code]", tabbed(sjoini(self(c) for c in n))),
            )

        def _visit_block(
            self,
            n: Node,
        ) -> Any:
            match n.choice:
                # <block> ::= <statement>;
                case 0:
                    return self(n[0])

                # <block> ::= "{" <statement>* "}";
                case 1:
                    return tabbed(self(n[1]))

        # <declaration> ::= "fn" <function> "\(" <parameter_list>? "\)" <block>;
        def _visit_declaration(self, n: ASTNode) -> Any:
            fn_name: str = n[1].lexeme
            # todo: no bueno, probably visitor contextualize this
            # "current symbol table"
            self._cst: dict[str, Any] = self._s[fn_name]
            # "current locals"
            self._cl: dict[str, int] = self._cst["locals"]
            # "current saved registers"
            self._csr: dict[str, int] = self._cst["saved"]
            fn_label: str = self._cst["label"]

            # todo: could be prettier
            # store arguments in local variables
            commit_args: str = ""
            if len(n[3]) != 0:
                commit_args = joini(
                    self._commit_var(c.lexeme, f"a{i}")
                    for i, c in enumerate(n[3][0])
                    if i < 6
                )

                if len(n[3][0]) > 6:
                    commit_args = join(
                        commit_args,
                        joini(
                            join(
                                f"l t0 sp {self._cst['stack_frame'] + (i - 6) * 4} # t0 = [sp + {self._cst['stack_frame'] + (i - 6) * 4}]",
                                self._commit_var(n[3][0][i].lexeme, "t0"),
                            )
                            for i in range(6, len(n[3][0]))
                        ),
                    )

            appetizer: str = join(
                f"{fn_label}:",
                tabbed(
                    join(
                        # allocate stack frame
                        f"subv sp sp {self._cst['stack_frame']} # sp = sp - {self._cst['stack_frame']};",
                        # todo: optimize this away if there are no fn calls?
                        # push ra onto stack
                        f"s ra sp {self._csr['ra']} # [sp + {self._csr['ra']}] = ra;",
                        commit_args,
                    )
                ),
            )
            main_course: str = ""
            dessert: str = tabbed(
                join(
                    # reload ra
                    f"l ra sp {self._csr['ra']} # ra = [sp + {self._csr['ra']}];",
                    # deallocate stack frame
                    f"addv sp sp {self._cst['stack_frame']} # sp = sp + {self._cst['stack_frame']};",
                    # go back
                    "jr ra # pc = ra;",
                )
            )

            # <block> ::= <statement> | "{" <statements>* "}";
            match n[5].choice:
                case 0:
                    main_course = tabbed(self(n[5]))

                case 1:
                    main_course = self(n[5])

                case _:  # pragma: no cover
                    assert False

            return join(appetizer, main_course, dessert)

        def _visit_statement(
            self,
            n: Node,
        ) -> Any:
            match n.choice:
                # <statement> ::= (<variable> | <array_access>) "=" (<operand> | <expression> | <mem_access> | "alloc" "\(" <variable> "\)" | "free" "\(" <variable> "\)" | "stoi" "\(" <variable> "\)" | <function> "\(" <flattened_argument_list>? "\)") ";";
                case 0:
                    main_course: str = ""
                    dessert: str = (
                        self._commit_var(n[0][0].lexeme, "t0")
                        if n[0].choice == 0
                        else self._commit_array_access(n[0][0], "t0")
                    )

                    match n[2].choice:
                        # <operand> ::= <variable> | <string> | <array_access> | decimal_integer;
                        case 0:
                            main_course = self._fetch_operand(n[2][0], "t0")

                        # <expression>
                        case 1:
                            main_course = self(n[2][0])

                        # <mem_access> ::= "\[" <variable> "+" decimal_integer "\]";
                        case 2:
                            main_course = join(
                                f"l t1 r1 {self._cl[n[2][0][1].lexeme]} # t1 = [sp + alloc[{n[2][0][1].lexeme}]];",
                                f"l t0 t1 {n[2][0][3].lexeme} # t0 = [t1 + {n[2][0][3].lexeme}]",
                            )

                        # todo: wait free() does not belong here lol
                        # "alloc" "\(" <operand> "\)" | "free" "\(" <operand> "\)"
                        case 3 | 4:
                            load_operand: str = self._fetch_operand(n[2][2], "a1")

                            # somehow n[2].choice works here...
                            # ^ no longer true but only shifted by 1
                            main_course = join(
                                f"setv a0 {n[2].choice + 1} # a0 = {n[2].choice + 1}; ({n[2][0].lexeme})",
                                load_operand,
                                f"e # a0 = {n[2][0].lexeme}(a1);",
                                f"set t0 a0 # t0 = a0;",
                            )

                        # "stoi" "\(" <operand> "\)"
                        case 5:
                            load_operand: str = self._fetch_operand(n[2][2], "a1")

                            main_course = join(
                                "setv a0 2 # a0 = 2; (stoi)",
                                load_operand,
                                f"e # a0 = {n[2][0].lexeme}(a1);",
                                f"set t0 a0 # t0 = a0;",
                            )

                        # <function> "\(" <flattened_argument_list> "\)"
                        case 6:
                            # todo: the second instruction is completely avoidable... just commit a0 directly
                            main_course = join(
                                self._call_function(n[2]),
                                "set t0 a0 # t0 = a0;",
                            )

                        case _:  # pragma: no cover
                            assert False

                    return join(main_course, dessert)

                # <statement> ::= ("print" | "printi" | "read") "\(" <operand> "\)" ";";
                case 1:
                    appetizer: str = self._fetch_operand(n[2], "a1")

                    main_course: str = ""
                    # "print" | "printi" | "read"
                    match n[0].choice:
                        # "print"
                        case 0:
                            main_course = join(
                                "setv a0 0 # a0 = 0; (print)",
                                "e # print(a1);",
                            )

                        # "printi"
                        case 1:
                            main_course = join(
                                "setv a0 3 # a0 = 3; (printi)",
                                "e # printi(a1);",
                            )

                        # "read"
                        case 2:
                            main_course = join(
                                "setv a0 1 # a0 = 1; (read)",
                                "e # read(a1);",
                            )

                        case _:  # pragma: no cover
                            assert False

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
                        f"b t0 {end_label} # if (t0) goto {end_label};",
                    )
                    dessert: str = join(
                        f"j {start_label} # goto {start_label};",
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
                        f"b t0 {label} # if (t0) goto {label};",
                    )
                    dessert: str = f"{label}:"

                    return join(appetizer, main_course, dessert)

                # <statement> ::= <mem_access> "=" <variable> ";";
                case 4:
                    return join(
                        f"l t0 r1 {self._cl[n[0][1].lexeme]} # t0 = [sp + alloc[{self._cl[n[0][1].lexeme]}]];",
                        f"l t1 r1 {self._cl[n[2].lexeme]} # t1 = [sp + alloc[{self._cl[n[2].lexeme]}]];",
                        f"s t1 t0 {n[0][3].lexeme} # [t0 + {n[0][3].lexeme}] = t1;",
                    )

                # <statement> ::= "return" <operand>? ";";
                case 5:
                    return_operand: str = ""

                    # todo: operand loading rework
                    if len(n[1]) != 0:
                        return_operand = self._fetch_operand(n[1][0], "a0")

                    # todo: duplicate of function dessert
                    return join(
                        return_operand,
                        # reload ra
                        f"l ra sp {self._csr['ra']} # ra = [sp + {self._csr['ra']}];",
                        # deallocate stack frame
                        f"addv sp sp {self._cst['stack_frame']} # sp = sp + {self._cst['stack_frame']};",
                        # go back
                        "jr ra # pc = ra;",
                    )

                # <statement> ::= <function> "\(" <flattened_argument_list>? "\)" ";";
                case 6:
                    return self._call_function(n)

                case _:  # pragma: no cover
                    assert False

        def _call_function(self, n: ASTNode) -> str:
            fn_name: str = n[0].lexeme
            fn_label: str = self._s[fn_name]["label"]

            fetch_args: str = ""
            if len(n[2]) != 0:
                # todo: support argument overflow
                fetch_args = joini(
                    self._fetch_operand(c, f"a{i}")
                    for i, c in enumerate(n[2][0])
                    if i < 6
                )

                if len(n[2][0]) > 6:
                    fetch_args = join(
                        fetch_args,
                        joini(
                            join(
                                self._fetch_operand(n[2][0][i], "t0"),
                                self._commit_var(f"#a{i}", "t0"),
                            )
                            for i in range(6, len(n[2][0]))
                        ),
                    )

            # todo: args
            # todo: reg saving
            return join(
                fetch_args,
                "addv ra pc 8 # t0 = pc + 8;",
                f"j {fn_label} # goto {fn_label};",
            )

        def _commit_var(self, var_name: str, reg: str) -> str:
            return (
                f"s {reg} sp {self._cl[var_name]} # [sp + alloc[{var_name}]] = {reg};"
            )

        def _commit_array_access(self, n: ASTNode, reg: str) -> str:
            return join(
                self._fetch_var(n[0], "t2"),
                self._fetch_operand(n[2], "t3"),
                f"lsv t3 t3 2 # t3 = t3 << 2;",
                f"add t2 t2 t3 # t2 = t2 + t3;",
                f"s {reg} t2 0 # {reg} = [t2 + 0];",
            )

        def _fetch_var(self, n: ASTNode, reg: str) -> str:
            var_name: str = n.lexeme
            return (
                f"l {reg} sp {self._cl[var_name]} # {reg} = [sp + alloc[{var_name}]];"
            )

        def _fetch_array_access(self, n: ASTNode, reg: str) -> str:
            return join(
                self._fetch_var(n[0], "t2"),
                self._fetch_operand(n[2], "t3"),
                f"lsv t3 t3 2 # t3 = t3 << 2;",
                f"add t2 t2 t3 # t2 = t2 + t3;",
                f"l {reg} t2 0 # {reg} = [t2 + 0];",
            )

        def _fetch_operand(self, n: ASTNode, reg: str) -> str:
            # <operand> ::= <variable> | decimal_integer;
            match n.choice:
                # <operand> ::= <variable>;
                case 0:
                    return self._fetch_var(n[0], reg)

                # <operand> ::= <string>;
                case 1:
                    return (
                        f"setv {reg} {self._c[n[0].literal]} # {reg} = {n[0].lexeme};"
                    )

                # <operand> ::= <array_access>;
                case 2:
                    return self._fetch_array_access(n[0], reg)

                # <operand> ::= decimal_integer;
                case 3:
                    return f"setv {reg} {n[0].lexeme} # {reg} = {n[0].lexeme};"

                case _:  # pragma: no cover
                    assert False

        def _visit_expression(self, n: ASTNode) -> Any:
            match n.choice:
                # <unary_operator> <operand>
                case 0:
                    # constant expression optimization
                    if n[1].choice == 3:
                        val: int = n[1][0].literal
                        val = 1 if val == 0 else 0
                        return f"setv t0 {val} # t0 = {val};"

                    else:
                        # todo: optimize constant
                        return join(
                            self._fetch_operand(n[1], "t1"),
                            f"eqv t0 t1 0 # t0 = t1 == 0;",
                        )

                # <operand> <binary_operator> <operand>
                case 1:
                    lop: ASTNode = n[0]
                    rop: ASTNode = n[2]

                    # constant expression optimization
                    if lop.choice == 3 and rop.choice == 3:
                        binop = {
                            # <binary_operator> ::= "\+";
                            0: lambda x, y: x + y,
                            # <binary_operator> ::= "-";
                            1: lambda x, y: x - y,
                            # <binary_operator> ::= "\*";
                            2: lambda x, y: x * y,
                            # <binary_operator> ::= "/";
                            3: lambda x, y: x // y,
                            # <binary_operator> ::= "%";
                            4: lambda x, y: x % y,
                            # <binary_operator> ::= "\|";
                            5: lambda x, y: x | y,
                            # <binary_operator> ::= "&";
                            6: lambda x, y: x & y,
                            # <binary_operator> ::= "^";
                            7: lambda x, y: x ^ y,
                            # <binary_operator> ::= "==";
                            8: lambda x, y: 1 if x == y else 0,
                            # <binary_operator> ::= "!=";
                            9: lambda x, y: 1 if x != y else 0,
                            # <binary_operator> ::= ">";
                            10: lambda x, y: 1 if x > y else 0,
                            # <binary_operator> ::= ">=";
                            11: lambda x, y: 1 if x >= y else 0,
                            # <binary_operator> ::= "<";
                            12: lambda x, y: 1 if x < y else 0,
                            # <binary_operator> ::= "<=";
                            13: lambda x, y: 1 if x <= y else 0,
                            # <binary_operator> ::= "<<";
                            14: lambda x, y: x << y,
                            # <binary_operator> ::= ">>";
                            15: lambda x, y: x >> y,
                        }[n[1].choice]

                        lop_val: int = lop[0].literal
                        rop_val: int = rop[0].literal
                        val: int = binop(lop_val, rop_val)
                        return f"setv t0 {val} # t0 = {val};"

                    inst = {
                        # <binary_operator> ::= "\+";
                        0: "add",
                        # <binary_operator> ::= "-";
                        1: "sub",
                        # <binary_operator> ::= "\*";
                        2: "mul",
                        # <binary_operator> ::= "/";
                        3: "div",
                        # <binary_operator> ::= "%";
                        4: "mod",
                        # <binary_operator> ::= "\|";
                        5: "or",
                        # <binary_operator> ::= "&";
                        6: "and",
                        # <binary_operator> ::= "^";
                        7: "xor",
                        # <binary_operator> ::= "==";
                        8: "eq",
                        # <binary_operator> ::= "!=";
                        9: "ne",
                        # <binary_operator> ::= ">";
                        10: "gt",
                        # <binary_operator> ::= ">=";
                        11: "ge",
                        # <binary_operator> ::= "<";
                        12: "lt",
                        # <binary_operator> ::= "<=";
                        13: "le",
                        # <binary_operator> ::= "<<";
                        14: "ls",
                        # <binary_operator> ::= ">>";
                        15: "rs",
                    }[n[1].choice]

                    # todo: fix lazy comment (print it as binary operation)
                    # todo: constant optimizations
                    # todo: very very sloppy
                    return join(
                        self._fetch_operand(lop, "t1"),
                        self._fetch_operand(rop, "t2"),
                        f"{inst} t0 t1 t2 # t0 = {inst}(t1, t2);",
                    )

                case _:  # pragma: no cover
                    assert False
