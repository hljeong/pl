fn sq(x) {
  sqx = x * x;
  return sqx;
}

fn cb(x) {
  sqx = sq(x);
  cbx = sqx * x;
  return cbx;
}

fn echo() {
  x = alloc(32);
  read(x);
  print(x);
  print("\n");
}

fn hello() print("hello\n");

fn early_return(x) {
  print("entering\n");
  if (x == 0) return;
  print("bad: did not return early\n");
}

fn main() {
  print("x = ");
  x_str = alloc(32);
  read(x_str);
  x = stoi(x_str);
  cbx = cb(x);
  printi(x);
  print(" ** 3 = ");
  printi(cbx);
  print("\n");
  hello();
  print("echo: ");
  echo();
  early_return(0);
}
