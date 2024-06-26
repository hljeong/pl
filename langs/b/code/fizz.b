buf_size = 32;
n_str = alloc(buf_size);
read(n_str);
n = stoi(n_str);
i = 1;
fizzbuzz = "fizzbuzz";
fizz = "fizz";
buzz = "buzz";
while (i <= n) {
  m3 = i;
  while (m3 > 0) m3 = m3 - 3;
  m5 = i;
  while (m5 > 0) m5 = m5 - 5;
  if (m3 == 0) {
    if (m5 == 0) print(fizzbuzz);
    if (m5 != 0) print(fizz);
  }
  if (m3 != 0) {
    if (m5 == 0) print(buzz);
    if (m5 != 0) printi(i);
  }
  i = i + 1;
}
