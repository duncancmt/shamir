from typing import Optional, TypeVar, Type, Tuple, Union, Literal, NoReturn
from types import TracebackType

_default_prim_poly = {
    256: (10, 5, 2),
    224: (12, 7, 2),
    192: (15, 11, 5),
    128: (7, 2, 1),
    8: (4, 3, 1),
}

import contextvars


class Context(object):
    bit_length: int
    modulus: int

    def __init__(self, bit_length: int, modulus: int) -> None:
        if modulus.bit_length() >= bit_length:
            raise ValueError("modulus exceeds bit length")
        self.bit_length = bit_length
        self.modulus = modulus

    SelfType = TypeVar("SelfType", bound="Context")

    def copy(self: SelfType) -> SelfType:
        return type(self)(self.bit_length, self.modulus)

    del SelfType


_current_context: contextvars.ContextVar[Context] = contextvars.ContextVar("gf_context")


def getcontext() -> Context:
    """Returns this thread's context.
    If this thread does not yet have a context, returns
    a new context and sets this thread's context.
    New contexts are copies of DefaultContext.
    """
    try:
        return _current_context.get()
    except LookupError:
        context = Context(1, 0)
        _current_context.set(context)
        return context


def setcontext(context: Context) -> None:
    """Set this thread's context to context."""
    _current_context.set(context)


def localcontext(ctx: Optional[Context] = None) -> "_ContextManager":
    if ctx is None:
        ctx = getcontext()
    return _ContextManager(ctx)


class _ContextManager(object):
    """Context manager class to support localcontext().
    Sets a copy of the supplied context in __enter__() and restores
    the previous decimal context in __exit__()
    """

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


class BinaryPolynomial(object):
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
        return type(self)(other) + -self

    def __mul__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        other = self._coerce(other)
        a = self._value
        b = other._value
        p = 0
        while a and b:
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
        quotient = 0
        remainder = numerator
        while remainder and remainder.bit_length() >= denominator.bit_length():
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

    def __div__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        return NotImplemented

    def __rdiv__(self: SelfType, other: int) -> NoReturn:
        raise NotImplementedError

    def __int__(self) -> int:
        return self._value

    def __bool__(self) -> bool:
        return bool(int(self))

    def __str__(self) -> str:
        return f"BinaryPolynomial({bin(self._value)})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, (int, BinaryPolynomial)):
            other = self._coerce(other)
            return self._value == other._value
        return False

    del SelfType


class Element(object):
    __slots__ = "_value", "_modulus"
    _value: BinaryPolynomial
    _modulus: BinaryPolynomial

    SelfType = TypeVar("SelfType", bound="Element")

    def __init__(
        self,
        value: Union[BinaryPolynomial, int],
        modulus: Union[BinaryPolynomial, int, None] = None,
    ) -> None:
        if isinstance(value, int):
            value = BinaryPolynomial(value)
        self._value = value
        if modulus is None:
            modulus = getcontext().modulus
        if isinstance(modulus, int):
            modulus = BinaryPolynomial(modulus)
        self._modulus = modulus

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

    def __radd__(self: SelfType, other: Union[BinaryPolynomial, int]) -> SelfType:
        return type(self)(other, self._modulus) + self

    def __neg__(self: SelfType) -> SelfType:
        return self

    def __sub__(
        self: SelfType, other: Union[SelfType, BinaryPolynomial, int]
    ) -> SelfType:
        return self + -other

    def __rsub__(self: SelfType, other: Union[BinaryPolynomial, int]) -> SelfType:
        return type(self)(other, self._modulus) - self

    def __mul__(
        self: SelfType, other: Union[SelfType, BinaryPolynomial, int]
    ) -> SelfType:
        other = self._coerce(other)
        modulus = self._modulus._value
        selector = 1 << (modulus.bit_length() - 1)
        mask = selector - 1
        modulus &= mask
        a = self._value._value
        b = other._value._value
        p = 0
        while a and b:
            if b & 1:
                p ^= a
            b >>= 1
            a <<= 1
            if a & selector:
                a ^= modulus
                a &= mask
        return type(self)(p, self._modulus)

    def __rmul__(self: SelfType, other: Union[BinaryPolynomial, int]) -> SelfType:
        return type(self)(other, self._modulus) * self

    def __truediv__(
        self: SelfType, other: Union[SelfType, BinaryPolynomial, int]
    ) -> SelfType:
        other = self._coerce(other)
        return self * ~other

    def __invert__(self: SelfType) -> SelfType:
        modulus = self._modulus
        t: Union[BinaryPolynomial, int] = 0
        newt: Union[BinaryPolynomial, int] = 1
        r = modulus
        newr = self._value
        while newr:
            quotient = r // newr
            r, newr = newr, r - quotient * newr
            t, newt = newt, t - quotient * newt
            print("quotient:", quotient)
            print("r:", r, "newr:", newr)
            print("t:", t, "newt:", newt)
        # if r != 1:
        #     raise RuntimeError("zero element or modulus is not irreducible")
        # if t > modulus:
        #     t = divmod(t, modulus)[1]
        return type(self)(t, self._modulus)

    def __bool__(self) -> bool:
        return self._value % self._modulus != 0

    def __str__(self) -> str:
        context = getcontext()
        if self._modulus == context.modulus:
            return f"Element({bin(int(self._value))})"
        else:
            return f"Element({bin(int(self._value))} over {bin(int(self._modulus))})"

    def __int__(self) -> int:
        return int(self._value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, (int, Element)):
            other = self._coerce(other)
            return self._value == other._value
        return False

    del SelfType


# Don't contaminate the namespace
del contextvars
