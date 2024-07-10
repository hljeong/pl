from common import Monad
from langs import A, B, B2, Expr
from runtime import MP0


def nop(*args, **kwargs):
    pass


def print_a(prog, output=True):
    return Monad(prog).then(A.parse).then(A.print).first(print if output else nop).v


def run_a(prog):
    (Monad(prog).then(A.parse).then(A.assemble).then(MP0()))


def print_b(prog, output=True):
    return Monad(prog).then(B.parse).then(B.print).first(print if output else nop).v


def compile_b(prog, output=True):
    return (
        Monad(prog)
        .then(B.parse)
        .then(B.compile)
        # todo: implement this
        # .also(Monad.F(lambda it: it).then(print))
        .first(print if output else nop)
        .v
    )


def run_b(prog):
    (
        Monad(prog)
        .then(B.parse)
        .then(B.compile)
        .then(A.parse)
        .then(A.assemble)
        .then(MP0())
    )


def print_b2(prog, output=True):
    return Monad(prog).then(B2.parse).then(B2.print).first(print if output else nop).v


def translate_b2(prog, output=True):
    return (
        Monad(prog).then(B2.parse).then(B2.translate).first(print if output else nop).v
    )


def compile_b2(prog, output=True):
    return (
        Monad(prog)
        .then(B2.parse)
        .then(B2.translate)
        .then(B.parse)
        .then(B.compile)
        .first(print if output else nop)
        .v
    )


def run_b2(prog):
    (
        Monad(prog)
        .then(B2.parse)
        .then(B2.translate)
        .then(B.parse)
        .then(B.compile)
        .then(A.parse)
        .then(A.assemble)
        .then(MP0())
    )


def print_expr(prog, output=True):
    return (
        Monad(prog).then(Expr.parse).then(Expr.print).first(print if output else nop).v
    )
