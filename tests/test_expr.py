import os
import sys
from io import StringIO
from git import Repo
from contextlib import contextmanager
from time import time

from common import load
from pl import print_expr


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


def load_expr(file):
    return load(from_git_root(f"./langs/expr/code/{file}"))


def assert_same(x, y):
    assert x == y


def check_output(capsys, expected):
    out, _ = capsys.readouterr()
    assert_same(out, expected)


def test_simple(capsys):
    f = "simple.expr"
    print_expr(load_expr(f))
    check_output(capsys, "a + b\n")


def test_complex(capsys):
    f = "complex.expr"
    print_expr(load_expr(f))
    check_output(capsys, "(a + b) * (c + (d * b + c + h * (x + y)))\n")
