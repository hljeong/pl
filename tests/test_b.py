import os
import sys
from io import StringIO
from git import Repo
from contextlib import contextmanager

from pl import run_b, print_b


@contextmanager
def input(input):
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


def test_nop():
    run_b(load_b("nop.b"))


def test_hello(capsys):
    run_b(load_b("hello.b"))
    check_output(capsys, "hello\n")


def test_echo(capsys):
    with input("hello"):
        run_b(load_b("echo.b"))
    check_output(capsys, "hello\n")


def test_read_int(capsys):
    with input("15"):
        run_b(load_b("read_int.b"))
    check_output(capsys, "15\n")


def test_ctrl_flow(capsys):
    run_b(load_b("ctrl_flow.b"))
    check_output(capsys, "0\n1\n2\n3\ni > 3\n")


def test_array(capsys):
    run_b(load_b("array.b"))
    check_output(capsys, "1\n2\n3\n7\n1\n400\n2\n")


# todo: change 9 << 5 back to 9 << 15 after fixing translation of <cmd>v
def test_ops(capsys):
    run_b(load_b("ops.b"))
    check_output(
        capsys,
        "21\n13\n68\n4\n1\n21\n0\n21\n0\n1\n1\n0\n0\n272\n1\n"
        "22\n12\n85\n3\n2\n21\n1\n20\n0\n1\n1\n0\n0\n544\n0\n"
        "8\n0\n16\n1\n0\n4\n4\n0\n1\n0\n1\n0\n1\n64\n0\n"
        "24\n-6\n135\n0\n9\n15\n9\n6\n0\n0\n0\n1\n1\n288\n0\n"
        "0\n1\n",
    )


def test_hello_fn(capsys):
    run_b(load_b("hello_fn.b"))
    check_output(capsys, "hello\n")


def test_nested_fn_calls(capsys):
    run_b(load_b("nested_fn_calls.b"))
    check_output(capsys, "hello\nhow are you\nbye\n")


def test_return_value(capsys):
    run_b(load_b("return_value.b"))
    check_output(capsys, "3\n")


def test_argument_passing(capsys):
    run_b(load_b("argument_passing.b"))
    check_output(capsys, "5\n")


def test_argument_overflow(capsys):
    run_b(load_b("argument_overflow.b"))
    check_output(capsys, "1\n3\n5\n7\n2\n4\n6\n8\n0\n")


def test_recursion(capsys):
    run_b(load_b("recursion.b"))
    check_output(capsys, "13\n")


def test_print(capsys):
    print_b(load_b("clueless.b"))
    printed, _ = capsys.readouterr()
    assert_same(printed, load_b("clueless.b"))

    run_b(printed)
    check_output(capsys, "13\n0\n1\n2\n3\ni > 3\nhello\n")
