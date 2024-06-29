fn bye() print("bye\n");

fn hello() {
  print("hello\n");
  how_are_you();
}

fn main() hello();

fn how_are_you() {
  print("how are you\n");
  bye();
}
