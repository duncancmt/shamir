from collections.abc import Iterable
import gf

# Galois Field Element
GFE = gf.ModularBinaryPolynomial[gf.BinaryPolynomial]


def split(secret: GFE, n: int, k: int) -> list[tuple[GFE, GFE], ...]:
    # from high degree to low degree
    coeffs = tuple(gf.random(secret.modulus) for _ in range(k - 1)) + (secret,)
    print("coeffs:", coeffs)
    result: list[tuple[GFE, GFE]] = []
    for i in range(1, n + 1):
        accum = secret.coerce(0)
        for coeff in coeffs:
            accum *= i
            accum += coeff
        result.append((secret.coerce(i), accum))
    return result


def recover(shares: Iterable[tuple[GFE, GFE]]) -> GFE:
    result: GFE
    accum: GFE
    for x_i, y_i in shares:
        for x_j, _ in shares:
            if x_j == x_i:
                continue
            term = x_j / (x_j - x_i)
            try:
                accum *= term
            except NameError:
                accum = y_i * term
        try:
            result += accum
        except NameError:
            result = accum
        del accum
    return result
