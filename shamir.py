"""Shamir Secret Sharing over GF(2^n).

Note: this implementation uses the hash of the secret to derive the coefficients
of the polynomial. This reduces the security of the system to the security of
the hash algorithm, SHAKE-256.
"""

import hashlib
from collections.abc import Iterable, Iterator
from typing import TypeVar

import gf

T = TypeVar("T")


def grouper(iterable: Iterable[T], n: int) -> Iterable[tuple[T, ...]]:
    """Return fixed-length sequential chunks of the iterable.

    If there aren't enough elements of the iterable to fill the last chunk, it
    is silently dropped.
    """
    return zip(*([iter(iterable)] * n))


# Galois Field Element
GFE = gf.ModularBinaryPolynomial[gf.BinaryPolynomial]


def _modulus_bytes(modulus: gf.BinaryPolynomial) -> bytes:
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


def _random_elements(
    secret: GFE, how_many: int, nonce: int = 0
) -> Iterator[GFE]:
    h = hashlib.shake_256()
    h.update(
        bytes(secret)
        + _modulus_bytes(secret.modulus)
        + how_many.to_bytes(4, "big")
        + nonce.to_bytes(4, "big")
    )
    return iter(
        secret.coerce(int.from_bytes(x, "big"))
        for x in grouper(h.digest(len(secret) * how_many), len(secret))
    )


def split(
    secret: GFE, k: int, n: int, nonce: int = 0
) -> list[tuple[GFE, GFE]]:
    """Split a member of GF(2^n) into some points (field element pairs).

    These points can be used to reconstruct the original member through Lagrange
    interpolation.
    """
    if k < 1:
        raise ValueError(f"Can't split into {k} shares")
    if n < k:
        raise ValueError(
            f"Requested {n} shares which is fewer than {k} required to recover"
        )
    # from high degree to low degree
    coeffs = tuple(_random_elements(secret, k - 1, nonce)) + (secret,)
    result: list[tuple[GFE, GFE]] = []
    for i in map(secret.coerce, range(1, n + 1)):
        accum = secret.coerce(0)
        for coeff in coeffs:
            accum *= i
            accum += coeff
        result.append((i, accum))
    return result


def recover(shares: Iterable[tuple[GFE, GFE]], nonce: int = 0) -> GFE:
    """Recover the constant term of the polynomial determined by the given points.

    The degree of the polynomial is determined by number of given points. Points
    are field element pairs over GF(2^n). Fundamentally, this is Lagrange
    interpolation.

    This function expects the coefficients of the polynomial to have been
    constructed by `split`. Raises `ValueError` otherwise.
    """
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
    original_shares = split(result, k, n, nonce)
    for i in shares:
        if i not in original_shares:
            raise ValueError("Invalid/malicious share")
    return result


__all__ = ["split", "recover"]
