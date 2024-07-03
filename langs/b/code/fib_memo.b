fn main() {
  print("n = ");
  n_str = alloc(32);
  read(n_str);
  n = stoi(n_str);

  if (n == 0) {
    print("n = 1\n");
    return;
  }

  if (n == 1) {
    print("n = 1\n");
    return;
  }

  memo_ptr = alloc(4);
  memo_ptr[0] = list_init();
  memo_ptr[0] = list_add(memo_ptr[0], 0);
  memo_ptr[0] = list_add(memo_ptr[0], 1);

  i = 0;
  while (i <= n) {
    fib = fib(i, memo_ptr);
    print("fib(");
    printi(i);
    print(") = ");
    printi(fib);
    print("\n");
    i = i + 1;
  }

}

fn fib(n, memo_ptr) {
  size = list_size(memo_ptr[0]);
  if (n < size) {
    x = list_get(memo_ptr[0], n);
    return x;
  }

  nm1 = n - 1;
  nm2 = n - 2;
  l = fib(nm2, memo_ptr);
  r = fib(nm1, memo_ptr);
  fibn = l + r;

  size = list_size(memo_ptr[0]);
  if (size == n) memo_ptr[0] = list_add(memo_ptr[0], fibn);
  return fibn;
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

fn list_init_with_capacity(capacity) {
  bytes = capacity * 4;
  bytes = bytes + 8;
  list = alloc(bytes);
  list[0] = capacity;
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
