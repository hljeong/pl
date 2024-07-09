import os
import sys
from io import StringIO
from git import Repo
from contextlib import contextmanager
from time import time

from common import load, Monad
from langs import A
from runtime import MP0
from pl import run_b2, print_b2, compile_b2


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
    return load(from_git_root(f"./langs/b2/code/{file}"))


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
    num_ins_generated = A.count_instructions_generated(compile_b2(prog, False))
    compile = lambda: compile_b2(prog, False)
    if input:
        with pipe(input):
            num_ins_executed = (
                Monad(compile_b2(prog, False))
                .then(A.parse)
                .then(A.assemble)
                .then(MP0.count_instructions_executed)
                .value
            )

    else:
        num_ins_executed = (
            Monad(compile_b2(prog, False))
            .then(A.parse)
            .then(A.assemble)
            .then(MP0.count_instructions_executed)
            .value
        )

    execute = lambda: run_b2(prog)
    if input:

        def execute_with_input():
            with pipe(input):
                run_b2(prog)

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
    prog = load_b2(f)
    assert_same(print_b2(prog, False), prog[:-1])

    run_b2(prog)
    check_output(capsys, "13\n0\n1\n3\n7\n15\n31\n63\ni > 3\nhello\n")


def test_expr(capsys):
    f = "expr.b2"
    run_b2(load_b2(f))
    check_output(capsys, "1\n32\n32\n1\n1\n")
    benchmark(f)
