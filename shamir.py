from collections.abc import Iterable
import gf

# Galois Field Element
GFE = gf.ModularBinaryPolynomial[gf.BinaryPolynomial]


def split(secret: GFE, n: int, k: int) -> list[tuple[GFE, GFE]]:
    # from high degree to low degree
    coeffs = tuple(gf.random(secret.modulus) for _ in range(k - 1)) + (secret,)
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
    for x_i, accum in shares:
        for x_j, _ in shares:
            if x_j == x_i:
                continue
            accum *= x_j / (x_j - x_i)
        try:
            result += accum
        except NameError:
            result = accum
    return result
