from common import Monad, Log
from langs.a import AAssembler, Machine
from langs.b import (
    BParser,
    BAggregator,
    BAllocator,
    BCompiler,
    BPrinter,
    BASTCleaner,
    BSymbolTableGenerator,
)


def run_a(prog):
    Monad(prog).then(AAssembler(Machine()))


def print_b(prog):
    Monad(prog).then(BParser()).then(BASTCleaner()).then(BPrinter()).then(print)


def compile_b(prog):
    (
        Monad(prog)
        .then(BParser())
        .then(BASTCleaner())
        .keep_then(BAggregator())
        .keep_then(
            lambda fix_this_ugly_thing_too: BAllocator()(fix_this_ugly_thing_too[0])
        )
        .keep_then(
            lambda also_fix_this_ugly_thing: BSymbolTableGenerator()(
                also_fix_this_ugly_thing[0][0]
            )
        )
        .then(
            lambda fix_this_ugly_thing: BCompiler(
                fix_this_ugly_thing[0][0][1],
                fix_this_ugly_thing[0][1],
                fix_this_ugly_thing[1],
            )(fix_this_ugly_thing[0][0][0])
        )
        .then(print)
    )


def run_b(prog):
    (
        Monad(prog)
        .then(BParser())
        .then(BASTCleaner())
        .keep_then(BAggregator())
        .keep_then(
            lambda fix_this_ugly_thing_too: BAllocator()(fix_this_ugly_thing_too[0])
        )
        .keep_then(
            lambda also_fix_this_ugly_thing: BSymbolTableGenerator()(
                also_fix_this_ugly_thing[0][0]
            )
        )
        .then(
            lambda fix_this_ugly_thing: BCompiler(
                fix_this_ugly_thing[0][0][1],
                fix_this_ugly_thing[0][1],
                fix_this_ugly_thing[1],
            )(fix_this_ugly_thing[0][0][0])
        )
        .then(AAssembler(Machine()))
    )
