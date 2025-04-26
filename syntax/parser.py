from __future__ import annotations
from types import new_class
from typing import NamedTuple, Callable, Any, DefaultDict
from collections import defaultdict
from itertools import pairwise, product
from sys import setrecursionlimit

# yikes
setrecursionlimit(5000)

from common import Log, ListSet, fixed_point, Graph
from lexical import Token, Vocabulary

from .ast import (
    ASTNode,
    NonterminalASTNode,
    AliasASTNode,
    TerminalASTNode,
)
from .grammar import Grammar

# todo: start delete
abcdef = 0


def fmt_rules(rules: Grammar.Rules) -> str:
    return "\n".join(str(rules).split("; "))


def fmt_grammar_rules(grammar: Grammar) -> str:
    return fmt_rules(grammar.rules)


# todo: end delete


# placing here for now cuz static methods suck
def util_dict_eq(
    a: DefaultDict[str, ListSet[str]], b: DefaultDict[str, ListSet[str]]
) -> bool:
    return (
        all(k in b for k in a)
        and all(k in a for k in b)
        and all(a[k] == b[k] for k in a)
    )


# placing here for now cuz static methods suck
def util_dict_cp(d: DefaultDict[str, ListSet[str]]) -> DefaultDict[str, ListSet[str]]:
    d_: DefaultDict[str, ListSet[str]] = defaultdict(lambda: ListSet())
    for k, v in d.items():
        d_[k] = ListSet(v)
    return d_


# todo: super sucky in terms of efficiency
def generate_first(grammar: Grammar) -> DefaultDict[str, ListSet[str]]:
    vocabulary: Vocabulary = grammar.vocabulary
    rules: Grammar.Rules = grammar.rules
    productions: dict[str, Grammar.Production] = {}

    first: DefaultDict[str, ListSet[str]] = defaultdict(lambda: ListSet())
    for terminal in vocabulary:
        first[terminal].add(terminal)
    for nonterminal in rules:
        rule: Grammar.Rule = rules[nonterminal]
        match rule:
            case Grammar.Production():
                productions[nonterminal] = rule
            case Grammar.Alias():
                first[nonterminal].add(rule.node_type)
            case _:  # pragma: no cover
                assert False

    def iterate_first(cur):
        cur = util_dict_cp(cur)  # prevent side effects to the original cur
        nxt = util_dict_cp(cur)
        for nonterminal in productions:
            production = productions[nonterminal]
            for expression in production:
                nullable = True
                for term in expression:
                    if term.node_type == "e":
                        continue
                    nxt[nonterminal] += cur[term.node_type] - ["e"]
                    if "e" not in cur[term.node_type]:
                        nullable = False
                        break

                if nullable:
                    nxt[nonterminal].add("e")
        return nxt

    return fixed_point(first, iterate_first, util_dict_eq)


# todo: super sucky in terms of efficiency
def generate_follow(grammar: Grammar) -> DefaultDict[str, ListSet[str]]:
    rules: Grammar.Rules = grammar.rules
    productions: dict[str, Grammar.Production] = {}

    for nonterminal in rules:
        rule: Grammar.Rule = rules[nonterminal]
        if type(rule) is Grammar.Production:
            productions[nonterminal] = rule

    first: DefaultDict[str, ListSet[str]] = generate_first(grammar)

    follow: DefaultDict[str, ListSet[str]] = defaultdict(lambda: ListSet())
    follow[f"<{grammar.name}>"].append("$")

    def iterate_follow(cur):
        cur = util_dict_cp(cur)  # prevent side effects to the original cur
        nxt = util_dict_cp(cur)
        for nonterminal in productions:
            production = productions[nonterminal]
            for expression in production:
                nxt[expression[-1].node_type] += cur[nonterminal] - ListSet(["e"])

                right_nullable = True
                for l_term, r_term in reversed(tuple(pairwise(expression))):
                    l, r = l_term.node_type, r_term.node_type
                    nxt[l] += first[r] - ["e"]
                    if right_nullable:
                        if "e" in first[r]:
                            nxt[l] += cur[nonterminal] - ["e"]
                        else:
                            right_nullable = False

        return nxt

    return fixed_point(follow, iterate_follow, util_dict_eq)


def sanitize_expression(expression: Grammar.Expression) -> Grammar.Expression:
    if len(expression) > 1:
        return Grammar.Expression(term for term in expression if term.node_type != "e")
    else:
        return expression


def expand_until_first_is_nonterminal(
    rules: Grammar.Rules,
    expression: Grammar.Expression,
) -> list[Grammar.Expression]:
    # todo: should move all of these checks to within Grammar.Expression (__post_init__?)
    # every expression should have at least one term
    assert expression

    expressions: list[Grammar.Expression] = [expression]
    # todo: delete
    # print(expressions)

    # todo: ugly nonterminal check
    while any(
        res_expression[0].node_type.startswith("<") for res_expression in expressions
    ):
        new_expressions: list[Grammar.Expression] = []
        for res_expression in expressions:
            branch_expressions: list[Grammar.Expression] = []
            first_term: str = res_expression[0].node_type
            # first term is nonterminal, expand this expression
            if first_term.startswith("<"):
                # this should have been expanded (if need be) already
                first_term_rule: Grammar.Rule = rules[first_term]
                if type(first_term_rule) is Grammar.Production:
                    for first_term_expression in first_term_rule:
                        # make a copy!!! this was a very difficult find
                        branch_expressions.append(
                            Grammar.Expression(first_term_expression)
                        )
                elif type(first_term_rule) is Grammar.Alias:
                    branch_expressions.append(Grammar.Expression([first_term_rule]))
                else:  # pragma: no cover
                    assert False

                for branch in branch_expressions:
                    branch.extend(res_expression[1:])

                # sanitize and add all branch expressions to result
                # sanitization is needed because first nonterminal could expand to epsilon
                # sanitization removes first term epsilons and might leave another nonterminal
                # as the first term -- need to expand again, hence the overarching while loop
                new_expressions.extend(map(sanitize_expression, branch_expressions))

            # first term is a terminal: no need to expand, just add this expression to result
            else:
                new_expressions.append(res_expression)

        # todo: begin delete
        # print(new_expressions)
        # if all(e in new_expressions for e in expressions):
        #     raise RuntimeError()
        # todo: end delete
        expressions = new_expressions

    return expressions


# output must satisfy:
# a production is either
# - single expression e, or
# - expressions of one term each
# every expression e has property len(first(e)) == 1
# ... scratch that
#
# not left-recursive means we can always expand an expression into multiple expressions
# until all expressions start with a terminal (?)
# a nonterminal n cannot ever generate expression [n, ...] in a non-left-recursive grammar
# then for every expansion of the first term, we must get an unseen nonterminal
# then, since there are a finite number of nonterminals, we will reach a terminal
# qed hooray
#
# order matters here -- it's a dag
# define a graph where nonterminal a extends an arc to nonterminal b if a's productions contains
# an expression starting w b
# then we should expand nonterminals in the reversed topological order
#
# it turns out the dag is not that simple to construct
# if a starting nonterminal expands to epsilon, it would be satinized away and possibly leave
# another nonterminal at the start -- this dependency is not captured by the graph construction
# outlined above
#
# every rule becomes one of:
# 1. single expression w multiple terms, the first term being a nonterminal
# 2. multiple expressions, each with a single terminal or a single nonterminal w rule of type 1
# this means no expression will have a nullable first term except for the expression e
def break_down(grammar: Grammar) -> Grammar:
    g: Graph[str] = Graph()

    broken_down_rules: Grammar.Rules = Grammar.Rules()

    # create graph:
    # for each expression in the production of a nonterminal n,
    # if the first term is a nonterminal n' then arc from n to n'
    # if the first term is nullable and the second term is a nonterminal n'',
    # arc from n to n''
    # continue until reaching a non-nullable term
    first: DefaultDict[str, ListSet[str]] = generate_first(grammar)
    for nonterminal, rule in grammar.rules.items():
        # ensure node exists
        g.node(nonterminal)
        if type(rule) is Grammar.Production:
            for expression in rule:
                # every expression should have at least one term
                assert expression
                for term in expression:
                    # todo: this nonterminal check is really ugly, need to fix some time
                    if term.node_type.startswith("<"):
                        g.arc(nonterminal, term.node_type)

                    # exit if term is not nullable
                    if "e" not in first[term.node_type]:
                        break

        elif type(rule) is Grammar.Alias:
            broken_down_rules[nonterminal] = rule

        else:  # pragma: no cover
            assert False

    if not g.is_dag():
        raise ValueError(f"{grammar} is left recursive")

    topological_order: list[str] = g.topological_order

    # expand nonterminals in reversed topological order -- only need to expand once!
    for nonterminal in reversed(topological_order):
        rule: Grammar.Rule = grammar.rules[nonterminal]
        # todo: delete
        # print("before:", nonterminal, "->", rule)
        if type(rule) is Grammar.Production:
            broken_down_production: Grammar.Production = Grammar.Production()
            for expression in rule:
                broken_down_production.extend(
                    expand_until_first_is_nonterminal(broken_down_rules, expression)
                )
                # todo: delete, extracted to expand_until_first_is_nonterminal()
                # # every expression should have at least one term
                # assert expression
                # first_term: str = expression[0].node_type
                # # first term is nonterminal, expand this expression
                # if first_term.startswith("<"):
                #     # the first term can possibly expand to multiple expressions
                #     branch_expressions: list[Grammar.Expression] = []
                #
                #     # this should have been expanded (if need be) already
                #     first_term_rule: Grammar.Rule = broken_down_rules[first_term]
                #     if type(first_term_rule) is Grammar.Production:
                #         for first_term_expression in first_term_rule:
                #             # make a copy!!! this was a very difficult find
                #             branch_expressions.append(
                #                 Grammar.Expression(first_term_expression)
                #             )
                #     elif type(first_term_rule) is Grammar.Alias:
                #         # todo: do this or extract the nonterminal?
                #         branch_expressions.append(Grammar.Expression([first_term_rule]))
                #     else:  # pragma: no cover
                #         assert False
                #
                #     for branch in branch_expressions:
                #         branch.extend(expression[1:])
                #
                #     # add all branch expressions to production
                #     broken_down_production.extend(branch_expressions)
                #
                # # first term is a terminal: no need to expand, just add this expression to production
                # else:
                #     broken_down_production.append(expression)

            # todo: begin delete
            # print("after:", nonterminal, "->", broken_down_production)
            # print()
            # todo: end delete
            broken_down_rules[nonterminal] = broken_down_production

            # multiple expressions: make sure each expression only has a single term
            # create auxiliary nonterminals when necessary
            # maybe this can be done in a different function -- kinda breaking
            # single responsibility here
            if len(broken_down_production) > 1:
                sanitized_broken_down_production: Grammar.Production = (
                    Grammar.Production()
                )
                for idx, expression in enumerate(broken_down_production):
                    # every expression should have at least one term
                    assert expression
                    if len(expression) > 1:
                        aux_nonterminal: str = f"{nonterminal}~{idx}"
                        sanitized_broken_down_production.append(
                            Grammar.Expression([Grammar.Term(aux_nonterminal)])
                        )
                        # todo: hopefully this does not collide w smth else
                        broken_down_rules[aux_nonterminal] = Grammar.Production(
                            [expression]
                        )
                    else:
                        sanitized_broken_down_production.append(expression)

                broken_down_rules[nonterminal] = sanitized_broken_down_production

            # todo: begin delete
            # print("after:", nonterminal, "->", broken_down_rules[nonterminal])
            # print()
            # todo: end delete

    # todo: begin delete
    # print("broken down:")
    # # print(fmt_rules(broken_down_rules))
    # print(broken_down_rules.keys())
    # print()
    # todo: end delete

    broken_down_grammar: Grammar = Grammar(grammar.name, broken_down_rules)
    # enforce output requirement w an assert
    first = generate_first(broken_down_grammar)
    # todo: delete this debug for loop
    for nonterminal, rule in broken_down_rules.items():
        if type(rule) is Grammar.Production and len(rule) == 1:
            pass
            # print(nonterminal, first[nonterminal], broken_down_rules[nonterminal])
    assert all(
        len(rule) == 1
        and len(first[nonterminal]) == 1
        or len(rule) > 1
        and all(len(expression) == 1 for expression in rule)
        for nonterminal, rule in broken_down_rules.items()
        if type(rule) is Grammar.Production
    )
    return broken_down_grammar


# todo: delete, this is old
# def break_down(grammar: Grammar) -> Grammar:
#     broken_down_rules: Grammar.Rules = Grammar.Rules()
#
#     for nonterminal, rule in grammar.rules.items():
#         # break down nonterminals with multiple expressions
#         if type(rule) is Grammar.Production and len(rule) > 1:
#             broken_down_rules[nonterminal] = Grammar.Production(
#                 (
#                     expression
#                     if len(expression) == 1
#                     else Grammar.Expression([Grammar.Term(f"{nonterminal}~{idx}")])
#                 )
#                 for idx, expression in enumerate(rule)
#             )
#             for idx, expression in enumerate(rule):
#                 if len(expression) > 1:
#                     broken_down_rules[f"{nonterminal}~{idx}"] = Grammar.Production(
#                         [expression]
#                     )
#
#         else:
#             broken_down_rules[nonterminal] = rule
#
#     return Grammar(f"broken_down_{grammar.name}", broken_down_rules)


namegen_idx: int = 0


def namegen() -> str:
    global namegen_idx
    name: str = f"intermediate_grammar_{namegen_idx}"
    namegen_idx += 1
    return name


# todo: delete, obsolete
# def expand_neq_common_first(
#     grammar: Grammar,
#     nonterminal_to_expand: str,
#     neq_common_first: list[Grammar.Expression],
# ) -> Grammar:
#     expanded_neq_common_first_rules: Grammar.Rules = Grammar.Rules()
#
#     for nonterminal, rule in grammar.rules.items():
#         if nonterminal == nonterminal_to_expand:
#             assert type(rule) is Grammar.Production
#             production: Grammar.Production = rule
#             expanded_neq_common_first_production: Grammar.Production = (
#                 Grammar.Production()
#             )
#
#             for expression in production:
#                 assert len(expression) == 1
#                 if expression in neq_common_first:
#                     expansion: Grammar.Production = grammar.rules[
#                         expression[0].node_type
#                     ]  # type: ignore
#                     expanded_neq_common_first_production.extend(expansion)
#
#                 else:
#                     expanded_neq_common_first_production.append(expression)
#
#             expanded_neq_common_first_rules[nonterminal] = (
#                 expanded_neq_common_first_production
#             )
#
#         else:
#             expanded_neq_common_first_rules[nonterminal] = rule
#
#     return Grammar(namegen(), expanded_neq_common_first_rules)
#
#
# def find_non_disjoint_expressions(
#     grammar: Grammar,
# ) -> tuple[str, list[int], ListSet[str], Grammar.Rules] | None:
#     first: DefaultDict[str, ListSet[str]] = generate_first(grammar)
#
#     for nonterminal, rule in grammar.rules.items():
#         if type(rule) is Grammar.Production and len(rule) > 1:
#             for idx, candidate_expression in enumerate(rule):
#                 assert len(candidate_expression) == 1
#                 non_disjoint_expression_idxs: list[int] = [idx]
#                 candidate_aux_nonterminal: str = candidate_expression[0].node_type
#                 common_first_so_far: ListSet[str] = first[candidate_aux_nonterminal]
#                 neq_common_first: list[Grammar.Expression] = []
#                 for off, check_expression in enumerate(rule[idx + 1 :]):
#                     assert len(check_expression) == 1
#                     check_aux_nonterminal: str = check_expression[0].node_type
#                     potential_common_first: ListSet[str] = (
#                         common_first_so_far & first[check_aux_nonterminal]
#                     )
#                     if potential_common_first:
#                         if common_first_so_far - first[check_aux_nonterminal]:
#                             neq_common_first = list(
#                                 rule[neq_common_first_idx]
#                                 for neq_common_first_idx in non_disjoint_expression_idxs
#                             )
#
#                         if first[check_aux_nonterminal] - common_first_so_far:
#                             neq_common_first.append(check_expression)
#
#                         common_first_so_far = potential_common_first
#                         non_disjoint_expression_idxs.append(idx + 1 + off)
#                 if len(non_disjoint_expression_idxs) > 1:
#                     if neq_common_first:
#                         # todo: start delete
#                         global abcdef
#                         # print(neq_common_first)
#                         # print(fmt_grammar_rules(grammar))
#                         # print()
#                         # expanded = expand_neq_common_first(
#                         #     grammar, nonterminal, neq_common_first
#                         # )
#                         # print(fmt_grammar_rules(break_down(expanded)))
#                         # print()
#                         abcdef += 1
#                         if abcdef == 5:
#                             # exit(0)
#                             pass
#                         # todo: end delete
#                         return find_non_disjoint_expressions(
#                             break_down(
#                                 expand_neq_common_first(
#                                     grammar, nonterminal, neq_common_first
#                                 )
#                             )
#                         )
#
#                     # todo: start delete
#                     # print("actually returned")
#                     # exit(0)
#                     # todo: end delete
#                     return (
#                         nonterminal,
#                         non_disjoint_expression_idxs,
#                         common_first_so_far,
#                         grammar.rules,
#                     )
#
#     return None


# todo: delete
# idek what this is anymore
# def left_factor(grammar: Grammar) -> Grammar:
#     broken_down_grammar: Grammar = break_down(grammar)
#
#     left_factored_grammar: Grammar = Grammar(namegen(), broken_down_grammar.rules)
#
#     while True:
#         find_non_disjoint_expressions_result = find_non_disjoint_expressions(
#             left_factored_grammar
#         )
#         if not find_non_disjoint_expressions_result:
#             break
#
#         (
#             nonterminal_to_be_factored,
#             non_disjoint_expression_idxs,
#             common_first,
#             modified_rules,
#         ) = find_non_disjoint_expressions_result
#
#         # print(nonterminal_to_be_factored)
#         # for idx in non_disjoint_expression_idxs:
#         #     print(
#         #         broken_down_grammar.rules[
#         #             broken_down_grammar.rules[nonterminal][idx][0].node_type
#         #         ]
#         #     )
#         # break
#
#         left_factored_rules: Grammar.Rules = Grammar.Rules()
#
#         for nonterminal, rule in modified_rules.items():
#             if nonterminal == nonterminal_to_be_factored:
#                 assert type(rule) is Grammar.Production
#                 new_aux_nonterminal: str = namegen()
#                 left_factored_rules[nonterminal] = Grammar.Production(
#                     [
#                         Grammar.Expression([Grammar.Term(new_aux_nonterminal)]),
#                         *(
#                             expression
#                             for idx, expression in enumerate(rule)
#                             if idx not in non_disjoint_expression_idxs
#                         ),
#                     ]
#                 )
#                 # left_factored_rules[new_aux_nonterminal] =
#                 # todo: need to first expand until common first == each first......
#
#             else:
#                 left_factored_rules[nonterminal] = rule
#
#     return left_factored_grammar


# return None if no left factoring needed
def left_factor_once(grammar: Grammar) -> Grammar | None:
    broken_down_grammar: Grammar = break_down(grammar)
    first: DefaultDict[str, ListSet[str]] = generate_first(broken_down_grammar)

    left_factored_rules: Grammar.Rules = Grammar.Rules()
    left_factored: bool = False

    for nonterminal, rule in broken_down_grammar.rules.items():
        if type(rule) is Grammar.Production:
            if len(rule) > 1:
                first_to_choices: DefaultDict[str, list[int]] = defaultdict(lambda: [])
                for choice, expression in enumerate(rule):
                    term: str = expression[0].node_type
                    # todo: ugly nonterminal check
                    expression_first: str = (
                        first[term][0] if term.startswith("<") else term
                    )
                    first_to_choices[expression_first].append(choice)

                left_factored_production: Grammar.Production = Grammar.Production()
                for first_terminal, choices in first_to_choices.items():
                    # multiple choices start w first_terminal, need to left factor
                    if len(choices) > 1:
                        left_factored = True
                        aux_nonterminal: str = (
                            f'{nonterminal}~{"|".join(map(str, choices))}'
                        )
                        aux_aux_nonterminal: str = f"{aux_nonterminal}:1"
                        left_factored_production.append(
                            Grammar.Expression([Grammar.Term(aux_nonterminal)])
                        )
                        left_factored_rules[aux_nonterminal] = Grammar.Production(
                            [
                                Grammar.Expression(
                                    [
                                        Grammar.Term(first_terminal),
                                        Grammar.Term(aux_aux_nonterminal),
                                    ]
                                )
                            ]
                        )
                        left_factored_aux_aux_production: Grammar.Production = (
                            Grammar.Production()
                        )
                        for choice in choices:
                            choice_term: str = rule[choice][0].node_type
                            # todo: ugly nonterminal check
                            if choice_term.startswith("<"):
                                choice_term_production: Grammar.Production = broken_down_grammar.rules[choice_term]  # type: ignore
                                assert (
                                    type(choice_term_production) is Grammar.Production
                                    and len(choice_term_production) == 1
                                )

                                choice_term_expression: Grammar.Expression = (
                                    choice_term_production[0]
                                )
                                if len(choice_term_expression) > 1:
                                    left_factored_aux_aux_production.append(
                                        Grammar.Expression(choice_term_expression[1:])
                                    )

                        if not left_factored_aux_aux_production:
                            left_factored_aux_aux_production.append(
                                Grammar.Expression([Grammar.Term("e")])
                            )

                        left_factored_rules[aux_aux_nonterminal] = (
                            left_factored_aux_aux_production
                        )

                    else:
                        left_factored_production.append(rule[choices[0]])

                left_factored_rules[nonterminal] = left_factored_production

            # production is single expression with possibly multiple terms
            else:
                left_factored_rules[nonterminal] = rule

        elif type(rule) is Grammar.Alias:
            left_factored_rules[nonterminal] = rule

        else:  # pragma: no cover
            assert False

    # todo: begin delete
    # print("left factored once:")
    # print(fmt_rules(left_factored_rules))
    # # print(left_factored_rules.keys())
    # print()
    # todo: end delete

    if not left_factored:
        return None
    return Grammar(grammar.name, left_factored_rules)


def left_factor(grammar: Grammar) -> Grammar:
    left_factored_grammar: Grammar = grammar
    next_grammar: Grammar | None = left_factor_once(grammar)
    # todo: delete
    cnt: int = 1
    while next_grammar:
        left_factored_grammar = next_grammar
        next_grammar = left_factor_once(left_factored_grammar)
        # todo: delete
        cnt += 1
        if cnt == 10:
            exit()
    return left_factored_grammar


class Parse:

    clean: Callable[[ASTNode], ASTNode]

    class ParseError(Exception):
        def __init__(self, msg: str = "an error occured"):
            super().__init__(msg)

    @staticmethod
    def for_grammar(grammar: Grammar, entry_point: str | None = None):
        entry_point = entry_point or grammar.entry_point
        return Parse.LL1.for_grammar(
            grammar, entry_point
        ) or Parse.Backtracking.for_grammar(grammar, entry_point)

    @staticmethod
    def for_lang(lang: "Lang", entry_point: str | None = None):  # type: ignore
        return Parse.for_grammar(lang.grammar, entry_point)

    @staticmethod
    def _clean(n: ASTNode) -> ASTNode:
        match n:
            case TerminalASTNode() | AliasASTNode():
                return n

        n_: ASTNode
        match n.node_type[-1]:
            case "?":
                n_ = NonterminalASTNode(n.node_type, extras=n.extras)
                if n.choice == 0:
                    n_.add(Parse._clean(n[0]))
                return n_

            case "*":
                n_ = NonterminalASTNode(n.node_type, extras=n.extras)
                if n.choice == 0:
                    n_.add(Parse._clean(n[0]))
                    n_.add_all(Parse._clean(n[1]))
                return n_

            case "+":
                n_ = NonterminalASTNode(n.node_type, extras=n.extras)
                n_.add(Parse._clean(n[0]))
                n_.add_all(Parse._clean(n[1]))
                return n_

            case _:
                match n:
                    case NonterminalASTNode(node_type, choice, extras):
                        n_ = NonterminalASTNode(node_type, choice=choice, extras=extras)

                    case _:  # pragma: no cover
                        assert False

                for c in n:
                    n_.add(Parse._clean(c))

        return n_

    class Backtracking:
        class Result(NamedTuple):
            node: ASTNode
            n_tokens_consumed: int

        NodeParser = Callable[["Parse.Backtracking"], Result | None]

        @staticmethod
        def for_grammar(grammar: Grammar, entry_point: str) -> Parse.Backtracking:
            vocabulary = grammar.vocabulary
            rules = grammar.rules
            node_parsers: dict[str, Parse.Backtracking.NodeParser] = {}

            for nonterminal in rules:
                rule: Grammar.Rule = rules[nonterminal]
                match rule:
                    case Grammar.Production():
                        node_parsers[nonterminal] = (
                            Parse.Backtracking.generate_nonterminal_parser(
                                nonterminal, rule
                            )
                        )

                    case Grammar.Alias(node_type=node_type):
                        node_parsers[nonterminal] = (
                            Parse.Backtracking.generate_alias_parser(
                                nonterminal, node_type
                            )
                        )

                    case _:  # pragma: no cover
                        assert False

            node_parsers.update(
                Parse.Backtracking.generate_parsers_from_vocabulary(vocabulary)
            )

            return Parse.Backtracking(node_parsers, entry_point, grammar.name)

        def __init__(
            self,
            node_parsers: dict[str, NodeParser],
            entry_point: str,
            grammar_name: str = "none",
        ):
            self._grammar_name: str = grammar_name
            self._node_parsers: dict[str, Parse.Backtracking.NodeParser] = node_parsers
            self._entry_point: str = entry_point

        def _parse(self) -> ASTNode:
            parse_result: Parse.Backtracking.Result | None = self._node_parsers[
                self._entry_point
            ](self)

            if parse_result is None:
                # todo: log this instead
                raise Parse.ParseError("failed to parse")

            elif not self.at_end():
                # todo: log this instead
                raise Parse.ParseError("did not parse until end of file")

            return parse_result.node

        def parse_node(
            self, term: "Term", **ctx: Any  # type: ignore
        ) -> Parse.Backtracking.Result | None:
            Log.t(
                f"parsing {term.node_type}, next token (index {self._current}) is {self._safe_peek()}",
                tag="parser",
            )

            # todo: type annotation
            parse: Parse.Backtracking.NodeParser = self._node_parsers[term.node_type]
            parse_result: Parse.Backtracking.Result | None = parse(self, **ctx)

            if parse_result is None:
                Log.t(f"unable to parse {term.node_type}", tag="parser")
            else:
                Log.t(f"parsed {term.node_type}", tag="parser")

            Log.t(
                f"next token (index {self._current}) is {self._safe_peek()}",
                tag="parser",
            )

            return parse_result

        def at_end(self) -> bool:
            return self._current >= len(self._tokens)

        def _peek(self) -> Token:
            return self._tokens[self._current]

        def _safe_peek(self) -> Token:
            if self.at_end():
                return Token("$", "")
            else:
                return self._peek()

        def _expect(self, token_type: str) -> Token | None:
            Log.t(f"expecting {token_type}", tag="parser")

            if self.at_end():
                Log.t(f"got EOF", tag="parser")
                return None

            token: Token = self._peek()
            Log.t(f"got {token.token_type}", tag="parser")
            if token.token_type != token_type:
                return None

            self._advance(1)
            return token

        def _advance(self, n_tokens: int) -> None:
            self._current += n_tokens

        def _save(self) -> int:
            return self._current

        def _backtrack(self, to: int) -> None:
            self._current = to

        def __call__(self, tokens: list[Token]) -> ASTNode:
            self._tokens: list[Token] = tokens
            self._current: int = 0
            return Parse._clean(self._parse())

        @staticmethod
        def generate_nonterminal_parser(
            nonterminal: str, body: Grammar.Production
        ) -> NodeParser:

            def nonterminal_parser(
                parser: Parse.Backtracking,
            ) -> Parse.Backtracking.Result | None:
                choices: dict[int, Parse.Backtracking.Result] = {}

                for choice, production in enumerate(body):

                    n: NonterminalASTNode = NonterminalASTNode(
                        nonterminal, choice=choice
                    )
                    good: bool = True
                    save: int = parser._save()
                    n_tokens_consumed: int = 0

                    c_res: Parse.Backtracking.Result | None
                    c: ASTNode

                    for term in production:
                        c_res: Parse.Backtracking.Result | None = parser.parse_node(
                            term
                        )

                        if c_res is not None:
                            c, c_n_tokens_consumed = c_res

                            if term.label:
                                c.extras["name"] = term.label
                            n.add(c)
                            n_tokens_consumed += c_n_tokens_consumed

                        else:
                            good = False
                            break

                    if good:
                        choices[choice] = Parse.Backtracking.Result(
                            n, n_tokens_consumed
                        )
                    parser._backtrack(save)

                if len(choices) == 0:
                    return None

                longest_match_idx = max(
                    choices, key=lambda idx: choices[idx].n_tokens_consumed
                )

                parser._advance(choices[longest_match_idx].n_tokens_consumed)

                return choices[longest_match_idx]

            return nonterminal_parser

        @staticmethod
        def generate_alias_parser(
            alias: str,
            terminal: str,
        ) -> NodeParser:

            # todo: review (enforce upstream?)
            assert terminal != "e"

            def alias_parser(
                parser: Parse.Backtracking,
            ) -> Parse.Backtracking.Result | None:
                token: Token | None = parser._expect(terminal)
                if token is None:
                    return None
                return Parse.Backtracking.Result(
                    AliasASTNode(alias, terminal, token), 1
                )

            return alias_parser

        @staticmethod
        def generate_terminal_parser(
            terminal: str,
        ) -> NodeParser:

            # todo: review epsilon handling
            if terminal == "e":
                return lambda *_: Parse.Backtracking.Result(
                    TerminalASTNode(terminal, Token("e", "")), 0
                )

            def terminal_parser(
                parser: Parse.Backtracking,
            ) -> Parse.Backtracking.Result | None:
                token: Token | None = parser._expect(terminal)
                if token is None:
                    return None
                return Parse.Backtracking.Result(TerminalASTNode(terminal, token), 1)

            return terminal_parser

        @staticmethod
        def generate_parsers_from_vocabulary(
            vocabulary: Vocabulary,
        ) -> dict[str, NodeParser]:
            return {
                terminal: Parse.Backtracking.generate_terminal_parser(terminal)
                for terminal in vocabulary
            }

    class LL1:
        @staticmethod
        def for_grammar(grammar: Grammar, entry_point: str) -> Parse.LL1 | None:
            left_factored_grammar: Grammar = left_factor(grammar)

            rules: Grammar.Rules = left_factored_grammar.rules
            productions: dict[str, Grammar.Production] = {}

            for nonterminal in rules:
                rule: Grammar.Rule = rules[nonterminal]
                if type(rule) is Grammar.Production:
                    productions[nonterminal] = rule

            first: DefaultDict[str, ListSet[str]] = generate_first(
                left_factored_grammar
            )
            follow: DefaultDict[str, ListSet[str]] = generate_follow(
                left_factored_grammar
            )

            parsing_table: DefaultDict[
                str,
                dict[str, int | None],
            ] = defaultdict(lambda: {})

            for nonterminal in productions:
                production = productions[nonterminal]
                for idx, expression in enumerate(production):
                    nullable = True
                    for term in expression:
                        for x in first[term.node_type]:
                            if x != "e":
                                if x in parsing_table[nonterminal]:
                                    Log.w(
                                        f"{grammar.name} is not ll(1): multiple productions for ({nonterminal}, {x})"
                                    )
                                    return None
                                parsing_table[nonterminal][x] = idx
                        if "e" not in first[term.node_type]:
                            nullable = False
                            break
                    if nullable:
                        for x in follow[nonterminal]:
                            if x in parsing_table[nonterminal]:
                                Log.w(
                                    f"{grammar.name} is not ll(1): multiple productions for ({nonterminal}, {x})"
                                )
                                return None
                            parsing_table[nonterminal][x] = idx

            # todo: delete
            # if grammar.name == "xbnf":
            #     return None
            # print(f"{grammar.name} is ll(1)")
            # print(first)
            # print(follow)
            # print(parsing_table)
            Log.t(f"{grammar.name} is ll(1), using ll(1) parser")
            return Parse.LL1(parsing_table, rules, entry_point, grammar.name)

        def __init__(
            self,
            parsing_table,
            rules,
            entry_point: str,
            grammar_name: str = "none",
        ):
            self._grammar_name: str = grammar_name
            self._parsing_table = parsing_table
            self._rules = rules
            self._entry_point: str = entry_point

        def __repr__(self) -> str:
            return f"Parse(grammar={self._grammar_name})"

        def _parse(self) -> ASTNode:
            return self._parse_node(Grammar.Term(self._entry_point))

        def _parse_node(self, term: Grammar.Term) -> ASTNode:  # type: ignore
            Log.t(
                f"parsing {term.node_type}, next token (index {self._current}) is {self._safe_peek()}",
                tag="parser",
            )
            n: ASTNode

            # todo: terrible start...
            if term.node_type.startswith("<"):
                t: Token = self._safe_peek()
                # alias
                # todo: disgusting.
                if term.node_type not in self._parsing_table:
                    token = self._expect(self._rules[term.node_type].node_type)
                    if not token:
                        # todo: need way better error message
                        raise Parse.ParseError(
                            f"did not parse expected {term.node_type}"
                        )
                    n = AliasASTNode(
                        term.node_type,
                        self._rules[term.node_type].node_type,
                        token,
                    )
                    if term.label:
                        n.extras["name"] = term.label
                    return n

                # todo: delete
                # print(
                #     f"parsing {term.node_type} ({self._rules[term.node_type]}), next token is {t.token_type}"
                # )
                if t.token_type not in self._parsing_table[term.node_type]:
                    raise Parse.ParseError(
                        f"unexpected token '{t.lexeme}' while parsing {term.node_type}, expecting {{{', '.join(self._parsing_table[term.node_type].keys())}}}"
                    )
                choice: int = self._parsing_table[term.node_type][t.token_type]
                n = NonterminalASTNode(term.node_type, choice=choice)
                if term.label:
                    n.extras["name"] = term.label
                production = self._rules[term.node_type][choice]
                n.add_all(self._parse_node(term) for term in production)
                return n
            elif term.node_type == "e":
                return TerminalASTNode("e", Token("e", ""))
            else:
                token = self._expect(term.node_type)
                if not token:
                    # todo: need way better error message
                    raise Parse.ParseError(f"did not parse expected {term.node_type}")
                return TerminalASTNode(term.node_type, token)

        def at_end(self) -> bool:
            return self._current >= len(self._tokens)

        def _peek(self) -> Token:
            return self._tokens[self._current]

        def _safe_peek(self) -> Token:
            if self.at_end():
                return Token("$", "")
            else:
                return self._peek()

        def _expect(self, token_type: str) -> Token | None:
            Log.t(f"expecting {token_type}", tag="parser")

            if self.at_end():
                Log.t(f"got EOF", tag="parser")
                return None

            token: Token = self._peek()
            Log.t(f"got {token.token_type}", tag="parser")
            if token.token_type != token_type:
                return None

            self._advance(1)
            return token

        def _advance(self, n_tokens: int) -> None:
            self._current += n_tokens

        def __call__(self, tokens: list[Token]) -> ASTNode:
            self._tokens: list[Token] = tokens
            self._current: int = 0
            return Parse._clean(self._parse())
