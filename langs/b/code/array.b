fn main() {
  a = alloc(5);
  x = 7;
  j = 2;
  a[0] = 1;
  a[1] = 2;
  a[j] = 3;
  a[3] = x;
  a[4] = a[0];

  i = 0;
  while (i < 5) {
    printi(a[i]);
    print("\n");
    i = i + 1;
  }
}
