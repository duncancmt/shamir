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


def modulus_bytes(modulus: gf.BinaryPolynomial) -> bytes:
    modulus = int(modulus)
    modulus &= ~((1 << (modulus.bit_length() - 1)) | 1)
    bits: list[int] = []
    while modulus:
        bit = modulus.bit_length() - 1
        bits.append(bit)
        modulus &= ~(1 << bit)
    if len(bits) != 3:
        raise ValueError(f"Invalid modulus {bits}")
    return (
        bits[0].to_bytes(1, "big")
        + bits[1].to_bytes(1, "big")
        + bits[2].to_bytes(1, "big")
    )


def random_elements(
    secret: GFE, how_many: int, version: int = 0
) -> Iterator[GFE]:
    h = hashlib.shake_256()
    h.update(
        bytes(secret)
        + modulus_bytes(secret.modulus)
        + how_many.to_bytes(4, "big")
        + version.to_bytes(4, "big")
    )
    return iter(
        secret.coerce(int.from_bytes(x, "big"))
        for x in grouper(h.digest(len(secret) * how_many), len(secret))
    )


def split(
    secret: GFE, k: int, n: int, version: int = 0
) -> list[tuple[GFE, GFE]]:
    # from high degree to low degree
    coeffs = tuple(random_elements(secret, k - 1, version)) + (secret,)
    result: list[tuple[GFE, GFE]] = []
    for i in map(secret.coerce, range(1, n + 1)):
        accum = secret.coerce(0)
        for coeff in coeffs:
            accum *= i
            accum += coeff
        result.append((i, accum))
    return result


def recover(shares: Iterable[tuple[GFE, GFE]], version: int = 0) -> GFE:
    result: GFE
    k = 0
    n = 0
    for x_i, accum in shares:
        k += 1
        n = max(int(x_i), n)
        for x_j, _ in shares:
            if x_j == x_i:
                continue
            accum *= x_j / (x_j - x_i)
        try:
            result += accum
        except NameError:
            result = accum
    original_shares = split(result, k, n, version)
    for i in shares:
        if i not in original_shares:
            raise ValueError("Invalid/malicious share")
    return result


__all__ = ["split", "recover"]
