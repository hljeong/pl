from collections.abc import Callable
from common import Monad, Log, ast_to_tree_string
from langs import A, B, Expr
from runtime import MP0


def nop(*args, **kwargs):
    pass


def print_a(prog, output=True):
    return (
        Monad(prog)
        .then(A.Parse())
        .then(A.Print())
        .first(print if output else nop)
        .value
    )


def run_a(prog):
    (Monad(prog).then(A.parse).then(A.build_internal_ast).then(A.assemble).then(MP0()))


def print_b(prog, output=True):
    return (
        Monad(prog)
        .then(B.parse)
        .then(B.build_internal_ast)
        .then(B.print)
        .first(print if output else nop)
        .value
    )


def compile_b(prog, output=True):
    return (
        Monad(prog)
        .then(B.parse)
        .then(B.build_internal_ast)
        .then(B.compile)
        # todo: implement this
        # .also(Monad.F(lambda it: it).then(print))
        .first(print if output else nop)
        .value
    )


def run_b(prog):
    (
        Monad(prog)
        .then(B.parse)
        .then(B.build_internal_ast)
        .then(B.compile)
        .then(A.parse)
        .then(A.build_internal_ast)
        .then(A.assemble)
        .then(MP0())
    )


def print_expr(prog, output=True):
    return (
        Monad(prog)
        .then(Expr.parse)
        .then(Expr.build_internal_ast)
        .then(Expr.print)
        .first(print if output else nop)
        .value
    )
