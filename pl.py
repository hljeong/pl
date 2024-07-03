from common import Monad, Log, ast_to_tree_string
from langs.a import (
    AParse,
    APrint,
    ABuildInternalAST,
    ATranslate,
    AAssemble,
)
from langs.b import (
    BParse,
    BPrint,
    BASTCleaner,
    BAggregate,
    BGenerateSymbolTable,
    BCompile,
)
from runtime import MP0


def print_a(prog):
    Monad(prog).then(AParse()).then(APrint()).then(print)


def run_a(prog):
    (
        Monad(prog)
        .then(AParse())
        .then(ABuildInternalAST())
        .then(ATranslate())
        .then(AAssemble())
        .then(MP0())
    )


def print_b(prog):
    Monad(prog).then(BParse()).then(BASTCleaner()).then(BPrint()).then(print)


def compile_b(prog):
    (
        Monad(prog)
        .then(BParse())
        .then(BASTCleaner())
        .keep(BAggregate(), returns="constant_aggregate")
        .keep(BGenerateSymbolTable(), returns="symbol_table")
        .keep(
            Monad.create(BCompile),
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
        .then(BParse())
        .then(BASTCleaner())
        .keep(BAggregate(), returns="constant_aggregate")
        .keep(BGenerateSymbolTable(), returns="symbol_table")
        .keep(
            Monad.create(BCompile),
            returns="compile",
            args=(Monad.use("constant_aggregate"), Monad.use("symbol_table")),
        )
        .then(Monad.use("compile"))
        .then(AParse())
        .then(ABuildInternalAST())
        .then(ATranslate())
        .then(AAssemble())
        .then(MP0())
    )
