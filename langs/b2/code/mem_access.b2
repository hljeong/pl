buffer_size = 32;
v0_str = alloc(buffer_size);

arr_size = 5;
a = alloc(arr_size);
p = alloc(arr_size);

i = 0;
while (i < arr_size) {
  read(v0_str);
  v0 = stoi(v0_str);
  v1 = a + i;
  [v1 + 0] = v0;
  i = i + 1;
}

i = 0;
while (i < arr_size) {
  v0 = p + i;
  v1 = a + i;
  v2 = [v0 + 0];
  v3 = [v1 + 0];
  v1 = v2 + v3;
  [v0 + 1] = v1;
  i = i + 1;
}

i = 0;
while (i < arr_size) {
  v0 = p + i;
  x = [v0 + 1];
  printi(x);
  i = i + 1;
}
