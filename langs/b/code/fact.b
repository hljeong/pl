buf_size = 32;
prompt = "n = ";
n_fact_equals = "n! = ";
newline = "\n";
n_str = alloc(buf_size);

print(prompt);
read(n_str);
n = stoi(n_str);

fact = 1;
while (n != 0) {
  fact = fact * n;
  n = n - 1;
}
print(n_fact_equals);
printi(fact);
print(newline);
