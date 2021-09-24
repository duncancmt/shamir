from collections.abc import Iterable
import gf

E = gf.GFElement[gf.BinaryPolynomial]

def split(secret: E, n:int, k:int) -> tuple[tuple[E, E], ...]:
    coeffs = tuple(gf.random(secret.modulus) for _ in range(k - 1)) + (secret,) # from high degree to low degree
    print("coeffs:", coeffs)
    result: list[tuple[E, E]] = []
    for i in range(1, n+1):
        accum = secret.coerce(0)
        for coeff in coeffs:
            accum *= i
            accum += coeff
        result.append((secret.coerce(i), accum))
    return tuple(result)
    
    
def recover(shares: Iterable[tuple[E, E]]) -> E:
    result: E
    accum: E
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
