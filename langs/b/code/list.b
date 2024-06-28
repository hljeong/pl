fn list_init() {
  list = alloc(7);
  list[0] = 5;
  list[1] = 0;
  return list;
}

fn list_realloc(list) {
  capacity = list[0];
  size = list[1];

  print("capacity (");
  printi(capacity);
  print(") reached\n");

  capacity = capacity * 3;
  capacity = capacity / 2;

  print("reallocating with capacity = ");
  printi(capacity);
  print("\n");

  new_list = alloc(capacity);
  new_list[0] = capacity;
  new_list[1] = size;

  i = 0;
  while (i < size) {
    ip2 = i + 2;
    new_list[ip2] = list[ip2];
    i = i + 1;
  }

  print("old list @ ");
  printi(list);
  print(", new list @ ");
  printi(new_list);
  print("\n");

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

fn list_print(list) {
  print("{");
  i = 0;
  size = list[1];
  while (i < size) {
    if (i > 0) print(", ");
    ip2 = i + 2;
    printi(list[ip2]);
    i = i + 1;
  }
  print("}\n");
}

fn input() {
  print("insert (-1 to quit): ");
  v_str = alloc(32);
  read(v_str);
  v = stoi(v_str);
  return v;
}

fn main() {
  list = list_init();

  print("list = ");
  list_print(list);
  print("\n");

  x = input();
  while (x != -1) {
    list = list_add(list, x);

    print("list = ");
    list_print(list);
    print("\n");

    x = input();
  }
}
