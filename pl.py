from common import Monad, Log, ast_to_tree_string
from langs.a import A
from langs.b import B
from runtime import MP0


def print_a(prog):
    Monad(prog).then(A.Parse()).then(A.Print()).then(print)


def run_a(prog):
    (
        Monad(prog)
        .then(A.Parse())
        .then(A.BuildInternalAST())
        .then(A.Translate())
        .then(A.Assemble())
        .then(MP0())
    )


def print_b(prog):
    Monad(prog).then(B.Parse()).then(B.BuildInternalAST()).then(B.Print()).then(print)


def compile_b(prog):
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
        # todo: implement this
        # .also(Monad.F(lambda it: it).then(print))
        .then(print)
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
