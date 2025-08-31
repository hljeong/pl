from typing import Iterable


def oxford(things: Iterable[str]) -> str:
    things_l: list[str] = list(things)
    match things_l:
        case []:
            return ""

        case [thing]:
            return thing

        case [thing1, thing2]:
            return f"{thing1} and {thing2}"

        case [*things, thing]:
            return f"{', '.join(things)}, and {thing}"

        # appease the dimwit type checker
        case _:
            assert False
