fn main() {
  ibuf = alloc(32);

  print("n = ");
  read(ibuf);
  n = stoi(ibuf);
  np1 = n + 1;

  a = alloc(n);
  p = alloc(np1);

  i = 0;
  while (i < n) {
    print("a[");
    printi(i);
    print("] = ");
    read(ibuf);
    a[i] = stoi(ibuf);
    i = i + 1;
  }

  i = 0;
  while (i < n) {
    ip1 = i + 1;
    p[ip1] = p[i] + a[i];
    i = i + 1;
  }

  print("a = {");
  i = 0;
  while (i < n) {
    if (i > 0) print(", ");
    printi(a[i]);
    i = i + 1;
  }
  print("}\n");

  print("p = {");
  i = 1;
  while (i <= n) {
    if (i > 1) print(", ");
    printi(p[i]);
    i = i + 1;
  }
  print("}\n");
}
