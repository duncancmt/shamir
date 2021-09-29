"""Shamir Secret Sharing over GF(2^n).

Note: this implementation uses the hash of the secret to derive the coefficients
of the polynomial. This reduces the security of the system to the security of
the hash algorithm, SHAKE-256.
"""

import hashlib
import itertools
from collections.abc import Collection, Iterable, Sequence
from typing import TypeVar, Union

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


def _hash_GFEs(x: Iterable[GFE]) -> GFE:
    h = hashlib.shake_256()
    for i in x:
        h.update(bytes(i))
    return i.coerce(h.digest(len(i)))


def _evaluate(
    poly: Iterable[GFE], x: Union[GFE, gf.BinaryPolynomial, int, bytes]
) -> GFE:
    accum: GFE
    for coeff in poly:
        try:
            accum *= x
            accum += coeff
        except NameError:
            accum = coeff
    return accum


def _lagrange_interpolate(
    points: Iterable[tuple[GFE, GFE]],
    x: Union[GFE, gf.BinaryPolynomial, int, bytes],
) -> GFE:
    result: GFE
    for i, (x_i, accum) in enumerate(points):
        for j, (x_j, _) in enumerate(points):
            if j == i:
                continue
            accum *= (x - x_j) / (x_i - x_j)
        try:
            result += accum
        except NameError:
            result = accum
    return result


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


def split(
    secret: GFE,
    k: int,
    n: int,
    salt: Union[GFE, gf.BinaryPolynomial, int, bytes] = 0,
) -> tuple[list[GFE], list[GFE], list[GFE]]:
    """Split a member of GF(2^n) into some points (field element pairs).

    These points can be used to reconstruct the original member through Lagrange
    interpolation.

    Returns the y-values corresponding to the x-values 1..n, and 2 lists of
    auxilliary, public values required to verify the validity of each individual
    share.
    """
    if k < 1:
        raise ValueError(f"Can't split into {k} shares")
    if n < k:
        raise ValueError(
            f"Requested {n} shares which is fewer than {k} required to recover"
        )

    h = hashlib.shake_256()
    h.update(
        bytes(secret)
        + _modulus_bytes(secret.modulus)
        + k.to_bytes(4, "big")
        + n.to_bytes(4, "big")
        + bytes(secret.coerce(salt))
    )
    random_elements = [
        secret.coerce(bytes(x))
        for x in grouper(h.digest(len(secret) * (k * 2 - 1)), len(secret))
    ]

    # from high to low order
    f_coeffs = random_elements[: k - 1]
    f_coeffs.append(secret)
    g_coeffs = random_elements[k - 1 :]

    # from low to high x
    f_values = [_evaluate(f_coeffs, secret.coerce(x)) for x in range(1, n + 1)]
    g_values = [_evaluate(g_coeffs, secret.coerce(x)) for x in range(1, n + 1)]

    v = list(map(_hash_GFEs, zip(f_values, g_values)))
    r = _hash_GFEs(v)

    # from high to low order
    c = [b + r * a for a, b in zip(f_coeffs, g_coeffs)]

    return f_values, v, c


def verify_share(y_f: GFE, v: Sequence[GFE], c: Iterable[GFE]) -> int:
    z = _hash_GFEs(v) * y_f
    for x in range(1, len(v) + 1):
        y_g = _evaluate(c, x) - z
        if v[x - 1] == _hash_GFEs((y_f, y_g)):
            return x
    return 0


def recover(
    shares: Iterable[GFE], v: Sequence[GFE], c: Collection[GFE]
) -> GFE:
    """Recover the constant term of the polynomial determined by the given shares.

    The degree of the polynomial is inferred from the length of `c`. Shares are
    points/field element pairs/GF(2^n)^2. Fundamentally, this is Lagrange
    interpolation.

    This function verifies each share against the public check data `v` and
    `c`. `v` must be long enough to accommodate the highest x-coordinate of
    `shares`.

    This function raises `ValueError` if too few shares pass validation against
    `v` and `c`. The `e.args[1]` is the list of invalid shares.
    """

    good_shares: list[tuple[GFE, GFE]] = []
    bad_shares: list[GFE] = []
    for y in shares:
        x = verify_share(y, v, c)
        if x == 0:
            bad_shares.append(y)
        else:
            good_shares.append((y.coerce(x), y))
        if len(good_shares) == len(c):
            break
    if len(good_shares) < len(c):
        raise ValueError("Invalid shares", bad_shares)
    return _lagrange_interpolate(good_shares, 0)


__all__ = ["split", "recover"]
