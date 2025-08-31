from io import StringIO

from lexer import Cursor, Source, Token
import hbnf


def regenerate_source(tokens: list[Token]) -> str:
    with StringIO() as s:
        row: int = 0
        col: int = 0
        for token in tokens:
            cursor: Cursor = token.rng.start
            s.write("\n" * (cursor.row - row))
            if cursor.row > row:
                row = cursor.row
                col = 0
            s.write(" " * (cursor.col - col))
            s.write(token.lexeme)
            col = token.rng.end.col
        s.seek(0)
        return s.read()


def test_bootstrap():
    src: Source = Source.from_file("hbnf.hbnf")
    tokens: list[Token] = hbnf.Lexer().lex(src)
    assert src.src == regenerate_source(tokens)

    ast: hbnf.Hbnf = hbnf.Parser().parse(tokens)
    # print(hbnf.ast_str(ast))

    import lexer

    BUILTINS: dict[str, type[Token]] = {
        '"?"': hbnf.Question,
        '"*"': hbnf.Asterisk,
        '"+"': hbnf.Plus,
        '":"': hbnf.Colon,
        '";"': hbnf.Semicolon,
        "identifier": hbnf.Identifier,
        "string": hbnf.String,
        '"{"': lexer.LeftBrace,
        '"}"': lexer.RightBrace,
        '"("': lexer.LeftParenthesis,
        '")"': lexer.RightParenthesis,
    }

    # todo: python codegen helper -> python hbnf
    from python_codegen import (
        Python,
        Class,
        Function,
        If,
        For,
        While,
        Try,
        Except,
        Statement,
        Statements,
        sep_join,
        join,
    )

    import sys

    og_write = sys.stdout.write
    sys.stdout.write = lambda *_, **__: None  # type: ignore

    non_builtin_terminal_defns: list[Statement] = []
    class_defns: list[Statement] = []
    parser_defn: list[Statement] = []

    non_builtin_terminal_idx: int = 1

    prods: list[hbnf.Prod] = ast.prods
    symbols: set[str] = set()
    terminals: set[str] = set()
    type_name: dict[str, str] = {}
    for prod in prods:
        lhs: str = prod.nonterm.identifier.lexeme
        if lhs in BUILTINS:
            raise ValueError(f"cannot define rules for {lhs} -- builtin nonterminal")
        # todo: deny repeat productions
        symbols.add(lhs)
        type_name[lhs] = lhs
        for rule in prod.rules:
            for factor in rule.factors:
                symbol: str
                match factor.symbol:
                    case hbnf.SymbolUnnamedVariant1(nonterm):
                        symbol = nonterm.lexeme
                        if symbol in BUILTINS:
                            terminals.add(symbol)
                            # todo: ew
                            type_name[symbol] = BUILTINS[symbol].__name__

                    case hbnf.SymbolUnnamedVariant2(term):
                        symbol = term.lexeme
                        terminals.add(symbol)
                        if symbol in BUILTINS:
                            # todo: ew
                            type_name[symbol] = BUILTINS[symbol].__name__
                        else:
                            # non-builtin terminal -> exact match
                            terminal_type_name: str = (
                                f"NonBuiltinTerminal{non_builtin_terminal_idx}"
                            )
                            non_builtin_terminal_idx += 1
                            type_name[symbol] = terminal_type_name
                            non_builtin_terminal_defns.append(
                                f"{terminal_type_name}: type[Token] = Token.define({symbol}, r{symbol})"
                            )

                symbols.add(symbol)

    imports: Statements = Statements(
        [
            "from dataclasses import dataclass",
            "from typing import Iterator, TypeAlias",
            "",
            "# todo: ...",
            "from test_hbnf import regenerate_source",
            "from lexer import Cursor, Source, Token",
            "from utils import oxford",
            "import hbnf",
            "",
            "# todo: move to ast.py or smth",
            "from hbnf import Node, InternalNode",
            f"from hbnf import {', '.join(type_name[symbol] for symbol in terminals if symbol in BUILTINS)}",
        ]
    )

    print("from dataclasses import dataclass")
    print("from typing import Iterator, TypeAlias")
    print()
    # todo: ...
    print("from test_hbnf import regenerate_source")
    print("from lexer import Cursor, Source, Token")
    print("from utils import oxford")
    print("import hbnf")
    # todo: move to ast.py or smth
    print("from hbnf import Node, InternalNode")
    print(
        f"from hbnf import {', '.join(type_name[symbol] for symbol in terminals if symbol in BUILTINS)}"
    )
    print()

    # todo: move this logic up after pythong codegen helper
    for symbol in terminals:
        if symbol not in BUILTINS:
            print(
                f"{type_name[symbol]}: type[Token] = Token.define({symbol}, r{symbol})"
            )

    # todo: dont need this?
    for prod in ast.prods:
        lhs: str = prod.nonterm.lexeme
        print(f"class {lhs}: ...")

    print()

    for prod in ast.prods:
        lhs: str = prod.nonterm.lexeme
        match len(prod.rules):
            case 1:
                # todo: dedup code: generate_single_rule_symbol_class
                rule: hbnf.Rule = prod.rules[0]
                fields: Statements = Statements()
                iter_fn: Function = Function("__iter__", "self", "Iterator[Node]")
                lhs_class_defn: Class = Class(
                    lhs,
                    dataclass=True,
                    base="InternalNode",
                    statements=[
                        fields,
                        "",
                        iter_fn,
                    ],
                )
                class_defns.append(lhs_class_defn)

                print(f"@dataclass")
                print(f"class {lhs}(InternalNode):")
                for factor_idx, factor in enumerate(rule.factors, 1):
                    varname: str = f"factor{factor_idx}"
                    base_type: str = type_name[factor.symbol.lexeme]

                    def maybe_type_ignore(s: str) -> str:
                        if factor.symbol.lexeme in BUILTINS:
                            return f"{s}  # type: ignore"
                        else:
                            return s

                    match factor.mult:
                        case None:
                            # todo: try to fix type check error?
                            print(maybe_type_ignore(f"    {varname}: {base_type}"))
                            fields += maybe_type_ignore(f"{varname}: {base_type}")

                        case hbnf.MultUnnamedVariant1():
                            # todo: try to fix type check error?
                            print(
                                maybe_type_ignore(f"    {varname}: {base_type} | None")
                            )
                            fields += maybe_type_ignore(
                                f"{varname}: {base_type} | None"
                            )

                        case hbnf.MultUnnamedVariant2() | hbnf.MultUnnamedVariant3():
                            # todo: tuple instead of list?
                            # todo: try to fix type check error?
                            print(
                                maybe_type_ignore(f"    {varname}: list[{base_type}]")
                            )
                            fields += maybe_type_ignore(f"{varname}: list[{base_type}]")

                print()
                print(f"    def __iter__(self) -> Iterator[Node]:")
                for factor_idx, factor in enumerate(rule.factors, 1):
                    varname: str = f"self.factor{factor_idx}"
                    match factor.mult:
                        case None:
                            print(f"        yield {varname}")
                            iter_fn += f"yield {varname}"

                        case hbnf.MultUnnamedVariant1():
                            print(f"        if {varname}:")
                            print(f"            yield {varname}")
                            iter_fn += If(varname, [f"yield {varname}"])

                        case hbnf.MultUnnamedVariant2() | hbnf.MultUnnamedVariant3():
                            print(f"        yield from {varname}")
                            iter_fn += f"yield from {varname}"

            case _:
                for rule_idx, rule in enumerate(prod.rules, 1):
                    fields: Statements = Statements()
                    iter_fn: Function = Function("__iter__", "self", "Iterator[Node]")
                    variant_class_defn: Class = Class(
                        f"{lhs}UnnamedVariant{rule_idx}",
                        dataclass=True,
                        base="InternalNode",
                        statements=[
                            fields,
                            "",
                            iter_fn,
                        ],
                    )
                    class_defns.append(variant_class_defn)

                    print(f"@dataclass")
                    print(f"class {lhs}UnnamedVariant{rule_idx}(InternalNode):")
                    for factor_idx, factor in enumerate(rule.factors, 1):
                        varname: str = f"factor{factor_idx}"
                        base_type: str = type_name[factor.symbol.lexeme]

                        def maybe_type_ignore(s: str) -> str:
                            if factor.symbol.lexeme in BUILTINS:
                                return f"{s}  # type: ignore"
                            else:
                                return s

                        match factor.mult:
                            case None:
                                # todo: try to fix type check error?
                                print(maybe_type_ignore(f"    {varname}: {base_type}"))
                                fields += maybe_type_ignore(f"{varname}: {base_type}")

                            case hbnf.MultUnnamedVariant1():
                                # todo: try to fix type check error?
                                print(
                                    maybe_type_ignore(
                                        f"    {varname}: {base_type} | None"
                                    )
                                )
                                fields += maybe_type_ignore(
                                    f"{varname}: {base_type} | None"
                                )

                            case (
                                hbnf.MultUnnamedVariant2() | hbnf.MultUnnamedVariant3()
                            ):
                                # todo: try to fix type check error?
                                print(
                                    maybe_type_ignore(
                                        f"    {varname}: list[{base_type}]"
                                    )
                                )
                                fields += maybe_type_ignore(
                                    f"{varname}: list[{base_type}]"
                                )

                    print()
                    print(f"    def __iter__(self) -> Iterator[Node]:")
                    for factor_idx, factor in enumerate(rule.factors, 1):
                        varname: str = f"self.factor{factor_idx}"
                        match factor.mult:
                            case None:
                                print(f"        yield {varname}")
                                iter_fn += f"yield {varname}"

                            case hbnf.MultUnnamedVariant1():
                                print(f"        if {varname}:")
                                print(f"            yield {varname}")
                                iter_fn += If(varname, [f"yield {varname}"])

                            case (
                                hbnf.MultUnnamedVariant2() | hbnf.MultUnnamedVariant3()
                            ):
                                print(f"        yield from {varname}")
                                iter_fn += f"yield from {varname}"

                    print()

                print(
                    f"{lhs}: TypeAlias = {' | '.join([f'{lhs}UnnamedVariant{idx}' for idx, _ in enumerate(prod.rules, 1)])}"
                )
                class_defns.append(
                    f"{lhs}: TypeAlias = {' | '.join([f'{lhs}UnnamedVariant{idx}' for idx, _ in enumerate(prod.rules, 1)])}"
                )

        print()

    print(
        """
class Parser:
    # todo: how to properly do exceptions?
    class Error(Exception):
        def __init__(self, src: Source, pos: Cursor, msg: str = "an error occurred"):
            rows_to_show: list[int] = list(
                range(max(0, pos.row - 3), min(src.rows, pos.row + 3))
            )
            # todo: this should come from utils lib for text column formatting
            # todo: also move this visualization code into Source
            line_num_width: int = max(len(str(row + 1)) for row in rows_to_show)
            rows: list[str] = [
                f"  {row + 1:>{line_num_width}} {src.lines[row]}"
                for row in rows_to_show
            ]
            rows.insert(
                rows_to_show.index(pos.row) + 1,
                f"  {' ' * line_num_width} {' ' * pos.col}^",
            )
            super().__init__("\\n".join([msg] + rows))

    class Instance:
        def __init__(self, tokens: list[Token]):
            if not tokens:
                # todo: possible to make Parser.Error better to account for this?
                raise ValueError("empty source")
            self.tokens: list[Token] = tokens
            # todo: kinda ugly
            self.src: Source = self.tokens[0].src
            self.idx: int = 0

        def at_end(self) -> bool:
            return self.idx >= len(self.tokens)

        def peek(self) -> Token:
            assert not self.at_end()
            return self.tokens[self.idx]

        def lookahead(self, *token_types: type[Token]) -> Token | None:
            if self.at_end():
                return None

            token: Token = self.peek()
            for token_type in token_types:
                if isinstance(token, token_type):
                    return token

            return None

        def advance(self):
            assert not self.at_end()
            self.idx += 1

        def consume(self) -> Token:
            token: Token = self.peek()
            self.advance()
            return token

        # todo: return type should be union of token_type -- is it even possible?
        def expect(self, *token_types: type[Token]) -> Token:
            if self.at_end():
                raise Parser.Error(
                    self.src,
                    self.tokens[-1].rng.end,
                    f"expected {oxford(token_type.name() for token_type in token_types)} but reached eof",
                )

            token: Token = self.peek()
            if not any(isinstance(token, token_type) for token_type in token_types):
                raise Parser.Error(
                    self.src,
                    token.rng.start,
                    f"expected {oxford(token_type.name() for token_type in token_types)} but got {token.name()}",
                )

            self.advance()
            return token

        # todo: return type should be token_type | None -- is it even possible?
        def maybe(self, *token_types: type[Token]) -> Token | None:
            return self.expect(*token_types) if self.lookahead(*token_types) else None

"""
    )

    parser_defn.append(
        join(
            [
                "# todo: how to properly do exceptions?",
                Class(
                    "Error",
                    base="Exception",
                    statements=[
                        Function(
                            "__init__",
                            'self, src: Source, pos: Cursor, msg: str = "an error occurred"',
                            statements=[
                                "rows_to_show: list[int] = list(range(max(0, pos.row - 3), min(src.rows, pos.row + 3)))",
                                "# todo: this should come from utils lib for text column formatting",
                                "# todo: also move this visualization code into Source",
                                "line_num_width: int = max(len(str(row + 1)) for row in rows_to_show)",
                                'rows: list[str] = [f"  {row + 1:>{line_num_width}} {src.lines[row]}" for row in rows_to_show]',
                                "rows.insert(rows_to_show.index(pos.row) + 1, f\"  {' ' * line_num_width} {' ' * pos.col}^\")",
                                'super().__init__("\\n".join([msg] + rows))',
                            ],
                        ),
                    ],
                ),
            ]
        )
    )

    parser_inst_defn: list[Statement] = [
        Function(
            "__init__",
            "self, tokens: list[Token]",
            statements=[
                If(
                    "not tokens",
                    [
                        "# todo: possible to make Parser.Error better to account for this?",
                        'raise ValueError("empty source")',
                    ],
                ),
                "self.tokens: list[Token] = tokens",
                "# todo: kinda ugly",
                "self.src: Source = self.tokens[0].src",
                "self.idx: int = 0",
            ],
        ),
        Function("at_end", "self", "bool", ["return self.idx >= len(self.tokens)"]),
        Function(
            "peek",
            "self",
            "Token",
            ["assert not self.at_end()", "return self.tokens[self.idx]"],
        ),
        Function(
            "lookahead",
            "self, *token_types: type[Token]",
            "Token | None",
            [
                If("self.at_end()", ["return None"]),
                "",
                "token: Token = self.peek()",
                For(
                    "token_type",
                    "token_types",
                    [If("isinstance(token, token_type)", ["return token"])],
                ),
                "",
                "return None",
            ],
        ),
        Function(
            "advance",
            "self",
            statements=[
                "assert not self.at_end",
                "self.idx += 1",
            ],
        ),
        Function(
            "consume",
            "self",
            "Token",
            [
                "token: Token = self.peek()",
                "self.advance()",
                "return token",
            ],
        ),
        join(
            [
                "# todo: return type should be union of token_type -- is it even possible?",
                Function(
                    "expect",
                    "self, *token_types: type[Token]",
                    "Token",
                    [
                        If(
                            "self.at_end()",
                            [
                                'raise Parser.Error(self.src, self.tokens[-1].rng.end, f"expected {oxford(token_type.name() for token_type in token_types)} but reached eof")'
                            ],
                        ),
                        "",
                        "token: Token = self.peek()",
                        If(
                            "not any(isinstance(token, token_type) for token_type in token_types)",
                            [
                                'raise Parser.Error(self.src, self.tokens[-1].rng.end, f"expected {oxford(token_type.name() for token_type in token_types)} but got {token.name()}")'
                            ],
                        ),
                        "",
                        "self.advance()",
                        "return token",
                    ],
                ),
            ]
        ),
        join(
            [
                "# todo: return type should be token_type | None -- is it even possible?",
                Function(
                    "maybe",
                    "self, *token_types: type[Token]",
                    "Token | None",
                    [
                        "return self.expect(*token_types) if self.lookahead(*token_types) else None"
                    ],
                ),
            ]
        ),
    ]

    def generate_single_rule_symbol_parser(symbol: str, rule: hbnf.Rule):
        nonlocal parser_inst_defn
        parse_fn: list[Statement] = []
        # todo: snake case it
        print(f"        def parse_{symbol}(self) -> {symbol}:")
        for factor_idx, factor in enumerate(rule.factors, 1):
            varname: str = f"factor{factor_idx}"
            base_type: str = type_name[factor.symbol.lexeme]

            parse_one: str
            try_parse_one: str
            if factor.symbol.lexeme in terminals:
                parse_one = f"self.expect({base_type})"
                try_parse_one = f"self.maybe({base_type})"
            else:
                parse_one = f"self.parse_{base_type}()"
                try_parse_one = f"self.try_parse_{base_type}()"

            def maybe_type_ignore(s: str) -> str:
                if factor.symbol.lexeme in BUILTINS:
                    return f"{s}  # type: ignore"
                else:
                    return s

            match factor.mult:
                case None:
                    # todo: try to fix type check error?
                    print(
                        maybe_type_ignore(
                            f"            {varname}: {base_type} = {parse_one}"
                        )
                    )
                    parse_fn.append(
                        # todo: try to fix type check error?
                        maybe_type_ignore(f"{varname}: {base_type} = {parse_one}")
                    )

                case hbnf.MultUnnamedVariant1():
                    # todo: try to fix type check error?
                    print(
                        maybe_type_ignore(
                            f"            {varname}: {base_type} | None = {try_parse_one}"
                        )
                    )
                    parse_fn.append(
                        # todo: try to fix type check error?
                        maybe_type_ignore(
                            f"{varname}: {base_type} | None = {try_parse_one}"
                        )
                    )

                case hbnf.MultUnnamedVariant2() | hbnf.MultUnnamedVariant3():
                    # todo: try to fix type check error?
                    print(
                        maybe_type_ignore(
                            f"            {varname}: list[{base_type}] = []"
                        )
                    )
                    print(
                        maybe_type_ignore(
                            f"            {varname}_item: {base_type} | None"
                        )
                    )
                    print(f"            while {varname}_item := {try_parse_one}:")
                    print(f"                {varname}.append({varname}_item)")
                    parse_fn.append(
                        join(
                            [
                                # todo: try to fix type check error?
                                maybe_type_ignore(f"{varname}: list[{base_type}] = []"),
                                maybe_type_ignore(
                                    f"{varname}_item: {base_type} | None"
                                ),
                                While(
                                    f"{varname}_item := {try_parse_one}",
                                    [f"{varname}.append({varname}_item)"],
                                ),
                            ]
                        )
                    )

            print()

        print(
            f"            return {symbol}({', '.join(f'factor{factor_idx}' for factor_idx, _ in enumerate(rule.factors, 1))})"
        )
        parse_fn.append(
            f"return {symbol}({', '.join(f'factor{factor_idx}' for factor_idx, _ in enumerate(rule.factors, 1))})"
        )
        print()

        parser_inst_defn.append(
            Function(f"parse_{symbol}", "self", symbol, [sep_join(parse_fn)])
        )

        print(f"        def try_parse_{symbol}(self) -> {symbol} | None:")
        print(f"            idx: int = self.idx")
        print(f"            try:")
        print(f"                return self.parse_{symbol}()")
        # todo: Parser.Exception
        print(f"            except Exception:")
        print(f"                self.idx = idx")
        print(f"                return None")
        print()

        parser_inst_defn.append(
            Function(
                f"try_parse_{symbol}",
                "self",
                f"{symbol} | None",
                [
                    "idx: int = self.idx",
                    Try([f"return self.parse_{symbol}()"]),
                    # todo: Parser.Exception
                    Except("Exception", ["self.idx = idx", "return None"]),
                ],
            )
        )

    for prod in ast.prods:
        lhs: str = prod.nonterm.identifier.lexeme
        match len(prod.rules):
            case 1:
                generate_single_rule_symbol_parser(lhs, prod.rules[0])

            case _:
                for rule_idx, rule in enumerate(prod.rules, 1):
                    generate_single_rule_symbol_parser(
                        f"{lhs}UnnamedVariant{rule_idx}", rule
                    )

                parse_defn: list[Statement] = [f"result: {lhs} | None"]
                print(f"        def parse_{lhs}(self) -> {lhs}:")
                print(f"            result: {lhs} | None")
                for rule_idx, rule in enumerate(prod.rules, 1):
                    print(
                        f"            if (result := self.try_parse_{lhs}UnnamedVariant{rule_idx}()) is not None:"
                    )
                    print(f"                return result")
                    print()
                    parse_defn.append(
                        If(
                            f"(result := self.try_parse_{lhs}UnnamedVariant{rule_idx}()) is not None",
                            ["return result"],
                        )
                    )

                # todo: sad message... also raise Parser.Error instead
                print(f'            raise ValueError("could not parse")')
                print()
                # todo: sad message... also raise Parser.Error instead
                parse_defn.append('raise ValueError("could not parse")')

                parser_inst_defn.append(
                    Function(f"parse_{lhs}", "self", lhs, [sep_join(parse_defn)])
                )

                print(f"        def try_parse_{lhs}(self) -> {lhs} | None:")
                print(f"            idx: int = self.idx")
                print(f"            try:")
                print(f"                return self.parse_{lhs}()")
                # todo: Parser.Exception
                print(f"            except Exception:")
                print(f"                self.idx = idx")
                print(f"                return None")
                print()

                parser_inst_defn.append(
                    Function(
                        f"try_parse_{lhs}",
                        "self",
                        f"{lhs} | None",
                        [
                            "idx: int = self.idx",
                            Try([f"return self.parse_{lhs}()"]),
                            # todo: Parser.Exception
                            Except("Exception", ["self.idx = idx", "return None"]),
                        ],
                    )
                )

        print()

    parser_defn.append(
        sep_join([Class("Instance", statements=[sep_join(parser_inst_defn)])])
    )

    print(
        """
src: Source = Source.from_file("hbnf.hbnf")
tokens: list[Token] = hbnf.Lexer().lex(src)
assert src.src == regenerate_source(tokens)

ast: hbnf.Hbnf = hbnf.Parser().parse(tokens)
print(hbnf.ast_str(ast))
        """
    )

    main: Statements = Statements(
        [
            'src: Source = Source.from_file("hbnf.hbnf")',
            "tokens: list[Token] = hbnf.Lexer().lex(src)",
            "assert src.src == regenerate_source(tokens)",
            "",
            "ast: hbnf.Hbnf = hbnf.Parser().parse(tokens)",
            "print(hbnf.ast_str(ast))",
        ]
    )

    code: Python = Python(
        [
            sep_join(
                [
                    "from __future__ import annotations",
                    imports,
                    sep_join(non_builtin_terminal_defns),
                    sep_join(class_defns),
                    Class("Parser", statements=[sep_join(parser_defn)]),
                    main,
                ]
            )
        ]
    )

    sys.stdout.write = og_write
    print(code)


if __name__ == "__main__":
    test_bootstrap()
