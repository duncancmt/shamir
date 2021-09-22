import secrets
from types import TracebackType
from typing import Literal, Optional, Tuple, Type, TypeVar, Union, Generic, overload

_default_prim_poly = {
    #1024: (
    #896: (
    #768: (
    640: (14, 3, 2),
    512: (8, 5, 2),
    448: (11, 6, 4),
    384: (16, 15, 6),
    320: (4, 3, 1),
    256: (10, 5, 2),
    224: (12, 7, 2),
    192: (15, 11, 5),
    160: (5, 3, 2),
    128: (7, 2, 1),
    64: (4, 3, 1), # for testing
    32: (7, 6, 2), # for testing
    16: (5, 3, 2), # for testing
    8: (4, 3, 1),  # Rijndael modulus, for testing
}



def get_modulus(bit_length: int) -> BinaryPolynomial:
    """Get the default modulus for the given bit length."""
    modulus = (1 << bit_length) | 1
    for i in _default_prim_poly[bit_length]:
        modulus |= 1 << i
    return BinaryPolynomial(modulus)


class BinaryPolynomial:
    """Represents a polynomial over GF(2)."""

    __slots__ = ("_value",)
    _value: int

    SelfType = TypeVar("SelfType", bound="BinaryPolynomial")

    def __init__(self, value: int) -> None:
        """Set the underlying bit-field representation, ensuring that it's positive."""
        if value < 0:
            value = -value
        self._value = value

    def _coerce(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        """Coerce an possibly-integer to a BinaryPolynomial."""
        if isinstance(other, int):
            return type(self)(other)
        return other

    def __add__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        """Addition of polynomials over GF(2)."""
        other = self._coerce(other)
        return type(self)(self._value ^ other._value)

    def __radd__(self: SelfType, other: int) -> SelfType:
        """Addition of polynomials over GF(2). Coerce integers."""
        return type(self)(other) + self

    def __neg__(self: SelfType) -> SelfType:
        """Negation of polynomials over GF(2) is the identity."""
        return self

    def __sub__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        """Subtraction of polynomials over GF(2) is addition."""
        return self + -other

    def __rsub__(self: SelfType, other: int) -> SelfType:
        """Subtraction of polynomials over GF(2) is addition. Coerce integers."""
        return type(self)(other) - self

    def __mul__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        """Multiplication of polynomials over GF(2)."""
        other = self._coerce(other)
        a = self._value
        b = other._value
        p = 0
        while b:
            if b & 1:
                p ^= a
            b >>= 1
            a <<= 1
        return type(self)(p)

    def __rmul__(self: SelfType, other: int) -> SelfType:
        """Multiplication of polynomials over GF(2). Coerce integers."""
        return type(self)(other) * self

    def __divmod__(
        self: SelfType, other: Union[SelfType, int]
    ) -> Tuple[SelfType, SelfType]:
        other = self._coerce(other)
        numerator = self._value
        denominator = other._value
        if denominator == 0:
            raise ZeroDivisionError("division by zero")
        quotient = 0
        remainder = numerator
        while remainder.bit_length() >= denominator.bit_length():
            shift = remainder.bit_length() - denominator.bit_length()
            quotient ^= 1 << shift
            remainder ^= denominator << shift
        return type(self)(quotient), type(self)(remainder)

    def __rdivmod__(self: SelfType, other: int) -> Tuple[SelfType, SelfType]:
        return divmod(type(self)(other), self)

    def __floordiv__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        """Quotient after division of polynomials over GF(2)."""
        return divmod(self, other)[0]

    def __rfloordiv__(self: SelfType, other: int) -> SelfType:
        """Quotient after division of polynomials over GF(2). Coerce integers."""
        return type(self)(other) // self

    def __mod__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        """Remainder after division of polynomials over GF(2)."""
        return divmod(self, other)[1]

    def __rmod__(self: SelfType, other: int) -> SelfType:
        """Remainder after division of polynomials over GF(2). Coerce integers."""
        return type(self)(other) % self

    def __int__(self) -> int:
        """Raw bit-field representation of the binary polynomial."""
        return self._value

    def __bool__(self) -> bool:
        """Nonzero-ness of the binary polynomial."""
        return bool(int(self))

    def __str__(self) -> str:
        """Human-readable representation of the binary polynomial."""
        return f"{type(self).__name__}({bin(int(self))})"

    def __hash__(self) -> int:
        """BinaryPolynomial hashes the same as int."""
        return hash(int(self))

    def __eq__(self, other: object) -> bool:
        """BinaryPolynomials are equal if their bit-fields are equal."""
        if isinstance(other, int):
            other = type(self)(other)
        if isinstance(other, BinaryPolynomial) and self._value == other._value:
            return True
        return NotImplemented

    del SelfType

PolynomialType = TypeVar("PolynomialType", bound=BinaryPolynomial)

class GFElement(Generic[PolynomialType]):
    __slots__ = "_value", "_modulus"
    _value: PolynomialType
    _modulus: PolynomialType

    SelfType = TypeVar("SelfType", bound="GFElement[PolynomialType]")

    @overload
    def __init__(self, value: PolynomialType, modulus: Union[PolynomialType, int]) -> None:
        ...

    @overload
    def __init__(self, value: int, modulus: PolynomialType) -> None:
        ...

    def __init__(
        self,
        value: Union[PolynomialType, int],
        modulus: Union[PolynomialType, int],
    ) -> None:
        if isinstance(modulus, int):
            if isinstance(value, int):
                raise TypeError("Unknown underlying PolynomialType")
            modulus = type(value)(modulus)
        if isinstance(value, int):
            value = type(modulus)(value)
        self._value = value % modulus
        self._modulus = modulus

    def _coerce(
        self: SelfType, other: Union[SelfType, PolynomialType, int]
    ) -> SelfType:
        if isinstance(other, int):
            return type(self)(type(self._value)(other), self._modulus)
        if isinstance(other, type(self._value)):
            return type(self)(other, self._modulus)
        if self._modulus != other._modulus: # type: ignore # mypy fails to narrow
            raise ValueError("Different fields")
        return other # type: ignore # mypy fails to narrow

    def __add__(
        self: SelfType, other: Union[SelfType, PolynomialType, int]
    ) -> SelfType:
        other = self._coerce(other)
        return type(self)(self._value + other._value, self._modulus)

    def __radd__(
        self: SelfType, other: Union[PolynomialType, int]
    ) -> SelfType:
        return type(self)(other, self._modulus) + self

    def __neg__(self: SelfType) -> SelfType:
        return self

    def __sub__(
        self: SelfType, other: Union[SelfType, PolynomialType, int]
    ) -> SelfType:
        return self + -other

    def __rsub__(
        self: SelfType, other: Union[PolynomialType, int]
    ) -> SelfType:
        return type(self)(other, self._modulus) - self

    def __mul__(
        self: SelfType, other: Union[SelfType, PolynomialType, int]
    ) -> SelfType:
        other = self._coerce(other)
        return type(self)(self._value * other._value, self._modulus)

    def __rmul__(
        self: SelfType, other: Union[PolynomialType, int]
    ) -> SelfType:
        return type(self)(other, self._modulus) * self

    def __truediv__(
        self: SelfType, other: Union[SelfType, PolynomialType, int]
    ) -> SelfType:
        other = self._coerce(other)
        return self * ~other

    def __rtruediv__(
        self: SelfType, other: Union[PolynomialType, int]
    ) -> SelfType:
        return type(self)(other, self._modulus) / self

    def __invert__(self: SelfType) -> SelfType:
        t: Union[PolynomialType, int] = 0
        t_new: Union[PolynomialType, int] = 1
        r = self._modulus
        r_new = self._value
        while r_new:
            quotient = r // r_new
            r, r_new = r_new, r - quotient * r_new
            t, t_new = t_new, t - quotient * t_new
        if r != 1: # type: ignore # mypy strict-equality gives a false-positive
            raise ZeroDivisionError("zero element or modulus is reducible")
        return type(self)(t, self._modulus)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __str__(self) -> str:
        return f"{type(self).__name__}({bin(int(self._value))}, {bin(int(self._modulus))})"

    def __hash__(self) -> int:
        return hash(int(self))

    def __int__(self) -> int:
        return int(self._value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, int):
            other = type(self._value)(other)
        if isinstance(other, type(self._value)):
            other = type(self)(other, self._modulus)
        if (
            isinstance(other, GFElement)
            and self._value == other._value
            and self._modulus == other._modulus
        ):
            return True
        return NotImplemented

    del SelfType


def random(modulus: BinaryPolynomial) -> GFElement[BinaryPolynomial]:
    value = secrets.randbits(modulus._value.bit_length() - 1)
    return GFElement(value, modulus)


__all__ = [
    "Context",
    "getcontext",
    "setcontext",
    "localcontext",
    "setfield",
    "BinaryPolynomial",
    "GFElement",
    "random",
]
