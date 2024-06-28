fn fib(n) {
  if (n <= 1) return n;
  nm2 = n - 2;
  nm1 = n - 1;
  l = fib(nm2);
  r = fib(nm1);
  fib = l + r;
  return fib;
}

fn main() {
  n_str = alloc(32);
  print("n = ");
  read(n_str);
  n = stoi(n_str);
  i = 0;
  while (i <= n) {
    fib = fib(i);
    print("fib(");
    printi(i);
    print(") = ");
    printi(fib);
    print("\n");
    i = i + 1;
  }
}

