fn fact(n) {
  if (n == 0) return 1;
  nm1 = n - 1;
  fact = fact(nm1);
  fact = fact * n;
  return fact;
}

fn main() {
  n_str = alloc(32);
  print("n = ");
  read(n_str);
  n = stoi(n_str);
  fact = fact(n);
  print("n! = ");
  printi(fact);
  print("\n");
}
