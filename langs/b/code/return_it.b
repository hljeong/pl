fn return_it(it) return it;

fn main() {
  x_str = alloc(32);
  print("x = ");
  read(x_str);
  x = stoi(x_str);
  y = return_it(x);
  print("return_it(x = ");
  printi(x);
  print(") returns ");
  printi(y);
  print("\n");
}
