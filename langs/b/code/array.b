fn main() {
  a = alloc(5);
  a[0] = 3;
  i = 1;
  a[i] = 4;
  a[2] = i;
  a[3] = "hmm";
  a[4] = a[0];
  i = 0;
  while (i < 5) {
    print("a[");
    printi(i);
    print("] = ");
    printi(a[i]);
    print("\n");
    i = i + 1;
  }
}
