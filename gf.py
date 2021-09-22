import contextvars
import secrets
from types import TracebackType
from typing import Literal, Optional, Tuple, Type, TypeVar, Union

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


class Context:
    """Stores the default modulus for newly-created field elements."""

    modulus: int

    SelfType = TypeVar("SelfType", bound="Context")

    def __init__(self, modulus: int) -> None:
        """Set the modulus."""
        self.modulus = modulus

    def copy(self: SelfType) -> SelfType:
        """Return a copy with the same modulus."""
        return type(self)(self.modulus)

    del SelfType


_current_context: contextvars.ContextVar[Context] = contextvars.ContextVar(
    "gf_context"
)


# Don't contaminate the namespace
del contextvars


def getcontext() -> Context:
    """Return this thread's context.

    If this thread does not yet have a context, return a new context and set
    this thread's context. New contexts have zero modulus, which is invalid.
    """
    try:
        return _current_context.get()
    except LookupError:
        context = Context(0)
        _current_context.set(context)
        return context


def setcontext(context: Context) -> None:
    """Set this thread's context to context."""
    _current_context.set(context)


def localcontext(ctx: Optional[Context] = None) -> "_ContextManager":
    """Return a context manager that swaps the current context for the given context."""
    if ctx is None:
        ctx = getcontext()
    return _ContextManager(ctx)


def setfield(bit_length: int) -> None:
    modulus = (1 << bit_length) | 1
    for i in _default_prim_poly[bit_length]:
        modulus |= 1 << i
    ctx = Context(modulus)
    setcontext(ctx)


class _ContextManager:
    """Context manager class to support localcontext().
    Sets a copy of the supplied context in __enter__() and restores
    the previous decimal context in __exit__()
    """

    new_context: Context
    saved_context: Context

    def __init__(self, new_context: Context):
        self.new_context = new_context.copy()

    def __enter__(self) -> Context:
        self.saved_context = getcontext()
        setcontext(self.new_context)
        return self.new_context

    def __exit__(
        self,
        exctype: Optional[Type[BaseException]],
        excinst: Optional[BaseException],
        exctb: Optional[TracebackType],
    ) -> Literal[False]:
        setcontext(self.saved_context)
        return False


class BinaryPolynomial:
    __slots__ = ("_value",)
    _value: int

    SelfType = TypeVar("SelfType", bound="BinaryPolynomial")

    def __init__(self, value: int) -> None:
        if value < 0:
            value = -value
        self._value = value

    def _coerce(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        if isinstance(other, int):
            return type(self)(other)
        return other

    def __add__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        other = self._coerce(other)
        return type(self)(self._value ^ other._value)

    def __radd__(self: SelfType, other: int) -> SelfType:
        return type(self)(other) + self

    def __neg__(self: SelfType) -> SelfType:
        return self

    def __sub__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        return self + -other

    def __rsub__(self: SelfType, other: int) -> SelfType:
        return type(self)(other) - self

    def __mul__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
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
        return divmod(self, other)[0]

    def __rfloordiv__(self: SelfType, other: int) -> SelfType:
        return type(self)(other) // self

    def __mod__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        return divmod(self, other)[1]

    def __rmod__(self: SelfType, other: int) -> SelfType:
        return type(self)(other) % self

    def __int__(self) -> int:
        return self._value

    def __bool__(self) -> bool:
        return bool(int(self))

    def __str__(self) -> str:
        return f"{type(self).__name__}({bin(int(self))})"

    def __hash__(self) -> int:
        return hash(int(self))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, int):
            other = type(self)(other)
        if isinstance(other, BinaryPolynomial) and self._value == other._value:
            return True
        return NotImplemented

    del SelfType


class GFElement:
    __slots__ = "_value", "_modulus"
    _value: BinaryPolynomial
    _modulus: BinaryPolynomial

    SelfType = TypeVar("SelfType", bound="GFElement")

    def __init__(
        self,
        value: Union[BinaryPolynomial, int],
        modulus: Union[BinaryPolynomial, int, None] = None,
    ) -> None:
        if modulus is None:
            modulus = getcontext().modulus
        if isinstance(modulus, int):
            modulus = BinaryPolynomial(modulus)
        self._modulus = modulus
        if isinstance(value, int):
            value = BinaryPolynomial(value)
        self._value = value % modulus

    def _coerce(
        self: SelfType, other: Union[SelfType, BinaryPolynomial, int]
    ) -> SelfType:
        if isinstance(other, (int, BinaryPolynomial)):
            other = type(self)(other, self._modulus)
        if self._modulus != other._modulus:
            raise ValueError("Different fields")
        return other

    def __add__(
        self: SelfType, other: Union[SelfType, BinaryPolynomial, int]
    ) -> SelfType:
        other = self._coerce(other)
        return type(self)(self._value + other._value, self._modulus)

    def __radd__(
        self: SelfType, other: Union[BinaryPolynomial, int]
    ) -> SelfType:
        return type(self)(other, self._modulus) + self

    def __neg__(self: SelfType) -> SelfType:
        return self

    def __sub__(
        self: SelfType, other: Union[SelfType, BinaryPolynomial, int]
    ) -> SelfType:
        return self + -other

    def __rsub__(
        self: SelfType, other: Union[BinaryPolynomial, int]
    ) -> SelfType:
        return type(self)(other, self._modulus) - self

    def __mul__(
        self: SelfType, other: Union[SelfType, BinaryPolynomial, int]
    ) -> SelfType:
        other = self._coerce(other)
        return type(self)(self._value * other._value, self._modulus)

    def __rmul__(
        self: SelfType, other: Union[BinaryPolynomial, int]
    ) -> SelfType:
        return type(self)(other, self._modulus) * self

    def __truediv__(
        self: SelfType, other: Union[SelfType, BinaryPolynomial, int]
    ) -> SelfType:
        other = self._coerce(other)
        return self * ~other

    def __rtruediv__(
        self: SelfType, other: Union[BinaryPolynomial, int]
    ) -> SelfType:
        return type(self)(other, self._modulus) / self

    def __invert__(self: SelfType) -> SelfType:
        t: Union[BinaryPolynomial, int] = 0
        t_new: Union[BinaryPolynomial, int] = 1
        r = self._modulus
        r_new = self._value
        while r_new:
            quotient = r // r_new
            r, r_new = r_new, r - quotient * r_new
            t, t_new = t_new, t - quotient * t_new
        if r != 1:
            raise ZeroDivisionError("zero element or modulus is reducible")
        return type(self)(t, self._modulus)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __str__(self) -> str:
        context = getcontext()
        if self._modulus == context.modulus:
            return f"{type(self).__name__}({bin(int(self._value))})"
        return f"{type(self).__name__}({bin(int(self._value))}, {bin(int(self._modulus))})"

    def __hash__(self) -> int:
        return hash(int(self))

    def __int__(self) -> int:
        return int(self._value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, (BinaryPolynomial, int)):
            other = type(self)(other, self._modulus)
        if (
            isinstance(other, GFElement)
            and self._value == other._value
            and self._modulus == other._modulus
        ):
            return True
        return NotImplemented

    del SelfType


def random() -> GFElement:
    modulus = getcontext().modulus
    value = secrets.randbits(modulus.bit_length() - 1)
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
