import os
import sys
from io import StringIO
from git import Repo
from contextlib import contextmanager
from time import time

from common import Monad
from langs import A
from runtime import MP0
from synthesis import synthesize, Source


@contextmanager
def pipe(input):
    foo = sys.stdin
    sys.stdin = StringIO(input)
    yield
    sys.stdin = foo


def from_git_root(path):
    repo = Repo(".", search_parent_directories=True)
    root = repo.git.rev_parse("--show-toplevel")
    return os.path.join(root, path)


def load_b2(file):
    return Source.load(from_git_root(f"./langs/b2/code/{file}"))


def assert_same(x, y):
    assert x == y


def check_output(capsys, expected):
    out, _ = capsys.readouterr()
    assert_same(out, expected)


def report(
    filename, num_ins_generated, compilation_time, num_ins_executed, execution_time
):
    first_entry = os.path.isfile("./benchmark")

    with open("./benchmark", "a") as f:
        if first_entry:
            f.write("\n")

        f.write(
            f"{filename}:\n"
            f"  generated {num_ins_generated} instructions in {compilation_time:.03f}s\n"
            f"  executed {num_ins_executed} instructions in {execution_time:.03f}s\n"
        )


def runtime(f, n=1):
    if not n:
        n = 1
    times = []
    for _ in range(n):
        start_time: float = time()
        f()
        end_time: float = time()
        delta_time: float = end_time - start_time
        times.append(delta_time)
    return sum(times) / n


def benchmark(filename, input=None):
    prog = load_b2(filename)
    num_ins_generated = A.count_instructions_generated(synthesize("a", prog, "b2"))
    compile = lambda: synthesize("a", prog, "b2")
    if input:
        with pipe(input):
            num_ins_executed = (
                Monad(synthesize("mp0", prog, "b2"))
                .then(MP0.count_instructions_executed)
                .v
            )

    else:
        num_ins_executed = (
            Monad(synthesize("mp0", prog, "b2")).then(MP0.count_instructions_executed).v
        )

    execute = lambda: MP0()(synthesize("mp0", prog, "b2"))
    if input:

        def execute_with_input():
            with pipe(input):
                MP0()(synthesize("mp0", prog, "b2"))

        execute = execute_with_input

    report(
        filename,
        num_ins_generated,
        runtime(compile),
        num_ins_executed,
        runtime(execute),
    )


def test_print(capsys):
    f = "clueless.b2"
    assert_same(
        synthesize("b2", load_b2(f), "b2", waypoints=["b2-ast"]),
        Source.content_of(load_b2(f))[:-1],
    )

    MP0()(synthesize("mp0", load_b2(f), "b2"))
    check_output(capsys, "13\n0\n1\n3\n7\n15\n31\n63\ni > 3\nhello\n")


def test_expr(capsys):
    f = "expr.b2"
    MP0()(synthesize("mp0", load_b2(f), "b2"))
    check_output(capsys, "1\n32\n32\n1\n1\n")
    benchmark(f)
