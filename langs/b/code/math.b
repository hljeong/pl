buf_size = 32;
newline = "\n";
x_equals = "x = ";
y_equals = "y = ";
z_equals = "z = ";
x_str = alloc(buf_size);
y_str = alloc(buf_size);
z_str = alloc(buf_size);

print(x_equals);
read(x_str);

print(y_equals);
read(y_str);

print(z_equals);
read(z_str);

x = stoi(x_str);
y = stoi(y_str);
z = stoi(z_str);

u = 3 * x;
{v = y & 1;
w = v - y;
}t = y <= u;
r = v | t;
c = 15 * 7;

u_equals = "u = 3 * x = ";
print(u_equals);
printi(u);
print(newline);

v_equals = "v = y & 1 = ";
print(v_equals);
printi(v);
print(newline);

w_equals = "w = v - y = ";
print(w_equals);
printi(w);
print(newline);

t_equals = "t = y <= u = ";
print(t_equals);
printi(t);
print(newline);

r_equals = "r = v | t = ";
print(r_equals);
printi(r);
print(newline);

c_equals = "c = 15 * 7 = ";
print(c_equals);
printi(c);
print(newline);
