from __future__ import annotations
from typing import Any, Optional, cast

from common import Monad, joini, sjoini, Mutable, unescape
from lexical import Lexer
from runtime import MP0
from syntax import (
    Grammar,
    Parser,
    ASTNode,
    Visitor,
    NonterminalASTNode,
    ChoiceNonterminalASTNode,
)
from runtime import Ins, Prog

from ..lang import Lang


class A(Lang):
    with open("langs/a/spec/a.xbnf") as xbnf_f:
        xbnf: str = xbnf_f.read()

    grammar: Grammar = Grammar.from_xbnf("a", xbnf, ignore=["#[^\n]*"])

    @staticmethod
    def count_instructions_generated(prog: str) -> int:
        ins_count: Mutable[int] = Mutable(0)
        translated_ast: ASTNode = (
            Monad(prog)
            .then(A.Parse())
            .then(A.BuildInternalAST())
            .then(A.Translate())
            .value
        )
        A.Assemble()(translated_ast, ins_count=ins_count)
        return ins_count.value

    @staticmethod
    def assemble(prog: str) -> Prog:
        return (
            Monad(prog)
            .then(A.Parse())
            .then(A.BuildInternalAST())
            .then(A.Translate())
            .then(A.Assemble())
            .value
        )

    class Parse:
        def __call__(self, prog: str, entry_point: Optional[str] = None) -> ASTNode:
            return (
                Monad(prog)
                .then(Lexer.for_lang(A))
                .then(Parser.for_lang(A, entry_point=entry_point))
                .value
            )

    class Print(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.visit_all(joini),
                default_terminal_node_visitor=lambda _, n: n.lexeme,
            )

        def _visit_a(self, n: ASTNode) -> str:
            return sjoini(self(c) for c in n[0])

        def _visit_instruction(self, n: ASTNode) -> str:
            return " ".join(self(c) for c in n)

        def _visit_pseudoinstruction(self, n: ASTNode) -> str:
            return " ".join(self(c) for c in n)

        def _visit_constant_definition(self, n: ASTNode) -> str:
            return " ".join(self(c) for c in n)

        def _visit_label(self, n: ASTNode) -> str:
            return "".join(self(c) for c in n)

    class BuildInternalAST(Visitor):
        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.rebuild,
                default_terminal_node_visitor=lambda _, n: n,
            )

        def _visit_a(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<a>")
            code_section: NonterminalASTNode = NonterminalASTNode("<code_section>")
            data_section: NonterminalASTNode = NonterminalASTNode("<data_section>")
            for c in n[0]:
                c_: ChoiceNonterminalASTNode = self(c)
                match c_.choice:
                    case 0:
                        for gc in c_[0]:
                            code_section.add(gc)

                    case 1:
                        for gc in c_[0]:
                            data_section.add(gc)

                    case _:
                        assert False

            n_.add(code_section)
            n_.add(data_section)
            return n_

        def _visit_data_section(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<data_section>")
            for c in n[1]:
                n_.add(self(c))

            return n_

        def _visit_constant_definition(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<constant_definition>")
            # should technically be able to support multiple labels...
            # but there is no reason for that
            n_.extras["labels"] = [self(n[0])]
            n_.add(self(n[1]))

            return n_

        def _visit_code_section(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<code_section>")
            for c in n[1]:
                n_.add(self(c))

            return n_

        def _visit_labeled_instruction(self, n: ASTNode) -> ASTNode:
            n_: ChoiceNonterminalASTNode = ChoiceNonterminalASTNode(
                "<instruction>", choice=n[1].choice
            )

            labels: list[str] = []

            if n[0]:
                for c in n[0]:
                    labels.append(self(c))

            n_.add(self(n[1])[0])
            # add labels to n_[0] since <instruction> layer will be stripped in translation
            n_[0].extras["labels"] = labels

            return n_

        def _visit_label(self, n: ASTNode) -> str:
            return n[0].lexeme

    class Translate(Visitor):

        def __init__(self):
            super().__init__(
                default_nonterminal_node_visitor=Visitor.rebuild,
                default_terminal_node_visitor=lambda _, n: n,
            )

        def _visit_code_section(self, n: ASTNode) -> ASTNode:
            n_: NonterminalASTNode = NonterminalASTNode("<code_section>")
            for c in n:
                match c.choice:
                    # <instruction> ::= <legal_instruction>;
                    case 0:
                        n_.add(self(c[0]))

                    # <instruction> ::= <pseudoinstruction>;
                    case 1:
                        translated: tuple[ASTNode] = self(c[0])

                        for gc in translated:
                            n_.add(gc)

            return n_

        def _visit_pseudoinstruction(self, n: ASTNode) -> tuple[ASTNode]:
            # todo: probably can't just copy extras if it contains more than labels
            def ins(code: str, extras: dict[str, Any] = {}) -> ASTNode:
                n_: ASTNode = A.Parse()(code, entry_point="<instruction>")[0]
                n_.extras = dict(extras)
                return n_

            match n.choice:
                # <pseudoinstruction> ::= "jr" <reg>;
                # -> addi pc <reg> 0
                case 0:
                    return (ins(f"addi pc {n[1].lexeme} 0", n.extras),)

                # <pseudoinstruction> ::= "j" <lbl>;
                # -> j <lbl> # unchanged -- to be resolved
                case 1:
                    return (ins(f"j {n[1].lexeme}", n.extras),)

                # <pseudoinstruction> ::= "b" <reg> <imm> | "b" <reg> <lbl>;
                # -> bne <reg> zr <imm|lbl> # latter case to be resolved
                case 2 | 3:
                    return (ins(f"bne {n[1].lexeme} zr {n[2].lexeme}", n.extras),)

                # <pseudoinstruction> ::= "beq" <reg> <reg> <lbl>;
                # -> beq <reg> <reg> <lbl> # to be resolved
                case 4:
                    return (
                        ins(
                            f"beq {n[1].lexeme} {n[2].lexeme} {n[3].lexeme}",
                            n.extras,
                        ),
                    )

                # <pseudoinstruction> ::= "bne" <reg> <reg> <lbl>;
                # -> bne <reg> <reg> <lbl> # to be resolved
                case 5:
                    return (
                        ins(
                            f"bne {n[1].lexeme} {n[2].lexeme} {n[3].lexeme}",
                            n.extras,
                        ),
                    )

                # <pseudoinstruction> ::= "ne" <reg> <reg> <reg>;
                # -> xor <reg> <reg> <reg>
                case 6:
                    return (
                        ins(
                            f"xor {n[1].lexeme} {n[2].lexeme} {n[3].lexeme}",
                            n.extras,
                        ),
                    )

                # <pseudoinstruction> ::= "nei" <reg> <reg> <imm>;
                # -> xori <reg> <reg> <imm>
                case 7:
                    return (
                        ins(
                            f"xori {n[1].lexeme} {n[2].lexeme} {n[3].lexeme}",
                            n.extras,
                        ),
                    )

                # <pseudoinstruction> ::= "not" <reg> <reg>;
                # -> eqi <reg> <reg> <imm>
                case 8:
                    return (ins(f"eqi {n[1].lexeme} {n[2].lexeme} 0", n.extras),)

                # <pseudoinstruction> ::= "set" <reg> <reg>;
                # -> addi <reg> <reg> 0
                case 9:
                    return (ins(f"addi {n[1].lexeme} {n[2].lexeme} 0", n.extras),)

                # <pseudoinstruction> ::= "setv" <reg> <val>;
                # -> addi <reg> zr <val>
                # todo: big vals
                case 10:
                    return (ins(f"addi {n[1].lexeme} zr {n[2].lexeme}", n.extras),)

                # <pseudoinstruction> ::= "setv" <reg> <lbl>;
                # -> setv <reg> <lbl> # unchanged -- to be resolved
                case 11:
                    return (ins(f"setv {n[1].lexeme} {n[2].lexeme}", n.extras),)

                # <pseudoinstruction> ::= "addv" <reg> <reg> <val> |
                #                         "subv" <reg> <reg> <val> |
                #                         "mulv" <reg> <reg> <val> |
                #                         "divv" <reg> <reg> <val> |
                #                         "modv" <reg> <reg> <val> |
                #                         "orv"  <reg> <reg> <val> |
                #                         "andv" <reg> <reg> <val> |
                #                         "xorv" <reg> <reg> <val> |
                #                         "eqv"  <reg> <reg> <val> |
                #                         "nev"  <reg> <reg> <val> |
                #                         "gtv"  <reg> <reg> <val> |
                #                         "gev"  <reg> <reg> <val> |
                #                         "ltv"  <reg> <reg> <val> |
                #                         "lev"  <reg> <reg> <val> |
                #                         "lsv"  <reg> <reg> <val> |
                #                         "rsv"  <reg> <reg> <val>;
                # -> "opi" <reg> <reg> <val>
                # todo: big vals
                case (
                    12
                    | 13
                    | 14
                    | 15
                    | 16
                    | 17
                    | 18
                    | 19
                    | 20
                    | 21
                    | 22
                    | 23
                    | 24
                    | 25
                    | 26
                    | 27
                ):
                    return (
                        ins(
                            f"{n[0].lexeme[: -1]}i {n[1].lexeme} {n[2].lexeme} {n[3].lexeme}",
                            n.extras,
                        ),
                    )

                case _:  # pragma: no cover
                    assert False

    class Assemble(Visitor):
        class ResolveLabels(Visitor):
            def __init__(self) -> None:
                super().__init__()

            def _visit_a(self, n: ASTNode) -> dict[str, int]:
                label_map: dict[str, int] = {}
                self._builtin_visit_all(n, loc=Mutable(1), label_map=label_map)
                return label_map

            def _locate_and_map(
                self, n: ASTNode, loc: Mutable[int], label_map: dict[str, int]
            ) -> None:
                n.extras["loc"] = loc.value
                for label in n.extras["labels"]:
                    label_map[label] = n.extras["loc"]

            def _visit_legal_instruction(
                self, n: ASTNode, loc: Mutable[int], **ctx: Any
            ) -> None:
                self._locate_and_map(n, loc=loc, **ctx)
                loc += 4

            def _visit_pseudoinstruction(
                self, n: ASTNode, loc: Mutable[int], **ctx: Any
            ) -> None:
                self._locate_and_map(n, loc=loc, **ctx)
                # todo: this will most likely need to be changed...
                # a very stupid way to do this would be preallocate n * 4 regardless of type
                # actually that *could* be an angle
                loc += 4

            def _visit_constant_definition(
                self, n: ASTNode, loc: Mutable[int], **ctx: Any
            ) -> None:
                self._locate_and_map(n, loc=loc, **ctx)
                loc += len(unescape(n[0].lexeme[1:-1])) + 1

        @staticmethod
        def _combine(v: Visitor, n: ASTNode, **ctx) -> Prog:
            prog: Prog = Prog()
            for c in n:
                prog += v(c, **ctx)
            return prog

        def __init__(self) -> None:
            super().__init__(
                default_nonterminal_node_visitor=A.Assemble._combine,
                default_terminal_node_visitor=lambda *_, **ctx: Prog(),
            )

        def _visit_a(self, n: ASTNode, ins_count: Mutable[int] = Mutable(0)) -> Prog:
            label_map: dict[str, int] = A.Assemble.ResolveLabels()(n)
            return A.Assemble._combine(
                self, n, label_map=label_map, ins_count=ins_count
            )

        def _visit_legal_instruction(
            self, n: ASTNode, ins_count: Mutable[int], **_: Any
        ) -> Ins:
            ins: Ins.Frag = Ins.Frag()
            match n.choice:
                # <legal_instruction> ::= <b_type_instruction>;
                case 0:
                    ins += Ins.Frag(0b0, 1)
                    ins += self(n[0][0])
                    ins += self(n[0][1])
                    ins += self(n[0][2])
                    ins += Ins.Frag(n[0][3].literal, 20, True)

                # <legal_instruction> ::= <oi_type_instruction>;
                case 1:
                    ins += Ins.Frag(0b10, 2)
                    ins += self(n[0][0])
                    ins += self(n[0][1])
                    ins += self(n[0][2])
                    ins += Ins.Frag(n[0][3].literal, 16, True)

                # <legal_instruction> ::= <m_type_instruction>;
                case 2:
                    ins += Ins.Frag(0b110, 3)
                    ins += self(n[0][0])
                    ins += self(n[0][1])
                    ins += self(n[0][2])
                    ins += Ins.Frag(n[0][3].literal, 18, True)

                # <legal_instruction> ::= <o_type_instruction>;
                case 3:
                    ins += Ins.Frag(0b1110, 4)
                    ins += self(n[0][0])
                    ins += self(n[0][1])
                    ins += self(n[0][2])
                    ins += self(n[0][3])
                    ins += Ins.Frag(0, 9)

                # <legal_instruction> ::= <j_type_instruction>;
                case 4:
                    ins += Ins.Frag(0b11110, 5)
                    ins += self(n[0][0])
                    ins += Ins.Frag(n[0][1].literal, 27, True)

                # <legal_instruction> ::= <e_type_instruction>;
                case 5:
                    ins += Ins.Frag(0b111110, 6)
                    ins += self(n[0][0])
                    ins += Ins.Frag(0, 25)

            ins_count += 1
            return ins()

        def _visit_b_type_command(self, n: ASTNode, **_: Any) -> Ins.Frag:
            return Ins.Frag(n.choice, 1)

        def _visit_oi_type_command(self, n: ASTNode, **_: Any) -> Ins.Frag:
            return Ins.Frag(n.choice, 4)

        def _visit_m_type_command(self, n: ASTNode, **_: Any) -> Ins.Frag:
            return Ins.Frag(n.choice, 1)

        def _visit_o_type_command(self, n: ASTNode, **_: Any) -> Ins.Frag:
            return Ins.Frag(n.choice, 4)

        def _visit_j_type_command(self, n: ASTNode, **_: Any) -> Ins.Frag:
            return Ins.Frag(n.choice, 0)

        def _visit_e_type_command(self, n: ASTNode, **_: Any) -> Ins.Frag:
            return Ins.Frag(n.choice, 1)

        def _resolve(
            self, n: ASTNode, label_n: ASTNode, label_map: dict[str, int], **_: Any
        ) -> int:
            return label_map[label_n.lexeme] - n.extras["loc"]

        def _visit_pseudoinstruction(
            self, n: ASTNode, label_map: dict[str, int], **ctx: Any
        ) -> Ins:
            def ins(code: str) -> ASTNode:
                n_: ASTNode = A.Parse()(code, entry_point="<instruction>")
                return n_

            match n.choice:
                # <pseudoinstruction> ::= "j" <lbl>;
                case 1:
                    return self(
                        ins(f"addi pc pc {self._resolve(n, n[1], label_map)}"), **ctx
                    )

                # <pseudoinstruction> ::= "bne" <reg> zr <lbl>;
                case 3:
                    return self(
                        ins(
                            f"bne {n[1].lexeme} zr {self._resolve(n, n[3], label_map)}"
                        ),
                        **ctx,
                    )

                # <pseudoinstruction> ::= "beq" <reg> <reg> <lbl>;
                case 4:
                    return self(
                        ins(
                            f"bne {n[1].lexeme} {n[2].lexeme} {self._resolve(n, n[3], label_map)}"
                        ),
                        **ctx,
                    )

                # <pseudoinstruction> ::= "bne" <reg> <reg> <lbl>;
                case 5:
                    return self(
                        ins(
                            f"bne {n[1].lexeme} {n[2].lexeme} {self._resolve(n, n[3], label_map)}"
                        ),
                        **ctx,
                    )

                # <pseudoinstruction> ::= "setv" <reg> <lbl>;
                case 11:
                    return self(
                        ins(
                            f"addi {n[1].lexeme} pc {self._resolve(n, n[2], label_map)}"
                        ),
                        **ctx,
                    )

                case _:  # pragma: no cover
                    assert False

        # todo: terrible typing
        def _visit_constant_definition(self, n: ASTNode, **_) -> Prog:
            # do not forget '\0'!!!
            return cast(
                Prog, bytes(list(ord(c) for c in unescape(n[0].lexeme[1:-1])) + [0])
            )

        def _visit_reg(self, n: ASTNode, **_) -> Ins.Frag:
            return MP0.reg(n.lexeme)
