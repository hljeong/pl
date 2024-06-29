fn main() {
  b = alloc(256);
  f = fib(7);
  printi(f);
  print("\n");
  i = 0;
  while (i < 4) {
    printi(i);
    print("\n");
    i = i + 1;
  }
  if (i > 3) print("i > 3\n");
  if (i > 5) {
    print("i > 5\n");
  }
  hello();
}

fn fib(n) {
  if (n <= 1) return n;
  nm2 = n - 2;
  nm1 = n - 1;
  lfib = fib(nm2);
  rfib = fib(nm1);
  fib = lfib + rfib;
  return fib;
}

fn hello() print("hello\n");

fn nop() {}
