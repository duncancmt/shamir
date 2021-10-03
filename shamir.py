"""Shamir Secret Sharing over GF(2^n).

Note: this implementation uses the hash-based verification scheme described in
https://doi.org/10.1016/j.ins.2014.03.025 and it uses the hash of the secret to
derive the coefficients of the polynomial. Each of these changes reduces the
security of the system to the security of the hash algorithm, SHAKE-256.
"""

import functools
import hashlib
import itertools
import operator
from collections.abc import Collection, Iterable
from typing import TypeVar, Union

import gf

T = TypeVar("T")


def grouper(iterable: Iterable[T], n: int) -> Iterable[tuple[T, ...]]:
    """Return fixed-length sequential chunks of the iterable.

    If there aren't enough elements of the iterable to fill the last chunk, it
    is silently dropped.
    """
    return zip(*([iter(iterable)] * n))


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


# Galois Field Element
GFE = gf.ModularBinaryPolynomial[gf.BinaryPolynomial]


def _hash_pair(
    a: GFE, b: Union[GFE, gf.BinaryPolynomial, int, bytes]
) -> bytes:
    b = a.coerce(b)
    h = hashlib.shake_256()
    h.update(b"\xff" + _modulus_bytes(a.modulus) + bytes(a) + bytes(b))
    return h.digest(len(a) * 2)


def _hash_list(x: Iterable[bytes], length: int) -> bytes:
    h = hashlib.shake_256()
    h.update(b"\xaa")
    for i in x:
        h.update(i)
    return h.digest(length)


def _evaluate(
    poly: Iterable[GFE], x: Union[GFE, gf.BinaryPolynomial, int, bytes]
) -> GFE:
    return functools.reduce(lambda accum, coeff: accum * x + coeff, poly)


def split(
    secret: Union[tuple[GFE], tuple[GFE, GFE]],
    k: int,
    n: int,
    salt: Union[GFE, gf.BinaryPolynomial, int, bytes] = 0,
) -> tuple[
    tuple[GFE, ...], tuple[bytes, ...], tuple[GFE, ...], tuple[int, ...]
]:
    """Perform Shamir Secret Sharing to split up to 2 members of GF(2^n).

    Returns the y coordinates corresponding to the x coordinates `[1..n]`, 2
    lists of auxilliary/public values required to verify the validity of each
    individual share, and the indices where the secrets were stored.

    The points (first return value and associated x coordinates) can be used to
    reconstruct a polynomial of degree `k - 1`. This polynomial has coefficients
    corresponding to the original secret(s).
    """
    if k < len(secret):
        raise ValueError(f"Can't split {len(secret)} secrets into {k} shares")
    if n < k:
        raise ValueError(
            f"Requested {n} shares which is fewer than {k} required to recover"
        )

    coerce = secret[0].coerce
    byte_length = len(secret[0])

    h = hashlib.shake_256()
    h.update(
        b"\x00"
        + _modulus_bytes(secret[0].modulus)
        + bytes(secret[0])
        + bytes(coerce(salt))
        + k.to_bytes(4, "big")
        + n.to_bytes(4, "big")
        + (bytes(secret[1]) if len(secret) > 1 else b"")  # type: ignore
    )
    random_elements = tuple(
        coerce(bytes(x))
        for x in grouper(
            h.digest(byte_length * (2 * k - len(secret))), byte_length
        )
    )

    # from high to low order
    f_coeffs = random_elements[: k - len(secret)]
    g_coeffs = random_elements[len(f_coeffs) :]
    # the optional second secret is the highest coeff
    f_coeffs = secret[1:] + f_coeffs + secret[:1]

    # from low to high x
    f_values = tuple(_evaluate(f_coeffs, coerce(x)) for x in range(1, n + 1))
    g_values = tuple(_evaluate(g_coeffs, coerce(x)) for x in range(1, n + 1))

    # This is the hash-based verification scheme described in
    # https://doi.org/10.1016/j.ins.2014.03.025
    v = tuple(map(_hash_pair, f_values, g_values))
    r = _hash_list(v, byte_length)
    # from high to low order
    c = tuple(b + r * a for a, b in zip(f_coeffs, g_coeffs))

    # Coefficients are ordered from high to low order, so we supply indices from
    # high to low to get the constant coefficient first.
    s = (len(c) - 1,) + ((0,) if len(secret) > 1 else ())
    return f_values, v, c, s


def verify(y_f: GFE, v: Iterable[bytes], c: Iterable[GFE]) -> GFE:
    """Check whether a alleged secret share belongs to a group of shares.

    The group of shares is specified by the public `v` and `c` values returned
    by `split`. If the share belongs to the group, this returns the x value
    corresponding to the share. If the share does not belong to the group, this
    returns 0.
    """
    # This is the hash-based verification scheme described in
    # https://doi.org/10.1016/j.ins.2014.03.025
    z = _hash_list(v, len(y_f)) * y_f
    result: int = 0
    for x, v_i in zip(itertools.count(1), v):
        y_g = _evaluate(c, x) - z
        if v_i == _hash_pair(y_f, y_g):
            if result != 0:
                return y_f.coerce(0)
            result = x
    return y_f.coerce(result)


def _recover_coeffs(points: Iterable[tuple[GFE, GFE]]) -> list[GFE]:
    """Return the minimal-order polynomial that intercepts each point.

    This is Lagrange interpolation. The coefficients are returned in reverse
    order (from high order to low order). Points with duplicate x coordinates
    are silently ignored.
    """
    def basis_poly(point: tuple[GFE, GFE]) -> list[GFE]:
        """Get the Lagrange basis polynomial for `point` := (`x_i`, `y_i`).

        The polynomial for `x_i` is zero for all `x_j != x_i` and is `y_i` at
        `x_i`. Strictly speaking, this isn't the *basis* polynomial because it's
        `y_i` at `x_i` instead of 1, but this difference avoids a multiplication
        by `y_i` later.
        """
        # Division is very expensive, so we compute the denominator of the
        # basis polynomial here and invert once.
        x_i, y_i = point
        old = x_i.coerce(1)
        for x_j, _ in points:
            if x_j == x_i:
                continue
            old *= x_i - x_j
        old = [y_i / old]

        for x_j, _ in points:
            if x_j == x_i:
                continue
            new = [x_j.coerce(0)]
            for coeff in old:
                new[-1] += coeff
                new.append(-x_j * coeff)
            old = new
        return old

    # By summing the coefficients of each basis polynomial, we recover the
    # coefficients of the original polynomial.
    return [
        functools.reduce(operator.add, coeffs)
        for coeffs in zip(*map(basis_poly, points))
    ]


def recover(
    shares: Iterable[GFE],
    v: Iterable[bytes],
    c: Collection[GFE],
    s: Iterable[int],
) -> tuple[GFE, ...]:
    """Recover the coefficients of the polynomial determined by the given shares.

    Shares are y coordinates of the polynomial. The x coordinate is inferred
    using `v` and `c`. The degree of the polynomial is inferred from the length
    of `c`. The indices specified in `s` determine which coefficients will be
    returned.

    This function verifies each share against the public check data `v` and `c`.
    This function raises `ValueError` if too few shares pass validation against
    `v` and `c`. The `e.args[1]` is the list of invalid shares.
    """
    good_shares: set[tuple[GFE, GFE]] = set()
    bad_shares: list[GFE] = []
    for y in shares:
        x = verify(y, v, c)
        if x == 0:
            bad_shares.append(y)
        else:
            good_shares.add((y.coerce(x), y))
        if len(good_shares) == len(c):
            break
    if len(good_shares) < len(c):
        raise ValueError("Too few valid shares. Invalid shares:", bad_shares)
    coeffs = _recover_coeffs(good_shares)
    return tuple(coeffs[i] for i in s)


__all__ = ["split", "verify", "recover"]
