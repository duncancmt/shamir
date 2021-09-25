from __future__ import annotations

import secrets
from types import TracebackType
from typing import Generic, Literal, Optional, Type, TypeVar, Union, overload

_default_prim_poly = {
    1024: (23, 22, 9),
    896: (23, 21, 16),
    768: (19, 17, 4),
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
    64: (4, 3, 1),  # for testing
    32: (7, 6, 2),  # for testing
    16: (5, 3, 2),  # for testing
    8: (4, 3, 1),  # Rijndael/AES modulus, for testing
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

    def __init__(self, value: Union[int, bytes]) -> None:
        """Set the underlying bit-field representation, ensuring that it's positive."""
        if isinstance(value, bytes):
            value = int.from_bytes(value, "little")
        if value < 0:
            value = -value
        self._value = value

    def coerce(self: SelfType, other: Union[SelfType, int, bytes]) -> SelfType:
        """Coerce a possibly-integer to a BinaryPolynomial."""
        if isinstance(other, (int, bytes)):
            return type(self)(other)
        return type(self)(other._value)

    def __add__(
        self: SelfType, other: Union[SelfType, int, bytes]
    ) -> SelfType:
        """Addition of polynomials over GF(2)."""
        other = self.coerce(other)
        return type(self)(self._value ^ other._value)

    def __radd__(self: SelfType, other: Union[int, bytes]) -> SelfType:
        """Addition of polynomials over GF(2). Coerce integers."""
        return type(self)(other) + self

    def __neg__(self: SelfType) -> SelfType:
        """Negation of polynomials over GF(2) is the identity."""
        return self

    def __sub__(
        self: SelfType, other: Union[SelfType, int, bytes]
    ) -> SelfType:
        """Subtraction of polynomials over GF(2) is addition."""
        other = self.coerce(other)
        return self + -other

    def __rsub__(self: SelfType, other: Union[int, bytes]) -> SelfType:
        """Subtraction of polynomials over GF(2) is addition. Coerce integers."""
        return type(self)(other) - self

    def __mul__(
        self: SelfType, other: Union[SelfType, int, bytes]
    ) -> SelfType:
        """Multiplication of polynomials over GF(2)."""
        other = self.coerce(other)
        a = self._value
        b = other._value
        p = 0
        while b:
            if b & 1:
                p ^= a
            b >>= 1
            a <<= 1
        return type(self)(p)

    def __rmul__(self: SelfType, other: Union[int, bytes]) -> SelfType:
        """Multiplication of polynomials over GF(2). Coerce integers."""
        return type(self)(other) * self

    def __divmod__(
        self: SelfType, other: Union[SelfType, int, bytes]
    ) -> tuple[SelfType, SelfType]:
        other = self.coerce(other)
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

    def __rdivmod__(
        self: SelfType, other: Union[int, bytes]
    ) -> tuple[SelfType, SelfType]:
        return divmod(type(self)(other), self)

    def __floordiv__(
        self: SelfType, other: Union[SelfType, int, bytes]
    ) -> SelfType:
        """Quotient after division of polynomials over GF(2)."""
        return divmod(self, other)[0]

    def __rfloordiv__(self: SelfType, other: Union[int, bytes]) -> SelfType:
        """Quotient after division of polynomials over GF(2). Coerce integers."""
        return type(self)(other) // self

    def __mod__(
        self: SelfType, other: Union[SelfType, int, bytes]
    ) -> SelfType:
        """Remainder after division of polynomials over GF(2)."""
        return divmod(self, other)[1]

    def __rmod__(self: SelfType, other: Union[int, bytes]) -> SelfType:
        """Remainder after division of polynomials over GF(2). Coerce integers."""
        return type(self)(other) % self

    def __pow__(self: SelfType, other: Union[int, bytes]) -> SelfType:
        if isinstance(other, bytes):
            other = int.from_bytes(other, "little")
        shifted = self
        result = type(self)(1)
        while other:
            if other & 1:
                result *= shifted
            other >>= 1
            shifted *= shifted
        return result

    def __int__(self) -> int:
        """Raw bit-field representation of the binary polynomial."""
        return self._value

    def bit_length(self) -> int:
        return int(self).bit_length()

    def __len__(self) -> int:
        return (self.bit_length() + 7) // 8

    def __bytes__(self) -> bytes:
        if not self:
            return b""
        return int(self).to_bytes(len(self), "little")

    def __bool__(self) -> bool:
        """Nonzero-ness of the binary polynomial."""
        return bool(int(self))

    def __str__(self) -> str:
        """Human-readable representation of the binary polynomial."""
        return f"{type(self).__name__}({bin(int(self))})"

    __repr__ = __str__

    def __hash__(self) -> int:
        """BinaryPolynomial hashes the same as int."""
        return hash(int(self))

    def __eq__(self, other: object) -> bool:
        """BinaryPolynomials are equal if their bit-fields are equal."""
        if isinstance(other, (int, bytes)):
            other = type(self)(other)
        if isinstance(other, BinaryPolynomial) and self._value == other._value:
            return True
        return NotImplemented

    del SelfType


PolynomialType = TypeVar("PolynomialType", bound=BinaryPolynomial)


class ModularBinaryPolynomial(Generic[PolynomialType]):
    __slots__ = "_value", "_modulus"
    _value: PolynomialType
    _modulus: PolynomialType

    SelfType = TypeVar(
        "SelfType", bound="ModularBinaryPolynomial[PolynomialType]"
    )

    @overload
    def __init__(
        self, value: PolynomialType, modulus: Union[PolynomialType, int, bytes]
    ) -> None:
        ...

    @overload
    def __init__(
        self, value: Union[int, bytes], modulus: PolynomialType
    ) -> None:
        ...

    def __init__(
        self,
        value: Union[PolynomialType, int, bytes],
        modulus: Union[PolynomialType, int, bytes],
    ) -> None:
        if isinstance(modulus, (int, bytes)):
            if isinstance(value, (int, bytes)):
                raise TypeError("Unknown underlying PolynomialType")
            modulus = type(value)(modulus)
        if isinstance(value, (int, bytes)):
            value = type(modulus)(value)
        self._value = value % modulus
        self._modulus = modulus

    def coerce(
        self: SelfType, other: Union[SelfType, PolynomialType, int, bytes]
    ) -> SelfType:
        if isinstance(other, (self.polynomial_type, int, bytes)):
            return type(self)(self._value.coerce(other), self._modulus)
        if self._modulus != self._modulus.coerce(other._modulus):  # type: ignore # mypy fails to narrow
            raise ValueError("Different fields")
        return type(self)(self._value.coerce(other._value), self._modulus)

    def __add__(
        self: SelfType, other: Union[SelfType, PolynomialType, int, bytes]
    ) -> SelfType:
        other = self.coerce(other)
        return type(self)(self._value + other._value, self._modulus)

    def __radd__(
        self: SelfType, other: Union[PolynomialType, int, bytes]
    ) -> SelfType:
        return type(self)(other, self._modulus) + self

    def __neg__(self: SelfType) -> SelfType:
        return self

    def __sub__(
        self: SelfType, other: Union[SelfType, PolynomialType, int, bytes]
    ) -> SelfType:
        other = self.coerce(other)
        return self + -other

    def __rsub__(
        self: SelfType, other: Union[PolynomialType, int, bytes]
    ) -> SelfType:
        return type(self)(other, self._modulus) - self

    def __mul__(
        self: SelfType, other: Union[SelfType, PolynomialType, int, bytes]
    ) -> SelfType:
        other = self.coerce(other)
        return type(self)(self._value * other._value, self._modulus)

    def __rmul__(
        self: SelfType, other: Union[PolynomialType, int, bytes]
    ) -> SelfType:
        return type(self)(other, self._modulus) * self

    def __truediv__(
        self: SelfType, other: Union[SelfType, PolynomialType, int, bytes]
    ) -> SelfType:
        other = self.coerce(other)
        return self * ~other

    def __rtruediv__(
        self: SelfType, other: Union[PolynomialType, int, bytes]
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
        if r != 1:  # type: ignore # mypy strict-equality gives a false-positive
            raise ZeroDivisionError("zero element or modulus is reducible")
        return type(self)(t, self._modulus)

    def __pow__(self: SelfType, other: Union[int, bytes]) -> SelfType:
        if isinstance(other, bytes):
            other = int.from_bytes(other, "little")
        shifted = self
        result = type(self)(1, self._modulus)
        while other:
            if other & 1:
                result *= shifted
            other >>= 1
            shifted *= shifted
        return result

    def bit_length(self) -> int:
        return self.modulus.bit_length() - 1

    def __len__(self) -> int:
        return (self.bit_length() + 7) // 8

    def __bytes__(self) -> bytes:
        # TODO: this is different from bytes(self._value) add unit test to demonstrate
        return int(self).to_bytes(len(self), "little")

    def __int__(self) -> int:
        return int(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __str__(self) -> str:
        return f"{type(self).__name__}({bin(int(self._value))}, {bin(int(self._modulus))})"

    __repr__ = __str__

    def __hash__(self) -> int:
        return hash(int(self))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, (self.polynomial_type, int, bytes)):
            other = type(self)(self._value.coerce(other), self._modulus)
        if (
            isinstance(other, ModularBinaryPolynomial)
            and self._value == other._value
            and self._modulus == other._modulus
        ):
            return True
        return NotImplemented

    @property
    def modulus(self) -> PolynomialType:
        return self._modulus

    @property
    def polynomial_type(self) -> Type[PolynomialType]:
        return type(self._value)

    del SelfType


__all__ = [
    "get_modulus",
    "BinaryPolynomial",
    "ModularBinaryPolynomial",
]
