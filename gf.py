"""Classes to support the pythonic manipulation of GF(2^n) elements."""

import warnings
from typing import Generic, Type, TypeVar, overload

_default_prim_poly = {
    # these excessively-large moduli are provided for future applications which
    # may want a very large group
    1024: (23, 22, 9),
    896: (23, 21, 16),
    768: (19, 17, 4),
    640: (14, 3, 2),
    512: (8, 5, 2),
    448: (11, 6, 4),
    384: (16, 15, 6),
    320: (4, 3, 1),
    # these are the only moduli used in practice due to BIP-0039 constraints
    256: (10, 5, 2),
    224: (12, 7, 2),
    192: (15, 11, 5),
    160: (5, 3, 2),
    128: (7, 2, 1),
    # these moduli are provided only for testing
    64: (4, 3, 1),
    32: (7, 6, 2),
    16: (5, 3, 2),
    8: (4, 3, 1),  # Rijndael/AES modulus
}


class BinaryPolynomial:
    """Represents a polynomial over GF(2)."""

    __slots__ = ("_value",)
    _value: int

    SelfType = TypeVar("SelfType", bound="BinaryPolynomial")

    def __init__(self, value: int | bytes) -> None:
        """Set the underlying bit-field representation, ensuring that it's positive."""
        if isinstance(value, bytes):
            value = int.from_bytes(value, "big")
        if value < 0:
            value = -value
        self._value = value

    def coerce(self: SelfType, other: SelfType | int | bytes) -> SelfType:
        """Coerce an integer or bytes to a BinaryPolynomial."""
        if isinstance(other, int | bytes):
            return type(self)(other)
        return type(self)(other._value)

    def __add__(self: SelfType, other: SelfType | int | bytes) -> SelfType:
        """Addition of polynomials over GF(2)."""
        return self.coerce(self._value ^ self.coerce(other)._value)

    def __radd__(self: SelfType, other: int | bytes) -> SelfType:
        """Addition of polynomials over GF(2). Coerce int/bytes."""
        return self.coerce(other) + self

    def __neg__(self: SelfType) -> SelfType:
        """Negation of polynomials over GF(2) is the identity."""
        return self

    def __sub__(self: SelfType, other: SelfType | int | bytes) -> SelfType:
        """Subtraction of polynomials over GF(2) is addition."""
        return self + -self.coerce(other)

    def __rsub__(self: SelfType, other: int | bytes) -> SelfType:
        """Subtraction of polynomials over GF(2) is addition. Coerce int/bytes."""
        return self.coerce(other) - self

    def __mul__(self: SelfType, other: SelfType | int | bytes) -> SelfType:
        """Multiplication of polynomials over GF(2)."""
        a = self._value
        b = self.coerce(other)._value
        p = 0
        while b:
            if b & 1:
                p ^= a
            b >>= 1
            a <<= 1
        return self.coerce(p)

    def __rmul__(self: SelfType, other: int | bytes) -> SelfType:
        """Multiplication of polynomials over GF(2). Coerce int/bytes."""
        return self.coerce(other) * self

    def __divmod__(
        self: SelfType, other: SelfType | int | bytes
    ) -> tuple[SelfType, SelfType]:
        """Quotient and remainder of division of polynomials over GF(2)."""
        numerator = self._value
        denominator = self.coerce(other)._value
        if denominator == 0:
            raise ZeroDivisionError("division by zero")
        quotient = 0
        remainder = numerator
        while remainder.bit_length() >= denominator.bit_length():
            shift = remainder.bit_length() - denominator.bit_length()
            quotient ^= 1 << shift
            remainder ^= denominator << shift
        return self.coerce(quotient), self.coerce(remainder)

    def __rdivmod__(
        self: SelfType, other: int | bytes
    ) -> tuple[SelfType, SelfType]:
        """Quotient and remainder of division of polynomials over GF(2). Coerce int/bytes."""
        return divmod(self.coerce(other), self)

    def __floordiv__(
        self: SelfType, other: SelfType | int | bytes
    ) -> SelfType:
        """Quotient after division of polynomials over GF(2)."""
        return divmod(self, other)[0]

    def __rfloordiv__(self: SelfType, other: int | bytes) -> SelfType:
        """Quotient after division of polynomials over GF(2). Coerce int/bytes."""
        return self.coerce(other) // self

    def __mod__(self: SelfType, other: SelfType | int | bytes) -> SelfType:
        """Remainder after division of polynomials over GF(2)."""
        return divmod(self, other)[1]

    def __rmod__(self: SelfType, other: int) -> SelfType:
        """Remainder after division of polynomials over GF(2). Coerce int/bytes."""
        return self.coerce(other) % self

    def __pow__(self: SelfType, other: int | bytes) -> SelfType:
        """Exponentiation of a polynomial over GF(2) by an integer."""
        if isinstance(other, bytes):
            other = int.from_bytes(other, "big")
        shifted = self
        result = self.coerce(1)
        while other:
            if other & 1:
                result *= shifted
            other >>= 1
            shifted *= shifted
        return result

    def __int__(self) -> int:
        """Raw bit-field representation."""
        return self._value

    def bit_length(self) -> int:
        """Length in bits of the bit-field representation."""
        return int(self).bit_length()

    def __len__(self) -> int:
        """Length in bytes of the bit-field."""
        return (self.bit_length() + 7) // 8

    def __bytes__(self) -> bytes:
        """Big-endian byte encoding of the bit-field."""
        return int(self).to_bytes(len(self), "big")

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
        try:
            other = self.coerce(other)  # type: ignore
        except TypeError:
            return NotImplemented
        else:
            return self._value == other._value

    del SelfType


def get_modulus(bit_length: int) -> BinaryPolynomial:
    """Get the default modulus for the given bit length."""
    if bit_length < 128:
        warnings.warn("Short bit length selected. Use this only for testing.")
    modulus = (1 << bit_length) | 1
    for i in _default_prim_poly[bit_length]:
        modulus |= 1 << i
    return BinaryPolynomial(modulus)


PolynomialType = TypeVar("PolynomialType", bound=BinaryPolynomial)


class ModularBinaryPolynomial(Generic[PolynomialType]):
    """An element of the field of binary polynomials, mod the primitive polynomial."""

    __slots__ = "_value", "_modulus"
    _value: PolynomialType
    _modulus: PolynomialType

    SelfType = TypeVar(
        "SelfType", bound="ModularBinaryPolynomial[PolynomialType]"
    )

    @overload
    def __init__(
        self, value: PolynomialType, modulus: PolynomialType | int | bytes
    ) -> None:
        ...

    @overload
    def __init__(self, value: int | bytes, modulus: PolynomialType) -> None:
        ...

    def __init__(
        self,
        value: PolynomialType | int | bytes,
        modulus: PolynomialType | int | bytes,
    ) -> None:
        """Store the value polynomial and modulus polynomial.

        Coerce int/bytes as necessary. Reduce the value by the modulus.  Raises
        TypeError if BinaryPolynomial implementation cannot be determined
        automatically.
        """
        if isinstance(modulus, int | bytes):
            if isinstance(value, int | bytes):
                raise TypeError("Unknown underlying PolynomialType")
            modulus = value.coerce(modulus)
        self._modulus = modulus
        if isinstance(value, int):
            value = modulus.coerce(value)
        elif isinstance(value, bytes):
            if len(value) != len(self):
                raise ValueError("Length mismatch")
            value = modulus.coerce(value)
        self._value = value % modulus

    def coerce(
        self: SelfType, other: SelfType | PolynomialType | int | bytes
    ) -> SelfType:
        """Coerce an int, bytes, or BinaryPolynomial to a ModularBinaryPolynomial."""
        if isinstance(other, self.polynomial_type | int | bytes):
            return type(self)(self._value.coerce(other), self._modulus)
        if self._modulus != self._modulus.coerce(other._modulus):  # type: ignore # mypy fails to narrow
            raise ValueError("Different fields")
        return type(self)(self._value.coerce(other._value), self._modulus)

    def __add__(
        self: SelfType, other: SelfType | PolynomialType | int | bytes
    ) -> SelfType:
        """Addition is the same as in the underlying BinaryPolynomial."""
        return self.coerce(self._value + self.coerce(other)._value)

    def __radd__(
        self: SelfType, other: PolynomialType | int | bytes
    ) -> SelfType:
        """Addition is the same as in the underlying BinaryPolynomial. Coerce BinaryPolynomial/int/bytes."""
        return self.coerce(other) + self

    def __neg__(self: SelfType) -> SelfType:
        """Negation is the identity."""
        return self

    def __sub__(
        self: SelfType, other: SelfType | PolynomialType | int | bytes
    ) -> SelfType:
        """Subtraction is the same as in the underlying BinaryPolynomial."""
        return self + -self.coerce(other)

    def __rsub__(
        self: SelfType, other: PolynomialType | int | bytes
    ) -> SelfType:
        """Subtraction is the same as in the underlying BinaryPolynomial. Coerce BinaryPolynomial/int/bytes."""
        return self.coerce(other) - self

    def __mul__(
        self: SelfType, other: SelfType | PolynomialType | int | bytes
    ) -> SelfType:
        """Multiplication is the same as BinaryPolynomial, but with a modular reduction."""
        # This could be made more efficient by performing modular reductions
        # incrementally during multiplication. However, this would complicate
        # the implementation.
        return self.coerce(self._value * self.coerce(other)._value)

    def __rmul__(
        self: SelfType, other: PolynomialType | int | bytes
    ) -> SelfType:
        """Multiplication is the same as BinaryPolynomial, but with a modular reduction. Coerce BinaryPolynomial/int/bytes."""
        return self.coerce(other) * self

    def __truediv__(
        self: SelfType, other: SelfType | PolynomialType | int | bytes
    ) -> SelfType:
        """Division is multiplication by the inverse of the denominator."""
        return self * ~self.coerce(other)

    def __rtruediv__(
        self: SelfType, other: PolynomialType | int | bytes
    ) -> SelfType:
        """Division is multiplication by the inverse of the denominator. Coerce BinaryPolynomial/int/bytes."""
        return self.coerce(other) / self

    def __invert__(self: SelfType) -> SelfType:
        """Inversion is performed by extended GCD over the BinaryPolynomial."""
        t: PolynomialType | int = 0
        t_new: PolynomialType | int = 1
        r = self._modulus
        r_new = self._value
        while r_new:
            quotient = r // r_new
            r, r_new, t, t_new = (
                r_new,
                r - quotient * r_new,
                t_new,
                t - quotient * t_new,
            )
        if r != 1:  # type: ignore # mypy strict-equality gives a false-positive
            raise ZeroDivisionError("zero element or modulus is reducible")
        return self.coerce(t)

    def __pow__(self: SelfType, other: int | bytes) -> SelfType:
        """Exponentiation by an integer is performed by square-and-multiply."""
        if isinstance(other, bytes):
            other = int.from_bytes(other, "big")
        shifted = self
        result = self.coerce(1)
        while other:
            if other & 1:
                result *= shifted
            other >>= 1
            shifted *= shifted
        return result

    def bit_length(self) -> int:
        """Length in bits of the field elements."""
        return self.modulus.bit_length() - 1

    def __len__(self) -> int:
        """Length in bytes of the field elements."""
        return (self.bit_length() + 7) // 8

    def __bytes__(self) -> bytes:
        """Big-endian byte encoding of the bit-field of the value.

        The length is the same for all members of the field because this uses
        the length of the modulus.
        """
        # This is different from bytes(self._value) because it uses the length
        # of the modulus
        return int(self).to_bytes(len(self), "big")

    def __int__(self) -> int:
        """Return the integer representation of the BinaryPolynomial."""
        return int(self._value)

    def __bool__(self) -> bool:
        """Nonzero-ness of the BinaryPolynomial (congruence to zero)."""
        return bool(self._value)

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{type(self).__name__}({bin(int(self._value))}, {bin(int(self._modulus))})"

    __repr__ = __str__

    def __hash__(self) -> int:
        """ModularyBinaryPolynomial hashes the same as int."""
        return hash(int(self))

    def __eq__(self, other: object) -> bool:
        """ModularBinaryPolynomials are equal if their values and moduli are equal."""
        try:
            other = self.coerce(other)  # type: ignore
        except TypeError:
            return NotImplemented
        except ValueError:
            return False  # different fields
        else:
            return self._value == other._value

    @property
    def modulus(self) -> PolynomialType:
        """The modulus of the field."""
        return self._modulus

    @property
    def polynomial_type(self) -> Type[PolynomialType]:
        """The underlying BinaryPolynomial type."""
        return type(self._value)

    del SelfType


__all__ = [
    "get_modulus",
    "BinaryPolynomial",
    "ModularBinaryPolynomial",
]
