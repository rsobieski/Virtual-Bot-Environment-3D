from typing import Tuple


def add_vec(a: Tuple[float, float, float], b: Tuple[float, float, float]):
    return [a[i] + b[i] for i in range(3)]
