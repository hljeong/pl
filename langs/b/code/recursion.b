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
