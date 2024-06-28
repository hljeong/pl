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
    v0 = stoi(ibuf);
    v1 = a + i;
    [v1 + 0] = v0;
    i = i + 1;
  }

  i = 0;
  while (i < n) {
    v0 = p + i;
    v1 = a + i;
    v2 = [v0 + 0];
    v3 = [v1 + 0];
    v1 = v2 + v3;
    [v0 + 1] = v1;
    i = i + 1;
  }

  print("a = {");
  i = 0;
  while (i < n) {
    if (i > 0) print(", ");
    v0 = a + i;
    x = [v0 + 0];
    printi(x);
    i = i + 1;
  }

  print("}\n");
  print("p = {");
  i = 0;
  while (i < n) {
    if (i > 0) print(", ");
    v0 = p + i;
    x = [v0 + 1];
    printi(x);
    i = i + 1;
  }
  print("}\n");
}
