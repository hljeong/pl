fn main() {
  a = alloc(20);
  x = 7;
  j = 2;
  a[0] = 1;
  a[1] = 2;
  a[j] = 3;
  a[3] = x;
  a[4] = a[0];

  b = alloc(8);
  b[0] = 400;
  b[1] = 2;

  i = 0;
  while (i < 5) {
    printi(a[i]);
    print("\n");
    i = i + 1;
  }

  printi(b[0]);
  print("\n");

  printi(b[1]);
  print("\n");
}
