import os
import sys
from io import StringIO
from git import Repo
from contextlib import contextmanager
from time import time

from langs.a import A
from runtime import MP0
from pl import run_b, print_b, compile_b


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


def load(file):
    with open(file, "r") as f:
        code = f.read()
    return code


def load_b(file):
    return load(from_git_root(f"./langs/b/code/{file}"))


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
            f"  compiled {num_ins_generated} instructions in {compilation_time:.03f}s\n"
            f"  executed {num_ins_executed} instructions in {execution_time:.03f}s\n"
        )


def runtime(f, n=5):
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
    prog = load_b(filename)
    num_ins_generated = A.count_instructions_generated(compile_b(prog, False))
    compile = lambda: compile_b(prog, False)
    if input:
        with pipe(input):
            num_ins_executed = MP0.count_instructions_executed(
                A.assemble(compile_b(prog, False))
            )

    else:
        num_ins_executed = MP0.count_instructions_executed(
            A.assemble(compile_b(prog, False))
        )
    execute = lambda: run_b(prog)
    if input:

        def execute_with_input():
            with pipe(input):
                run_b(prog)

        execute = execute_with_input

    report(
        filename,
        num_ins_generated,
        runtime(compile),
        num_ins_executed,
        runtime(execute),
    )


def test_nop():
    f = "nop.b"
    run_b(load_b(f))
    benchmark(f)


def test_hello(capsys):
    f = "hello.b"
    run_b(load_b(f))
    check_output(capsys, "hello\n")
    benchmark(f)


def test_echo(capsys):
    f = "echo.b"
    i = "hello"
    with pipe(i):
        run_b(load_b(f))

    check_output(capsys, "hello\n")
    benchmark(f, i)


def test_read_int(capsys):
    f = "read_int.b"
    i = "15"
    with pipe(i):
        run_b(load_b(f))
    check_output(capsys, "15\n")
    benchmark(f, i)


def test_ctrl_flow(capsys):
    f = "ctrl_flow.b"
    run_b(load_b(f))
    check_output(capsys, "0\n1\n2\n3\ni > 3\n")
    benchmark(f)


def test_array(capsys):
    f = "array.b"
    run_b(load_b(f))
    check_output(capsys, "1\n2\n3\n7\n1\n400\n2\n")
    benchmark(f)


# todo: change 9 << 5 back to 9 << 15 after fixing translation of <cmd>v
def test_ops(capsys):
    f = "ops.b"
    run_b(load_b(f))
    check_output(
        capsys,
        "21\n13\n68\n4\n1\n21\n0\n21\n0\n1\n1\n0\n0\n272\n1\n"
        "22\n12\n85\n3\n2\n21\n1\n20\n0\n1\n1\n0\n0\n544\n0\n"
        "8\n0\n16\n1\n0\n4\n4\n0\n1\n0\n1\n0\n1\n64\n0\n"
        "24\n-6\n135\n0\n9\n15\n9\n6\n0\n0\n0\n1\n1\n288\n0\n"
        "0\n1\n",
    )
    benchmark(f)


def test_hello_fn(capsys):
    f = "hello_fn.b"
    run_b(load_b(f))
    check_output(capsys, "hello\n")
    benchmark(f)


def test_nested_fn_calls(capsys):
    f = "nested_fn_calls.b"
    run_b(load_b(f))
    check_output(capsys, "hello\nhow are you\nbye\n")
    benchmark(f)


def test_return_value(capsys):
    f = "return_value.b"
    run_b(load_b(f))
    check_output(capsys, "3\n")
    benchmark(f)


def test_argument_passing(capsys):
    f = "argument_passing.b"
    run_b(load_b(f))
    check_output(capsys, "5\n")
    benchmark(f)


def test_argument_overflow(capsys):
    f = "argument_overflow.b"
    run_b(load_b(f))
    check_output(capsys, "1\n3\n5\n7\n2\n4\n6\n8\n0\n")
    benchmark(f)


def test_recursion(capsys):
    f = "recursion.b"
    run_b(load_b(f))
    check_output(capsys, "13\n")
    benchmark(f)


def test_print(capsys):
    assert_same(print_b(load_b("clueless.b"), False), load_b("clueless.b")[:-1])

    run_b(load_b("clueless.b"))
    check_output(capsys, "13\n0\n1\n2\n3\ni > 3\nhello\n")
