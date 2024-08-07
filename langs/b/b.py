from __future__ import annotations
from typing import Any, Callable

from common import (
    Monad,
    tabbed,
    joinv,
    join,
    sjoinv,
    sjoin,
    load,
)
from lexical import Lex
from syntax import (
    Grammar,
    Parse,
    Visitor,
    ASTNode,
    NonterminalASTNode,
)

from ..lang import Lang


class B(Lang):
    name = "b"
    grammar = Grammar.from_xbnf("b", load("langs/b/spec/b.xbnf"), ignore=["#[^\n]*"])

    compile: Callable[[ASTNode], None]

    class Parse:
        def __init__(self, entry_point: str | None = None) -> None:
            self._lex = Lex.for_lang(B)
            self._parse = Parse.for_lang(B, entry_point=entry_point)

        def __call__(self, prog) -> ASTNode:
            return Monad(prog).then(self._lex).then(self._parse).v

    class Shake(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.rebuild,
                default_terminal_node_visitor=lambda _, n: n,
            )

        def _visit_b(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<b>")
            main_fn_declared: bool = False
            declarations: dict[str, NonterminalASTNode] = {}
            for c in n.declarations:
                declaration: NonterminalASTNode = self(c)
                name: str = declaration.name.lexeme

                if name in declarations:
                    # todo: log error
                    raise RuntimeError(f"function '{name}' declared multiple times")

                if name == "main":
                    if main_fn_declared:
                        # todo: log error
                        raise RuntimeError(f"function '{name}' declared multiple times")

                    n_.add(declaration)
                    main_fn_declared = True

                else:
                    declarations[name] = declaration

            if not main_fn_declared:
                # todo: log error
                raise RuntimeError("main function not declared")

            for name in declarations:
                n_.add(declarations[name])

            return n_

        def _visit_argument_list(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<flattened_argument_list>")
            n_.add(self(n.first))
            for c in n.rest:
                n_.add(self(c.arg))
            n_.extras["name"] = "args"
            return n_

        def _visit_parameter_list(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<flattened_parameter_list>")
            n_.add(self(n.first))
            for c in n.rest:
                n_.add(self(c.param))
            n_.extras["name"] = "params"
            return n_

    class Print(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.visit_all(join),
                default_terminal_node_visitor=lambda _, n: n.lexeme,
            )

        def _visit_b(self, n: ASTNode) -> str:
            return self._builtin_visit_all(n, sjoin)

        def _visit_declaration(self, n: ASTNode) -> str:
            return f"fn {self(n.name)}({self(n.params)}) {self(n.body)}"

        def _visit_flattened_argument_list(self, n: ASTNode) -> str:
            return self._builtin_visit_all(n, ", ".join)

        def _visit_flattened_parameter_list(self, n: ASTNode) -> str:
            return self._builtin_visit_all(n, ", ".join)

        def _visit_block(
            self,
            n: NonterminalASTNode,
        ) -> str:
            match n.choice:
                # <block> ::= <statement>;
                case 0:
                    return self(n.statement)

                # <block> ::= "{" <statement>* "}";
                case 1:
                    inner: str = self(n.statements)
                    if not inner:
                        return "{}"

                    else:
                        return joinv("{", tabbed(inner), "}")

                case _:  # pragma: no cover
                    assert False

        def _visit_statement(
            self,
            n: NonterminalASTNode,
        ) -> str:
            match n.choice:
                # <statement> ::= (<variable> | <array_access>) "=" (<operand> | <expression> | <function> "\(" <flattened_parameter_list>? "\)") ";";
                case 0:
                    match n.rhs.choice:
                        # <operand> | <expression>
                        case 0 | 1:
                            return f"{self(n.lhs)} = {self(n.rhs)};"

                        # <function> "\(" <flattened_parameter_list>? "\)"
                        case 2:
                            return (
                                # todo: change n.rhs[2] to n.rhs.args when function calls are unified
                                f"{self(n.lhs)} = {self(n.rhs.fn)}({self(n.rhs[2])});"
                            )

                        case _:  # pragma: no cover
                            assert False

                # <statement> ::= "while" "\(" <expression> "\)" <block>;
                case 1:
                    return f"while ({self(n.cond)}) {self(n.body)}"

                # <statement> ::= "if" "\(" <expression> "\)" <block>;
                case 2:
                    return f"if ({self(n.cond)}) {self(n.body)}"

                # <statement> ::= "return" <operand>? ";";
                case 3:
                    if n.ret:
                        return f"return {self(n.ret)};"
                    else:
                        return "return;"

                # <statement> ::= <function> "\(" <flattened_argument_list>? "\)" ";";
                case 4:
                    # todo: change n[2] to n.args when function calls are unified
                    return f"{self(n.fn)}({self(n[2])});"

                case _:  # pragma: no cover
                    assert False

        def _visit_expression(
            self,
            n: ASTNode,
        ) -> str:
            match n.choice:
                # <expression> ::= <unary_operator> <operand>;
                case 0:
                    return f"{self(n.uop)}{self(n.op)}"

                # <expression> ::= <operand> <binary_operator> <operand>;
                case 1:
                    return f"{self(n.lop)} {self(n.bop)} {self(n.rop)}"

                case _:  # pragma: no cover
                    assert False

        def _visit_array_access(
            self,
            n: ASTNode,
        ) -> str:
            return f"{self(n.arr)}[{self(n.idx)}]"

    class Compile(Visitor):
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

        def __init__(
            self,
        ):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.visit_all(join),
            )

        # todo: incredibly ugly
        def _generate_data_section(self) -> str:
            return joinv("[data]", join(f'{self._c[s]}: "{s}"' for s in self._c))

        def _label(self) -> str:
            label = f"l{self._label_num}"
            self._label_num += 1
            return label

        def _visit_b(self, n: ASTNode) -> str:
            self._c: dict[str, str] = B.Compile.Aggregate()(n)
            self._s: dict[str, dict[str, Any]] = B.Compile.GenerateSymbolTable()(n)
            self._label_num: int = 0
            return sjoinv(
                self._generate_data_section(),
                joinv("[code]", sjoin(self(c) for c in n)),
            )

        def _visit_block(
            self,
            n: ASTNode,
        ) -> Any:
            match n.choice:
                # <block> ::= <statement>;
                case 0:
                    return self(n.statement)

                # <block> ::= "{" <statement>* "}";
                case 1:
                    return tabbed(self(n.statements))

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
            if n.params:
                commit_args = join(
                    self._commit_var(c.lexeme, f"a{i}")
                    for i, c in enumerate(n.params[0])
                    if i < 6
                )

                if len(n.params[0]) > 6:
                    commit_args = joinv(
                        commit_args,
                        join(
                            joinv(
                                f"l t0 sp {self._cst['stack_frame'] + (i - 6) * 4} # t0 = [sp + {self._cst['stack_frame'] + (i - 6) * 4}]",
                                self._commit_var(n.params[0][i].lexeme, "t0"),
                            )
                            for i in range(6, len(n.params[0]))
                        ),
                    )

            appetizer: str = joinv(
                f"{fn_label}:",
                tabbed(
                    joinv(
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
                joinv(
                    # reload ra
                    f"l ra sp {self._csr['ra']} # ra = [sp + {self._csr['ra']}];",
                    # deallocate stack frame
                    f"addv sp sp {self._cst['stack_frame']} # sp = sp + {self._cst['stack_frame']};",
                    # go back
                    "jr ra # pc = ra;",
                )
            )

            # <block> ::= <statement> | "{" <statements>* "}";
            match n.body.choice:
                case 0:
                    main_course = tabbed(self(n.body))

                case 1:
                    main_course = self(n.body)

                case _:  # pragma: no cover
                    assert False

            return joinv(appetizer, main_course, dessert)

        def _visit_statement(
            self,
            n: Node,
        ) -> Any:
            match n.choice:
                # <statement> ::= (<variable> | <array_access>) "=" (<operand> | <expression> | <function> "\(" <flattened_argument_list>? "\)") ";";
                case 0:
                    main_course: str = ""
                    dessert: str = (
                        self._commit_var(n.lhs[0].lexeme, "t0")
                        if n.lhs.choice == 0
                        else self._commit_array_access(n.lhs[0], "t0")
                    )

                    match n.rhs.choice:
                        # <operand> ::= <variable> | <string> | <array_access> | decimal_integer;
                        case 0:
                            main_course = self._fetch_operand(n.rhs[0], "t0")

                        # <expression>
                        case 1:
                            main_course = self(n.rhs[0])

                        # <function> "\(" <flattened_argument_list> "\)"
                        case 2:
                            # todo: the second instruction is completely avoidable... just commit a0 directly
                            main_course = joinv(
                                self._call_function(n.rhs),
                                "set t0 a0 # t0 = a0;",
                            )

                        case _:  # pragma: no cover
                            assert False

                    return joinv(main_course, dessert)

                # <statement> ::= "while" "\(" <expression> "\)" <block>;
                case 1:
                    start_label: str = self._label()
                    end_label: str = self._label()
                    main_course: str = tabbed(self(n.body))
                    appetizer: str = joinv(
                        f"{start_label}:",
                        self(n.cond),
                        f"eqv t0 t0 0 # t0 = (t0 == 0);",
                        f"b t0 {end_label} # if (t0) goto {end_label};",
                    )
                    dessert: str = joinv(
                        f"j {start_label} # goto {start_label};",
                        f"{end_label}:",
                    )

                    return joinv(appetizer, main_course, dessert)

                # <statement> ::= "if" "\(" <expression> "\)" <block>;
                case 2:
                    label: str = self._label()
                    main_course: str = tabbed(self(n.body))
                    appetizer: str = joinv(
                        self(n.cond),
                        f"eqv t0 t0 0 # t0 = (t0 == 0);",
                        f"b t0 {label} # if (t0) goto {label};",
                    )
                    dessert: str = f"{label}:"

                    return joinv(appetizer, main_course, dessert)

                # <statement> ::= "return" <operand>? ";";
                case 3:
                    return_operand: str = ""

                    # todo: operand loading rework
                    if len(n[1]) != 0:
                        return_operand = self._fetch_operand(n.ret[0], "a0")

                    # todo: duplicate of function dessert
                    return joinv(
                        return_operand,
                        # reload ra
                        f"l ra sp {self._csr['ra']} # ra = [sp + {self._csr['ra']}];",
                        # deallocate stack frame
                        f"addv sp sp {self._cst['stack_frame']} # sp = sp + {self._cst['stack_frame']};",
                        # go back
                        "jr ra # pc = ra;",
                    )

                # <statement> ::= <function> "\(" <flattened_argument_list>? "\)" ";";
                case 4:
                    return self._call_function(n)

                case _:  # pragma: no cover
                    assert False

        def _call_function(self, n: ASTNode) -> str:
            fn_name: str = n.fn.lexeme
            fetch_args: str = ""

            # todo: allocating this on the stack every time is kinda bad...
            ecalls: dict[str, int] = {
                "print": 0,
                "read": 1,
                "stoi": 2,
                "printi": 3,
                "alloc": 4,
                "free": 5,
            }

            if fn_name in ecalls:
                fetch_args = (
                    f"setv a0 {ecalls[fn_name]} # a0 = {ecalls[fn_name]} ({fn_name});"
                )
                if n.args:
                    # todo: prayging user does not spam arguments in ecall rn
                    #         -- would need extra processing in symbol table generation
                    fetch_args = joinv(
                        fetch_args,
                        join(
                            self._fetch_operand(c, f"a{i + 1}")
                            for i, c in enumerate(n.args[0])
                            if i < 5
                        ),
                    )

                    if len(n.args[0]) > 5:
                        fetch_args = joinv(
                            fetch_args,
                            join(
                                joinv(
                                    self._fetch_operand(n.args[0][i], "t0"),
                                    self._commit_var(f"#a{i + 1}", "t0"),
                                )
                                for i in range(5, len(n.args[0]))
                            ),
                        )

                # todo: reg saving
                return joinv(
                    fetch_args,
                    f"e # a0 = {fn_name}({B.print(n.args)});",
                )

            else:
                fn_label: str = self._s[fn_name]["label"]
                if n.args:
                    fetch_args = join(
                        self._fetch_operand(c, f"a{i}")
                        for i, c in enumerate(n.args[0])
                        if i < 6
                    )

                    if len(n.args[0]) > 6:
                        fetch_args = joinv(
                            fetch_args,
                            join(
                                joinv(
                                    self._fetch_operand(n.args[0][i], "t0"),
                                    self._commit_var(f"#a{i}", "t0"),
                                )
                                for i in range(6, len(n.args[0]))
                            ),
                        )

                # todo: reg saving
                return joinv(
                    fetch_args,
                    "addv ra pc 8 # t0 = pc + 8;",
                    f"j {fn_label} # goto {fn_label};",
                )

        def _commit_var(self, var_name: str, reg: str) -> str:
            return (
                f"s {reg} sp {self._cl[var_name]} # [sp + alloc[{var_name}]] = {reg};"
            )

        def _commit_array_access(self, n: ASTNode, reg: str) -> str:
            return joinv(
                self._fetch_var(n.arr, "t2"),
                self._fetch_operand(n.idx, "t3"),
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
            return joinv(
                self._fetch_var(n.arr, "t2"),
                self._fetch_operand(n.idx, "t3"),
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
                    if n.op.choice == 3:
                        val: int = n.op[0].literal
                        val = 1 if val == 0 else 0
                        return f"setv t0 {val} # t0 = {val};"

                    else:
                        # todo: optimize constant
                        return joinv(
                            self._fetch_operand(n.op, "t1"),
                            f"eqv t0 t1 0 # t0 = t1 == 0;",
                        )

                # <operand> <binary_operator> <operand>
                case 1:
                    # constant expression optimization
                    if n.lop.choice == 3 and n.rop.choice == 3:
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
                        }[n.bop.choice]

                        lop_val: int = n.lop[0].literal
                        rop_val: int = n.rop[0].literal
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
                    }[n.bop.choice]

                    # todo: fix lazy comment (print it as binary operation)
                    # todo: constant optimizations
                    # todo: very very sloppy
                    return joinv(
                        self._fetch_operand(n.lop, "t1"),
                        self._fetch_operand(n.rop, "t2"),
                        f"{inst} t0 t1 t2 # t0 = {inst}(t1, t2);",
                    )

                case _:  # pragma: no cover
                    assert False


B.parse = B.Parse()
B.shake = B.Shake()
B.print = B.Print()

B.compile = B.Compile()
