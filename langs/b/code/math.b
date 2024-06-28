fn main() {
  x_str = alloc(32);
  y_str = alloc(32);
  z_str = alloc(32);

  print("x = ");
  read(x_str);

  print("y = ");
  read(y_str);

  print("z = ");
  read(z_str);

  x = stoi(x_str);
  y = stoi(y_str);
  z = stoi(z_str);

  u = 3 * x;
  v = y & 1;
  w = v - y;
  t = y <= u;
  r = v | t;
  c = 15 * 7;

  print("u = 3 * x = ");
  printi(u);
  print("\n");

  print("v = y & 1 = ");
  printi(v);
  print("\n");

  print("w = v - y = ");
  printi(w);
  print("\n");

  print("t = y <= u = ");
  printi(t);
  print("\n");

  print("r = v | t = ");
  printi(r);
  print("\n");

  print("c = 15 * 7 = ");
  printi(c);
  print("\n");
}
