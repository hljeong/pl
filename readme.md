# pl

## requirement
python 3.12

## setup
```sh
python -m venv .venv        # create virtual environment
source .venv/bin/activate   # activate virtual environment
make install                # install dependencies
```

## test
```sh
make test
```

## run code
```sh
source .venv/bin/activate
./pl <lang> <cmd> <prog>

# alternatively,
source .venv/bin/activate
python pl <lang> <cmd> <prog>
```

try these examples:

- [echo.a](./langs/a/code/echo.a):
    ```sh
    ./pl a run ./langs/a/code/echo.a
    ```

- [fact.a](./langs/a/code/fact.a)
    ```sh
    ./pl a run ./langs/a/code/fact.a
    ```

- [fizz.b](./langs/b/code/fizz.b)
    ```sh
    ./pl b run ./langs/b/code/fizz.b
    ```

- [pfact.b](./langs/b/code/pfact.b)
    ```sh
    ./pl b run ./langs/b/code/pfact.b
    ```

- [fib_memo.b](./langs/b/code/fib_memo.b)
    ```sh
    ./pl b run ./langs/b/code/fib_memo.b
    ```

## references
* [java bnf](https://cs.au.dk/~amoeller/RegAut/JavaBNF.html)
