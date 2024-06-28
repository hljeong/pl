fn disp(vname, x) {
  print(vname);
  print(" = ");
  printi(x);
  print("\n");
}

fn f(x, y, z, u, v, w, r) {
  disp("x", x);
  disp("y", y);
  disp("z", z);
  disp("u", u);
  disp("v", v);
  disp("w", w);
  disp("r", r);
}

fn prompt(vname) {
  v_str = alloc(32);
  print(vname);
  print(" = ");
  read(v_str);
  v = stoi(v_str);
  return v;
}

fn main() {
  x = prompt("x");
  y = prompt("y");
  z = prompt("z");
  u = prompt("u");
  v = prompt("v");
  w = prompt("w");
  r = prompt("r");
  f(x, y, z, u, v, w, r);
}
