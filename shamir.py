"""Shamir Secret Sharing over GF(2^n).

Note: this implementation uses the hash-based verification scheme described in
https://doi.org/10.1016/j.ins.2014.03.025 and it uses the hash of the secret to
derive the coefficients of the polynomial. Each of these changes reduces the
security of the system to the security of the hash algorithm, SHAKE-256.
"""

import hashlib
import itertools
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


def _hash_GFEs(x: Iterable[GFE]) -> GFE:
    h = hashlib.shake_256()
    modulus: gf.BinaryPolynomial
    for i in x:
        try:
            if i.modulus != modulus:
                raise ValueError("Different fields")
        except NameError:
            modulus = i.modulus
            h.update(b"\xff" + _modulus_bytes(modulus))
        h.update(bytes(i))
    byte_length = (modulus.bit_length() + 6) // 8
    return gf.ModularBinaryPolynomial(h.digest(byte_length), modulus)


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


def split(
    secret: Union[tuple[GFE], tuple[GFE, GFE]],
    k: int,
    n: int,
    salt: Union[GFE, gf.BinaryPolynomial, int, bytes] = 0,
) -> tuple[tuple[GFE, ...], tuple[GFE, ...], tuple[GFE, ...], tuple[int, ...]]:
    """Split up to 2 members of GF(2^n) into some points (field element pairs).

    These points can be used to reconstruct the polynomial and extract the
    original member(s) as its coefficients.

    Returns the y-values corresponding to the x-values 1..n, 2 lists of
    auxilliary/public values required to verify the validity of each individual
    share, and the indices of the coefficients where the secrets were stored.
    """
    if k < 1:
        raise ValueError(f"Can't split into {k} shares")
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
    f_coeffs = secret[1:] + f_coeffs + secret[:1]

    # from low to high x
    f_values = tuple(_evaluate(f_coeffs, coerce(x)) for x in range(1, n + 1))
    g_values = tuple(_evaluate(g_coeffs, coerce(x)) for x in range(1, n + 1))

    # This is the hash-based verification scheme described in
    # https://doi.org/10.1016/j.ins.2014.03.025
    v = tuple(_hash_GFEs(ys) for ys in zip(f_values, g_values))
    r = _hash_GFEs(v)
    # from high to low order
    c = tuple(b + r * a for a, b in zip(f_coeffs, g_coeffs))

    return f_values, v, c, (len(c) - 1,) + ((0,) if len(secret) > 1 else ())


def verify(y_f: GFE, v: Iterable[GFE], c: Iterable[GFE]) -> GFE:
    """Check whether a alleged secret share belongs to a group of shares.

    The group of shares is specified by the public `v` and `c` values returned
    by `split`. If the share belongs to the group, this returns the x value
    corresponding to the share. If the share does not belong to the group, this
    returns 0.
    """
    # This is the hash-based verification scheme described in
    # https://doi.org/10.1016/j.ins.2014.03.025
    z = _hash_GFEs(v) * y_f
    result: int = 0
    for x, v_i in zip(itertools.count(1), v):
        y_g = _evaluate(c, x) - z
        if v_i == _hash_GFEs((y_f, y_g)):
            if result != 0:
                return y_f.coerce(0)
            result = x
    return y_f.coerce(result)


def _recover_coeffs(points: Iterable[tuple[GFE, GFE]]) -> list[GFE]:
    def lagrange_poly(x_i: GFE) -> list[GFE]:
        old = x_i.coerce(1)
        for x_j, _ in points:
            if x_j == x_i:
                continue
            old *= x_i - x_j
        old = [~old]

        for x_j, _ in points:
            if x_j == x_i:
                continue
            new = [x_j.coerce(0)]
            for coeff in old:
                new[-1] += coeff
                new.append(-x_j * coeff)
            old = new
        return old

    result: list[GFE] = []
    for x_i, y_i in points:
        for j, coeff in enumerate(lagrange_poly(x_i)):
            term = y_i * coeff
            try:
                result[j] += term
            except IndexError:
                result.append(term)
    return result


def recover(
    shares: Iterable[GFE],
    v: Iterable[GFE],
    c: Collection[GFE],
    s: Iterable[int],
) -> tuple[GFE, ...]:
    """Recover the coefficients of the polynomial determined by the given shares.

    The degree of the polynomial is inferred from the length of `c`. Shares are
    points/field element pairs/GF(2^n)^2. The indices specified in `s` determine
    which coefficients will be returned.

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
