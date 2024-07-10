from __future__ import annotations
from typing import Callable

from common import (
    Monad,
    tabbed,
    join,
    joini,
    sjoini,
    load,
)
from lexical import Lex
from syntax import (
    Grammar,
    Parse,
    Visitor,
    ASTNode,
    NonterminalASTNode,
    ChoiceNonterminalASTNode,
)


class B2:
    grammar: Grammar = Grammar.from_xbnf(
        "b2", load("langs/b2/spec/b2.xbnf"), ignore=["#[^\n]*"]
    )

    class Parse:
        def __init__(self, entry_point: str | None = None) -> None:
            self._lex = Lex.for_lang(B2)
            self._parse = Parse.for_lang(B2, entry_point=entry_point)

        def __call__(self, prog) -> ASTNode:
            return Monad(prog).then(self._lex).then(self._parse).v

    parse: Callable[[str], ASTNode]
    print: Callable[[ASTNode], str]
    translate: Callable[[ASTNode], ASTNode]
    compile: Callable[[ASTNode], None]

    class BuildInternalAST(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.rebuild,
                default_terminal_node_visitor=lambda _, n: n,
            )

        def _visit_b2(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<b2>")
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
                default_nonterminal_node_visitor=Visitor.visit_all(
                    lambda components: " ".join(
                        filter(lambda s: len(s) != 0, components)
                    )
                ),
                default_terminal_node_visitor=lambda _, n: n.lexeme,
            )

        def _visit_b2(self, n: ASTNode) -> str:
            return self._builtin_visit_all(n, sjoini)

        def _visit_declaration(self, n: ASTNode) -> str:
            return f"fn {self(n.name)}({self(n.params)}) {self(n.body)}"

        def _visit_flattened_argument_list(self, n: ASTNode) -> str:
            return self._builtin_visit_all(n, ", ".join)

        def _visit_flattened_parameter_list(self, n: ASTNode) -> str:
            return self._builtin_visit_all(n, ", ".join)

        def _visit_block(
            self,
            n: ChoiceNonterminalASTNode,
        ) -> str:
            match n.choice:
                # <block> ::= <statement>;
                case 0:
                    return self(n.statement)

                # <block> ::= "{" <statement>* "}";
                case 1:
                    inner: str = self._builtin_visit_all(n.statements, joini)
                    if not inner:
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
                # <statement> ::= <expression> ";";
                case 0:
                    return f"{self(n.expr)};"

                # <statement> ::= "while" "\(" <expression> "\)" <block>;
                case 1:
                    return f"while ({self(n.cond)}) {self(n.body)}"

                # <statement> ::= "if" "\(" <expression> "\)" <block>;
                case 2:
                    return f"if ({self(n.cond)}) {self(n.body)}"

                # <statement> ::= "return" <expression>? ";";
                case 3:
                    if n.ret:
                        return f"return {self(n.ret)};"
                    else:
                        return "return;"

                case _:  # pragma: no cover
                    assert False

        def _visit_primary_expression(
            self,
            n: ASTNode,
        ) -> str:
            match n.choice:
                # <primary_expression> ::= "(" <expression> ")";
                case 0:
                    return f"({self(n[1])})"

                # <primary_expression> ::= <function> "(" <flattened_argument_list> ")";
                case 1:
                    return f"{self(n.fn)}({self(n.args)})"

                case 2 | 3 | 4 | 5:
                    return self(n[0])

                case _:  # pragma: no cover
                    assert False

        def _visit_unary_expression(self, n: ASTNode) -> str:
            ops_str: str = "".join(self._builtin_visit_all(n.ops))
            return "".join([ops_str, self(n.expr)])

        def _visit_array_access(self, n: ASTNode) -> str:
            return f"{self(n.arr)}[{self(n.idx)}]"

        def _visit_string(self, n: ASTNode) -> str:
            return n.lexeme

    class Translate(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.visit_all("".join),
                default_terminal_node_visitor=lambda _, n: n.lexeme,
            )

        def _visit_b2(self, n: ASTNode) -> str:
            self._n_vars: int = 0
            self._vars: list[str] = []
            return self._builtin_visit_all(n, sjoini)

        def _var(self) -> str:
            if self._vars:
                return self._vars.pop()
            else:
                # todo: this might collide w vars in the input
                var: str = f"v{self._n_vars}"
                self._n_vars += 1
                return var

        def _free(self, var: str) -> None:
            self._vars.append(var)

        def _visit_declaration(self, n: ASTNode) -> str:
            return f"fn {self(n.name)}({B2.print(n.params)}) {self(n.body)}"

        def _visit_block(self, n: ASTNode) -> str:
            statements: list[str] = []
            match n.choice:
                # <block> ::= statement=<statement>;
                case 0:
                    statements.append(self(n.statement))

                # <block> ::= "{" statements=<statement>* "}";
                case 1:
                    for statement in n.statements:
                        statements.append(self(statement))

            if joini(statements) == "":
                return "{}"
            else:
                return join("{", tabbed(joini(statements)), "}")

        def _visit_statement(self, n: ASTNode) -> str:
            setup: str = ""
            var: str
            match n.choice:
                # <statement> ::= <expression> ";";
                case 0:
                    setup, _ = self(n.expr)
                    return setup

                # <statement> ::= "while" "(" <expression> ")" <block> ";";
                case 1:
                    setup, var = self(n.cond)
                    # dont forget to load up var at the end of the loop body!!!
                    # took me so long to find this...
                    original_body: str = self(n.body)  # guaranteed to have brances
                    mutated_body: str = join(
                        *original_body.split("\n")[:-1], tabbed(setup), "}"
                    )
                    # todo: get rid of the != 0
                    return join(setup, f"while ({var} != 0) {mutated_body}")

                # <statement> ::= "if" "(" cond=<expression> ")" body=<block> ";";
                case 2:
                    setup, var = self(n.cond)
                    # todo: get rid of the != 0
                    return join(setup, f"if ({var} != 0) {self(n.body)}")

                # <statement> ::= return <expression>? ";";
                case 3:
                    if n.ret:
                        setup, var = self(n.ret[0])
                        return join(setup, f"return {var};")

                    else:
                        return "return;"

                case _:  # pragma no cover
                    assert False

        def _visit_expression(self, n: ASTNode) -> str:
            return self(n[0])

        def _visit_assignment_expression(self, n: ASTNode) -> tuple[str, str]:
            match n.choice:
                # <assignment_expression> ::= expr=<or_expression>;
                case 0:
                    return self(n.expr)

                # <assignment_expression> ::= lhs=<store> "=" rhs=<assignment_expression>;
                case 1:
                    setup, rvar = self(n.rhs)
                    var: str
                    match n.lhs.choice:
                        # <store> ::= <variable>;
                        case 0:
                            var = n.lhs[0].lexeme
                            setup = join(setup, f"{var} = {rvar};")

                        # <store> ::= <array_access>;
                        case 1:
                            var = self._var()
                            aisetup, aivar = self(n.lhs[0].idx)
                            setup = join(
                                setup,
                                aisetup,
                                f"{n.lhs[0].arr.lexeme}[{aivar}] = {rvar};",
                                f"{var} = {n.lhs[0].arr.lexeme}[{aivar}];",
                            )

                        case _:  # pragma: no cover
                            assert False

                    return setup, var

                case _:  # pragma: no cover
                    assert False

        def _visit_relational_expression(self, n: ASTNode) -> tuple[str, str]:
            if not n.rest:
                return self(n.lexpr)

            setup, lvar = self(n.lexpr)
            var: str = self._var()
            for rhs in n.rest:
                rsetup, rvar = self(rhs.expr)
                setup = join(
                    setup, rsetup, f"{var} = {lvar} {rhs[0][0].lexeme} {rvar};"
                )
                # use self as lvar for subsequent ops
                lvar = var

            return setup, var

        def _visit_or_expression(self, n: ASTNode) -> tuple[str, str]:
            if not n.rest:
                return self(n.lexpr)

            setup, lvar = self(n.lexpr)
            var: str = self._var()
            for rhs in n.rest:
                rsetup, rvar = self(rhs.expr)
                setup = join(setup, rsetup, f"{var} = {lvar} {rhs[0].lexeme} {rvar};")
                # use self as lvar for subsequent ops
                lvar = var

            return setup, var

        def _visit_xor_expression(self, n: ASTNode) -> tuple[str, str]:
            if not n.rest:
                return self(n.lexpr)

            setup, lvar = self(n.lexpr)
            var: str = self._var()
            for rhs in n.rest:
                rsetup, rvar = self(rhs.expr)
                setup = join(setup, rsetup, f"{var} = {lvar} {rhs[0].lexeme} {rvar};")
                # use self as lvar for subsequent ops
                lvar = var

            return setup, var

        def _visit_and_expression(self, n: ASTNode) -> tuple[str, str]:
            if not n.rest:
                return self(n.lexpr)

            setup, lvar = self(n.lexpr)
            var: str = self._var()
            for rhs in n.rest:
                rsetup, rvar = self(rhs.expr)
                setup = join(setup, rsetup, f"{var} = {lvar} {rhs[0].lexeme} {rvar};")
                # use self as lvar for subsequent ops
                lvar = var

            return setup, var

        def _visit_shift_expression(self, n: ASTNode) -> tuple[str, str]:
            if not n.rest:
                return self(n.lexpr)

            setup, lvar = self(n.lexpr)
            var: str = self._var()
            for rhs in n.rest:
                rsetup, rvar = self(rhs.expr)
                setup = join(
                    setup, rsetup, f"{var} = {lvar} {rhs[0][0].lexeme} {rvar};"
                )
                # use self as lvar for subsequent ops
                lvar = var

            return setup, var

        def _visit_additive_expression(self, n: ASTNode) -> tuple[str, str]:
            if not n.rest:
                return self(n.lexpr)

            setup, lvar = self(n.lexpr)
            var: str = self._var()
            for rhs in n.rest:
                rsetup, rvar = self(rhs.expr)
                setup = join(
                    setup, rsetup, f"{var} = {lvar} {rhs[0][0].lexeme} {rvar};"
                )
                # use self as lvar for subsequent ops
                lvar = var

            return setup, var

        def _visit_multiplicative_expression(self, n: ASTNode) -> tuple[str, str]:
            if not n.rest:
                return self(n.lexpr)

            setup, lvar = self(n.lexpr)
            var: str = self._var()
            for rhs in n.rest:
                rsetup, rvar = self(rhs.expr)
                setup = join(
                    setup, rsetup, f"{var} = {lvar} {rhs[0][0].lexeme} {rvar};"
                )
                # use self as lvar for subsequent ops
                lvar = var

            return setup, var

        def _visit_unary_expression(self, n: ASTNode) -> tuple[str, str]:
            if not n.ops:
                return self(n.expr)

            setup, var = self(n.expr)
            for uop in list(iter(n.ops))[::-1]:
                setup = join(setup, f"{var} = {uop[0].lexeme}{var};")

            return setup, var

        def _visit_primary_expression(self, n: ASTNode) -> tuple[str, str]:
            match n.choice:
                # <primary_expression> ::= "(" expr=<expression> ")";
                case 0:
                    return self(n.expr)

                # <primary_expression> ::= fn=<function> "(" args=<flattened_argument_list> ")";
                case 1:
                    setup: str = ""
                    vars: list[str] = []
                    if n.args:
                        for arg in n.args[0]:
                            asetup, avar = self(arg)
                            vars.append(avar)
                            setup = join(setup, asetup)
                    var: str
                    # dont reuse here...
                    var = self._var()
                    setup = join(setup, f"{var} = {n.fn.lexeme}({', '.join(vars)});")
                    return setup, var

                # <primary_expression> ::= <array_access>;
                case 2:
                    setup, var = self(n[0].idx)
                    # reuse var!
                    setup = join(setup, f"{var} = {n[0].arr.lexeme}[{var}];")
                    return setup, var

                # <primary_expression> ::= <integer> | <string> | <variable>;
                case 3 | 4 | 5:
                    var: str = self._var()
                    return f"{var} = {n[0].lexeme};", var

                case _:  # pragma: no cover
                    assert False


B2.parse = Monad.F(B2.Parse()).then(B2.BuildInternalAST()).f
B2.print = B2.Print()
B2.translate = B2.Translate()
