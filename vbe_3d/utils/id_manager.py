from itertools import count

_counter = count()


def next_id() -> int:
    return next(_counter)
