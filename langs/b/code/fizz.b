n_str = alloc(32);

print("n = ");
read(n_str);
n = stoi(n_str);

i = 1;
while (i <= n) {
  m3 = i % 3;
  m5 = i % 5;
  if (m3 == 0) {
    if (m5 == 0) print("fizzbuzz");
    if (m5 != 0) print("fizz");
  }
  if (m3 != 0) {
    if (m5 == 0) print("buzz");
    if (m5 != 0) printi(i);
  }
  print("\n");
  i = i + 1;
}
