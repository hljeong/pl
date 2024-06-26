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
- no tests at the moment...
```sh
make test
```

## run code
```sh
# alterntively,
source .venv/bin/activate
./pl <language> <program>

# alternatively,
source .venv/bin/activate
python pl <language> <program>
```

try these examples:

- [echo.a](./langs/a/code/echo.a):
    ```sh
    ./pl a ./langs/a/code/echo.a
    ```

- [fact.a](./langs/a/code/fact.a)
    ```sh
    ./pl a ./langs/a/code/fact.a
    ```

- [fact.b](./langs/b/code/fact.b)
    ```sh
    ./pl b ./langs/b/code/fact.b
    ```

- [fizz.b](./langs/b/code/fizz.b)
    ```sh
    ./pl b ./langs/b/code/fizz.b
    ```
