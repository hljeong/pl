# pl

## requirement
python 3.12

## setup
```sh
python -m venv .venv        # create virtual environment
source .venv/bin/activate   # activate virtual environment
make install                # install dependencies
```

> [!IMPORTANT]
> make sure to activate virtual environment before proceeding
> ```sh
> source .venv/bin/activate
> ```


## test
```sh
make test
```

## run code
```sh
python pl <source>

# alternatively,
./pl <source>

# see -h for help:
./pl -h
```

## synthesize code
```sh
./syn <source> <target>

# see -h for help:
./syn -h
```

try these examples:

- [echo.a](./langs/a/code/echo.a):
    ```sh
    ./pl ./langs/a/code/echo.a
    ```

- [fact.a](./langs/a/code/fact.a)
    ```sh
    ./pl ./langs/a/code/fact.a
    ```

- [fizz.b](./langs/b/code/fizz.b)
    ```sh
    ./pl ./langs/b/code/fizz.b
    ```

- [pfact.b](./langs/b/code/pfact.b)
    ```sh
    ./pl ./langs/b/code/pfact.b
    ```

- [fib_memo.b](./langs/b/code/fib_memo.b)
    ```sh
    ./pl ./langs/b/code/fib_memo.b
    ```

- [list.b2](./langs/b2/code/list.b2)
    ```sh
    ./pl ./langs/b2/code/list.b2
    ```

- synthesize [list.b2](./langs/b2/code/list.b2) to `a`
    ```sh
    ./syn ./langs/b2/code/list.b2 a
    ```

## references
* [java bnf](https://cs.au.dk/~amoeller/RegAut/JavaBNF.html)
