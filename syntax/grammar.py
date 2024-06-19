from __future__ import annotations
from collections import defaultdict
from typing import Optional, Callable, Union, Any

from common import Monad, Log
from lexical import Vocabulary, Lexer

from .ast import ASTNode
from .parser import ExpressionTerm, Parser
from .visitor import Visitor


class Grammar:
    def __init__(
        self,
        name: str,
        xbnf: Optional[str] = None,
        vocabulary: Optional[Vocabulary] = None,
        node_parsers: Optional[
            dict[str, Callable[[Parser, Optional[bool]], Optional[ASTNode]]]
        ] = None,
        ignore: list[str] = [],
    ):
        if xbnf is not None and (vocabulary is not None or node_parsers is not None):
            Log.w("more than sufficient arguments provided", tag="Grammar")

        if vocabulary is None:
            if xbnf is None:
                error: ValueError = ValueError(
                    "provide either xbnf or both vocabulary and node_parsers to create a grammar"
                )
                if not Log.ef(
                    "[red]ValueError:[/red] provide either xbnf or both vocabulary and node_parsers to create a grammar"
                ):
                    raise error

            ast: ASTNode = (
                Monad(xbnf)
                .then(Lexer(xbnf_grammar).lex)
                .then(Parser(xbnf_grammar).parse)
                .value
            )

            vocabulary = VocabularyGenerator(ignore).generate(ast)
            node_parsers = NodeParsersGenerator().generate(ast)

        elif node_parsers is None:
            error: ValueError = ValueError(
                "provide either xbnf or both vocabulary and node_parsers to create a grammar"
            )
            if not Log.ef(
                "[red]ValueError:[/red] provide either xbnf or both vocabulary and node_parsers to create a grammar"
            ):
                raise error

        # todo: validate input grammar
        self._name: str = name
        self._vocabulary: Vocabulary = vocabulary
        self._node_parsers: dict[
            str, Callable[[Parser, Optional[bool]], Optional[ASTNode]]
        ] = node_parsers

    @property
    def name(self) -> str:
        return self._name

    @property
    def vocabulary(self) -> Vocabulary:
        return self._vocabulary

    @property
    def node_parsers(self) -> dict[str : Callable[[Parser], Optional[ASTNode]]]:
        return self._node_parsers

    @property
    def entry_point(self) -> str:
        return f"<{self._name}>"


xbnf_vocabulary = Vocabulary(
    {
        '"<"': Vocabulary.Definition.make("<"),
        "identifier": Vocabulary.Definition.builtin["identifier"],
        '">"': Vocabulary.Definition.make(">"),
        '"::="': Vocabulary.Definition.make("::="),
        '"\\+"': Vocabulary.Definition.make("\\+"),
        '";"': Vocabulary.Definition.make(";"),
        "escaped_string": Vocabulary.Definition.builtin["escaped_string"],
        '"\\("': Vocabulary.Definition.make("\\("),
        '"\\?"': Vocabulary.Definition.make("\\?"),
        '"\\)"': Vocabulary.Definition.make("\\)"),
        '"\\*"': Vocabulary.Definition.make("\\*"),
        '"\\|"': Vocabulary.Definition.make("\\|"),
    }
)

xbnf_node_parsers = {
    "<xbnf>": Parser.generate_nonterminal_parser(
        "<xbnf>",
        [
            [ExpressionTerm("<production>", "+")],
        ],
    ),
    "<production>": Parser.generate_nonterminal_parser(
        "<production>",
        [
            [
                ExpressionTerm("<nonterminal>"),
                ExpressionTerm('"::="'),
                ExpressionTerm("<body>"),
                ExpressionTerm('";"'),
            ],
        ],
    ),
    "<nonterminal>": Parser.generate_nonterminal_parser(
        "<nonterminal>",
        [
            [
                ExpressionTerm('"<"'),
                ExpressionTerm("identifier"),
                ExpressionTerm('">"'),
            ],
        ],
    ),
    "<body>": Parser.generate_nonterminal_parser(
        "<body>",
        [
            [
                ExpressionTerm("<expression>"),
                ExpressionTerm("<body>:1", "*"),
            ],
        ],
    ),
    "<body>:1": Parser.generate_nonterminal_parser(
        "<body>:1",
        [
            [
                ExpressionTerm('"\\|"'),
                ExpressionTerm("<expression>"),
            ],
        ],
    ),
    "<expression>": Parser.generate_nonterminal_parser(
        "<expression>",
        [
            [
                ExpressionTerm("<expression>:0", "+"),
            ],
        ],
    ),
    "<expression>:0": Parser.generate_nonterminal_parser(
        "<expression>:0",
        [
            [
                ExpressionTerm("<group>"),
                ExpressionTerm("<multiplicity>", "?"),
            ],
        ],
    ),
    "<group>": Parser.generate_nonterminal_parser(
        "<group>",
        [
            [ExpressionTerm("<term>")],
            [
                ExpressionTerm('"\\("'),
                ExpressionTerm("<body>"),
                ExpressionTerm('"\\)"'),
            ],
        ],
    ),
    "<term>": Parser.generate_nonterminal_parser(
        "<term>",
        [
            [ExpressionTerm("<nonterminal>")],
            [ExpressionTerm("<terminal>")],
        ],
    ),
    "<terminal>": Parser.generate_nonterminal_parser(
        "<terminal>",
        [
            [ExpressionTerm("escaped_string")],
            [ExpressionTerm("identifier")],
        ],
    ),
    "<multiplicity>": Parser.generate_nonterminal_parser(
        "<multiplicity>",
        [
            [ExpressionTerm('"\\?"')],
            [ExpressionTerm('"\\*"')],
            [ExpressionTerm('"\\+"')],
            [ExpressionTerm("decimal_integer")],
        ],
    ),
    '"::="': Parser.generate_terminal_parser('"::="'),
    '";"': Parser.generate_terminal_parser('";"'),
    '"<"': Parser.generate_terminal_parser('"<"'),
    '">"': Parser.generate_terminal_parser('">"'),
    '"\\|"': Parser.generate_terminal_parser('"\\|"'),
    '"\\("': Parser.generate_terminal_parser('"\\("'),
    '"\\)"': Parser.generate_terminal_parser('"\\)"'),
    "escaped_string": Parser.generate_terminal_parser("escaped_string"),
    "identifier": Parser.generate_terminal_parser("identifier"),
    '"\\?"': Parser.generate_terminal_parser('"\\?"'),
    '"\\*"': Parser.generate_terminal_parser('"\\*"'),
    '"\\+"': Parser.generate_terminal_parser('"\\+"'),
    "decimal_integer": Parser.generate_terminal_parser("decimal_integer"),
}

xbnf_grammar: Grammar = Grammar(
    "xbnf",
    vocabulary=xbnf_vocabulary,
    node_parsers=xbnf_node_parsers,
)


class VocabularyGenerator(Visitor):
    def __init__(self, ignore: list[str] = []):
        super().__init__(
            {"escaped_string": self._visit_escaped_string},
            Visitor.visit_all,
        )
        self._ignore: list[str] = Vocabulary.DEFAULT_IGNORE
        self._ignore.extend(ignore)

    def generate(self, ast: ASTNode) -> Vocabulary:
        self._dictionary: dict[str, Vocabulary.Definition] = {}
        self.visit(ast)
        return Vocabulary(self._dictionary, ignore=self._ignore)

    def _visit_escaped_string(
        self,
        node: ASTNode,
        _: Visitor,
    ) -> None:
        if node.lexeme not in self._dictionary:
            self._dictionary[node.lexeme] = Vocabulary.Definition.make(node.literal)


class NodeParsersGenerator(Visitor):
    def __init__(self):
        super().__init__(
            {
                "<xbnf>": self._visit_xbnf,
                "<production>": self._visit_production,
                "<body>": self._visit_body,
                "<expression>": self._visit_expression,
                "<group>": self._visit_group,
                "<multiplicity>": self._visit_multiplicity,
            }
        )

    def generate(
        self, ast: ASTNode
    ) -> dict[str, Callable[[Parser], Optional[ASTNode]]]:
        self._productions = defaultdict(list[ExpressionTerm])
        # todo: this is ugly, move to call stack
        self._lhs_stack: list[str] = []
        self._idx_stack: list[int] = []
        self._used: set[str] = set()
        # entry point is used
        self._used.add(f"<{ast[0][0][0][1].lexeme}>")
        self._node_parsers: dict[
            str, Callable[[Parser, Optional[bool]], Optional[ASTNode]]
        ] = {}
        self.visit(ast)

        for node_type in self._used:
            if node_type not in self._node_parsers:
                # todo: assert node_type is a nontemrinal
                error: ValueError = ValueError(
                    f"no productions defined for {node_type}"
                )
                if not Log.ef(
                    f"[red]ValueError:[/red] no productions defined for {node_type}"
                ):
                    raise error

        # todo: analyze tree from entry nonterminal to determine disconnected components
        # todo: currently this does not detect <x> ::= <y>; <y> ::= <x>;
        for node_type in self._node_parsers:
            Log.w(
                f"parsers are generated for {node_type} but not used",
                node_type not in self._used,
                tag="Grammar",
            )

        return self._node_parsers

    def _add_terminal(self, terminal: str) -> None:
        if terminal not in self._node_parsers:
            self._used.add(terminal)
            self._node_parsers[terminal] = Parser.generate_terminal_parser(terminal)

    def _add_nonterminal(
        self, nonterminal: str, body: list[list[ExpressionTerm]]
    ) -> None:
        if nonterminal not in self._node_parsers:
            self._node_parsers[nonterminal] = Parser.generate_nonterminal_parser(
                nonterminal, body
            )
        else:
            Log.w(
                f"multiple production definitions for {nonterminal} are disregarded",
                tag="Grammar",
            )

    def _visit_xbnf(
        self,
        node: ASTNode,
        visitor: Visitor,
    ) -> Any:
        # node[0]: <production>+
        # production: <production>
        for production in node[0]:
            visitor.visit(production)

    def _visit_production(
        self,
        node: ASTNode,
        visitor: Visitor,
    ) -> Any:
        nonterminal: str = f"<{node[0][1].lexeme}>"

        self._lhs_stack.append(nonterminal)
        self._idx_stack.append(0)

        # not using extend => force 1 production definition for each nonterminal
        self._add_nonterminal(nonterminal, visitor.visit(node[2]))

        self._idx_stack.pop()
        self._lhs_stack.pop()

    def _visit_body(
        self,
        node: ASTNode,
        visitor: Visitor,
    ) -> list[list[ExpressionTerm]]:
        productions: list[list[ExpressionTerm]] = []

        # only 1 production
        if len(node[1]) == 0:
            # node[0]: <expression>
            productions.append(visitor.visit(node[0]))

        # multiple productions
        else:

            auxiliary_nonterminal = f"{self._lhs_stack[-1]}~{self._idx_stack[-1]}"
            self._lhs_stack.append(auxiliary_nonterminal)
            self._idx_stack.append(0)

            # node[0]: <expression>
            productions.append(visitor.visit(node[0]))

            self._idx_stack.pop()
            self._lhs_stack.pop()
            self._idx_stack[-1] += 1

        # node[1]: ("\|" <expression>)*
        # or_production: "\|" <expression>
        for or_production in node[1]:
            auxiliary_nonterminal = f"{self._lhs_stack[-1]}~{self._idx_stack[-1]}"
            self._lhs_stack.append(auxiliary_nonterminal)
            self._idx_stack.append(0)

            # or_production[1]: <expression>
            productions.append(visitor.visit(or_production[1]))

            self._idx_stack.pop()
            self._lhs_stack.pop()
            self._idx_stack[-1] += 1

        return productions

    def _visit_expression(
        self,
        node: ASTNode,
        visitor: Visitor,
    ) -> list[ExpressionTerm]:
        ret = []

        # node[0]: (<group> <multiplicity>?)+
        # expression_term: <group> <multiplicity>?
        for expression_term in node[0]:
            # multiplicity: <multiplicity>?
            optional_multiplicity: ListNonterminalASTNode = expression_term[1]

            # default multiplicity is 1
            if len(optional_multiplicity) == 0:
                multiplicity: Union[str, int] = 1

            else:
                multiplicity: Union[str, int] = visitor.visit(optional_multiplicity[0])

            # expression_term[0]: <group>
            group: str = visitor.visit(expression_term[0])

            ret.append(ExpressionTerm(group, multiplicity))

        return ret

    def _visit_group(
        self,
        node: ASTNode,
        visitor: Visitor,
    ) -> str:
        match node.choice:
            # node: <term>
            case 0:
                # term: <nonterminal> | <terminal>
                term = node[0]

                self._idx_stack[-1] += 1

                match term.choice:
                    # term: <nonterminal>
                    case 0:
                        nonterminal = f"<{term[0][1].lexeme}>"
                        self._used.add(nonterminal)
                        return nonterminal

                    # term: <terminal>
                    case 1:
                        # term[0]: escaped_string | identifier
                        terminal = term[0][0].lexeme

                        self._add_terminal(terminal)
                        return terminal

            # node: "\(" <body> "\)"
            case 1:
                auxiliary_nonterminal = f"{self._lhs_stack[-1]}:{self._idx_stack[-1]}"
                self._lhs_stack.append(auxiliary_nonterminal)
                self._idx_stack.append(0)
                self._used.add(auxiliary_nonterminal)

                # node[1]: <body>
                self._add_nonterminal(auxiliary_nonterminal, visitor.visit(node[1]))

                self._idx_stack.pop()
                self._lhs_stack.pop()
                self._idx_stack[-1] += 1

                return auxiliary_nonterminal

    def _visit_multiplicity(
        self,
        node: ASTNode,
        visitor: Visitor,
    ) -> Union[str, int]:
        match node.choice:
            # node: "\?" | "\*" | "\+"
            case 0 | 1 | 2:
                return node[0].lexeme

            # node: decimal_integer
            case 1:
                return node[0].literal
