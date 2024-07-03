fn main() {
  print("n = ");
  n_str = alloc(32);
  read(n_str);
  n = stoi(n_str);

  if (n == 0) {
    print("n = 0\n");
    return;
  }

  if (n == 1) {
    print("n = 1\n");
    return;
  }

  pf = list_init();
  f = 2;
  while (n > 1) {
    nmf = n % f;
    while (nmf == 0) {
      list_add(pf, f);
      n = n / f;
      nmf = n % f;
    }
    f = f + 1;
  }

  print("n = ");
  m = list_size(pf);
  i = 0;
  while (i < m) {
    if (i > 0) print(" * ");

    f = list_get(pf, i);
    printi(f);

    i = i + 1;
  }
  print("\n");
}

fn list_get(list, i) {
  i = i + 2;
  return list[i];
}

fn list_size(list) return list[1];

fn list_init() {
  list = alloc(28);
  list[0] = 5;
  list[1] = 0;
  return list;
}

fn list_realloc(list) {
  capacity = list[0];
  size = list[1];

  capacity = capacity * 3;
  capacity = capacity / 2;

  bytes = capacity * 4;
  bytes = bytes + 8;
  new_list = alloc(bytes);
  new_list[0] = capacity;
  new_list[1] = size;

  i = 0;
  while (i < size) {
    ip2 = i + 2;
    new_list[ip2] = list[ip2];
    i = i + 1;
  }

  return new_list;
}

fn list_add(list, x) {
  capacity = list[0];
  size = list[1];
  if (size == capacity) list = list_realloc(list);

  idx = list[1] + 2;
  list[idx] = x;
  list[1] = list[1] + 1;

  return list;
}
