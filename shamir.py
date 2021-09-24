import hashlib
import itertools
from collections.abc import Iterable, Iterator
from typing import TypeVar

import gf

T = TypeVar("T")


def grouper(iterable: Iterable[T], n: int) -> Iterable[tuple[T, ...]]:
    return zip(*([iter(iterable)] * n))


# Galois Field Element
GFE = gf.ModularBinaryPolynomial[gf.BinaryPolynomial]


def random_elements(
    secret: GFE, k: int, how_many: int, version: int = 0
) -> Iterator[GFE]:
    h = hashlib.shake_256()
    h.update(
        bytes(secret)
        + bytes(secret.modulus)
        + k.to_bytes((k.bit_length() + 7) // 8, "little")
        + version.to_bytes((version.bit_length() + 7) // 8, "little")
    )
    return iter(
        secret.coerce(int.from_bytes(x, "little"))
        for x in grouper(h.digest(len(secret) * how_many), len(secret))
    )


def split(
    secret: GFE, n: int, k: int, version: int = 0
) -> list[tuple[int, GFE, GFE]]:
    noise = random_elements(secret, k, n + k - 1, version)
    # from high degree to low degree
    coeffs = tuple(itertools.islice(noise, k - 1)) + (secret,)
    result: list[tuple[int, GFE, GFE]] = []
    for i, x in zip(itertools.count(1), noise):
        accum = secret.coerce(0)
        for coeff in coeffs:
            accum *= x
            accum += coeff
        result.append((i, x, accum))
    return result


def recover(shares: Iterable[tuple[int, GFE, GFE]], version: int = 0) -> GFE:
    result: GFE
    n = 0
    k = 0
    for i, x_i, accum in shares:
        n = max(i, n)
        k += 1
        for j, x_j, _ in shares:
            if j == i:
                continue
            accum *= x_j / (x_j - x_i)
        try:
            result += accum
        except NameError:
            result = accum
    original_shares = frozenset(split(result, n, k, version))
    for i in shares:
        assert i in original_shares
    return result
