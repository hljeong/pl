import sys
from io import StringIO
from contextlib import contextmanager

from pl import run_b, print_b


@contextmanager
def input(input):
    foo = sys.stdin
    sys.stdin = StringIO(input)
    yield
    sys.stdin = foo


def assert_same(x, y):
    assert x == y


def check_output(capsys, expected):
    out, _ = capsys.readouterr()
    assert_same(out, expected)


def test_nop():
    run_b(r"fn main() {}")


def test_hello(capsys):
    run_b(r'fn main() print("hello\n");')
    check_output(capsys, "hello\n")


def test_echo(capsys):
    with input("hello"):
        run_b(
            r"""
            fn main() {
                input = alloc(32);
                read(input);
                print(input);
                print("\n");
            }
            """
        )
    check_output(capsys, "hello\n")


def test_read_int(capsys):
    with input("15"):
        run_b(
            r"""
            fn main() {
                n_str = alloc(32);
                read(n_str);
                n = stoi(n_str);
                printi(n);
                print("\n");
            }
            """
        )
    check_output(capsys, "15\n")


def test_ctrl_flow(capsys):
    run_b(
        r"""
        fn main() {
            i = 0;
            while (i < 4) {
                printi(i);
                print("\n");
                i = i + 1;
            }
            if (i > 3) {
                print("i > 3\n");
            }
            if (i > 5) {
                print("i > 5\n");
            }
        }
        """
    )
    check_output(capsys, "0\n1\n2\n3\ni > 3\n")


def test_array(capsys):
    run_b(
        r"""
        fn main() {
            a = alloc(5);
            x = 7;
            j = 2;
            a[0] = 1;
            a[1] = 2;
            a[j] = 3;
            a[3] = x;
            a[4] = a[0];

            i = 0;
            while (i < 5) {
                printi(a[i]);
                print("\n");
                i = i + 1;
            }
        }
        """
    )
    check_output(capsys, "1\n2\n3\n7\n1\n")


def test_ops(capsys):
    run_b(
        r"""
        fn main() {
            n = 58;
            x = 17; y = 4;
            v = alloc(n);

            v[0]  = x + y;    v[1]  = x - y;    v[2]  = x * y;   v[3]  = x / y;
            v[4]  = x % y;    v[5]  = x | y;    v[6]  = x & y;   v[7]  = x ^ y;
            v[8]  = x == y;   v[9]  = x != y;   v[10] = x > y;   v[11] = x >= y;
            v[12] = x < y;    v[13] = x <= y;

            v[14] = x + 5;    v[15] = x - 5;    v[16] = x * 5;   v[17] = x / 5;
            v[18] = x % 5;    v[19] = x | 5;    v[20] = x & 5;   v[21] = x ^ 5;
            v[22] = x == 5;   v[23] = x != 5;   v[24] = x > 5;   v[25] = x >= 5;
            v[26] = x < 5;    v[27] = x <= 5;

            v[28] = 4 + y;    v[29] = 4 - y;    v[30] = 4 * y;   v[31] = 4 / y;
            v[32] = 4 % y;    v[33] = 4 | y;    v[34] = 4 & y;   v[35] = 4 ^ y;
            v[36] = 4 == y;   v[37] = 4 != y;   v[38] = 4 > y;   v[39] = 4 >= y;
            v[40] = 4 < y;    v[41] = 4 <= y;

            v[42] = 9 + 15;   v[43] = 9 - 15;   v[44] = 9 * 15;  v[45] = 9 / 15;
            v[46] = 9 % 15;   v[47] = 9 | 15;   v[48] = 9 & 15;  v[49] = 9 ^ 15;
            v[50] = 9 == 15;  v[51] = 9 != 15;  v[52] = 9 > 15;  v[53] = 9 >= 15;
            v[54] = 9 < 15;   v[55] = 9 <= 15;

            v[56] = !x;       v[57] = !0;

            i = 0;
            while (i < n) {
                printi(v[i]);
                print("\n");
                i = i + 1;
            }
        }
        """
    )
    check_output(
        capsys,
        "21\n13\n68\n4\n1\n21\n0\n21\n0\n1\n1\n1\n0\n0\n"
        "22\n12\n85\n3\n2\n21\n1\n20\n0\n1\n1\n1\n0\n0\n"
        "8\n0\n16\n1\n0\n4\n4\n0\n1\n0\n0\n1\n0\n1\n"
        "24\n-6\n135\n0\n9\n15\n9\n6\n0\n1\n0\n0\n1\n1\n"
        "0\n1\n",
    )


def test_hello_fn(capsys):
    run_b(
        r"""
        fn hello() print("hello\n");

        fn main() hello();
        """
    )
    check_output(capsys, "hello\n")


def test_nested_fn_calls(capsys):
    run_b(
        r"""
        fn bye() print("bye\n");

        fn hello() {
            print("hello\n");
            how_are_you();
        }

        fn main() hello();

        fn how_are_you() {
            print("how are you\n");
            bye();
        }
        """
    )
    check_output(capsys, "hello\nhow are you\nbye\n")


def test_return_value(capsys):
    run_b(
        r"""
        fn return3() {
            return 3;
        }

        fn main() {
            three = return3();
            printi(three);
            print("\n");
        }
        """
    )
    check_output(capsys, "3\n")


def test_argument_passing(capsys):
    run_b(
        r"""
        fn return_it(it) {
            return it;
        }

        fn main() {
            it = return_it(5);
            printi(it);
            print("\n");
        }
        """
    )
    check_output(capsys, "5\n")


def test_argument_overflow(capsys):
    run_b(
        r"""
        fn printiln(v) {
            printi(v);
            print("\n");
        }

        fn so_many_args(v0, v1, v2, v3, v4, v5, v6, v7, v8) {
            printiln(v0);
            printiln(v1);
            printiln(v2);
            printiln(v3);
            printiln(v4);
            printiln(v5);
            printiln(v6);
            printiln(v7);
            printiln(v8);
        }

        fn main() so_many_args(1, 3, 5, 7, 2, 4, 6, 8, 0);
        """
    )
    check_output(capsys, "1\n3\n5\n7\n2\n4\n6\n8\n0\n")


def test_recursion(capsys):
    run_b(
        r"""
        fn fib(n) {
            if (n <= 1) return n;
            nm2 = n - 2;
            nm1 = n - 1;
            lfib = fib(nm2);
            rfib = fib(nm1);
            fib = lfib + rfib;
            return fib;
        }

        fn main() {
            f = fib(7);
            printi(f);
            print("\n");
        }
        """
    )
    check_output(capsys, "13\n")


def test_hello_fn(capsys):
    run_b(
        r"""
        fn hello() print("hello\n");

        fn main() hello();
        """
    )
    check_output(capsys, "hello\n")


def test_nested_fn_calls(capsys):
    run_b(
        r"""
        fn bye() print("bye\n");

        fn hello() {
            print("hello\n");
            how_are_you();
        }

        fn main() hello();

        fn how_are_you() {
            print("how are you\n");
            bye();
        }
        """
    )
    check_output(capsys, "hello\nhow are you\nbye\n")


def test_return_value(capsys):
    run_b(
        r"""
        fn return3() {
            return 3;
        }

        fn main() {
            three = return3();
            printi(three);
            print("\n");
        }
        """
    )
    check_output(capsys, "3\n")


def test_argument_passing(capsys):
    run_b(
        r"""
        fn return_it(it) {
            return it;
        }

        fn main() {
            it = return_it(5);
            printi(it);
            print("\n");
        }
        """
    )
    check_output(capsys, "5\n")


def test_argument_overflow(capsys):
    run_b(
        r"""
        fn printiln(v) {
            printi(v);
            print("\n");
        }

        fn so_many_args(v0, v1, v2, v3, v4, v5, v6, v7, v8) {
            printiln(v0);
            printiln(v1);
            printiln(v2);
            printiln(v3);
            printiln(v4);
            printiln(v5);
            printiln(v6);
            printiln(v7);
            printiln(v8);
        }

        fn main() so_many_args(1, 3, 5, 7, 2, 4, 6, 8, 0);
        """
    )
    check_output(capsys, "1\n3\n5\n7\n2\n4\n6\n8\n0\n")


def test_recursion(capsys):
    run_b(
        r"""
        fn fib(n) {
            if (n <= 1) return n;
            nm2 = n - 2;
            nm1 = n - 1;
            lfib = fib(nm2);
            rfib = fib(nm1);
            fib = lfib + rfib;
            return fib;
        }

        fn main() {
            f = fib(7);
            printi(f);
            print("\n");
        }
        """
    )
    check_output(capsys, "13\n")


def test_print(capsys):
    print_b(
        r"""
        fn fib(n) {
            if (n <= 1) return n;
            nm2 = n - 2;
            nm1 = n - 1;
            lfib = fib(nm2);
            rfib = fib(nm1);
            fib = lfib + rfib;
            return fib;
        }

        fn main() {
            b = alloc(256);

            f = fib(7);
            printi(f);
            print("\n");

            i = 0;
            while (i < 4) { printi(i); print("\n"); i = i + 1; }
            if (i > 3)
                print("i > 3\n");

            if (i > 5) {
                print("i > 5\n");
            }

            hello();
        }

        fn hello() print("hello\n");

        fn nop() {}
        """
    )
    out, _ = capsys.readouterr()
    run_b(out)
    check_output(capsys, "13\n0\n1\n2\n3\ni > 3\nhello\n")
