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
    (
        Monad(prog)
        .then(A.Parse())
        .then(A.BuildInternalAST())
        .then(A.Translate())
        .then(A.Assemble())
        .then(MP0())
    )


def print_b(prog, output=True):
    return (
        Monad(prog)
        .then(B.Parse())
        .then(B.BuildInternalAST())
        .then(B.Print())
        .first(print if output else nop)
        .value
    )


def compile_b(prog, output=True):
    return (
        Monad(prog)
        .then(B.Parse())
        .then(B.BuildInternalAST())
        .keep(B.Aggregate(), returns="constant_aggregate")
        .keep(B.GenerateSymbolTable(), returns="symbol_table")
        .keep(
            Monad.create(B.Compile),
            returns="compile",
            args=(Monad.use("constant_aggregate"), Monad.use("symbol_table")),
        )
        .then(Monad.use("compile"))
        # todo: implement this
        # .also(Monad.F(lambda it: it).then(print))
        .first(print if output else nop)
        .value
    )


def run_b(prog):
    (
        Monad(prog)
        .then(B.Parse())
        .then(B.BuildInternalAST())
        .keep(B.Aggregate(), returns="constant_aggregate")
        .keep(B.GenerateSymbolTable(), returns="symbol_table")
        .keep(
            Monad.create(B.Compile),
            returns="compile",
            args=(Monad.use("constant_aggregate"), Monad.use("symbol_table")),
        )
        .then(Monad.use("compile"))
        .then(A.Parse())
        .then(A.BuildInternalAST())
        .then(A.Translate())
        .then(A.Assemble())
        .then(MP0())
    )


def print_expr(prog, output=True):
    return (
        Monad(prog)
        .then(Expr.Parse())
        .then(Expr.BuildInternalAST())
        .then(Expr.Print())
        .first(print if output else nop)
        .value
    )
