n_str = alloc(32);

print("n = ");
read(n_str);
n = stoi(n_str);

fact = 1;
while (n != 0) {
  fact = fact * n;
  n = n - 1;
}

print("n! = ");
printi(fact);
print("\n");
