from typing import Optional, TypeVar, Type, Tuple, Union, Literal
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


class Element(object):
    __slots__ = "_value", "_bit_length", "_modulus"
    _value: int
    _bit_length: int
    _modulus: int

    SelfType = TypeVar("SelfType", bound="Element")

    def __init__(self, value: int, context: Optional[Context] = None) -> None:
        self._value = value
        if context is None:
            context = getcontext()
        self._bit_length = context.bit_length
        self._modulus = context.modulus

    def _coerce(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        if isinstance(other, int):
            return type(self)(other, Context(self._bit_length, self._modulus))
        context = getcontext()
        if self._bit_length != context.bit_length or self._modulus != context.modulus:
            raise RuntimeError("Wrong context")
        if self._bit_length != other._bit_length or self._modulus != other._modulus:
            raise TypeError("Different fields")
        return other

    def __add__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        other = self._coerce(other)
        return type(self)(
            self._value ^ other._value, Context(self._bit_length, self._modulus)
        )

    def __neg__(self: SelfType) -> SelfType:
        return self

    def __sub__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        return self + -other

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
        context = Context(self._bit_length, self._modulus)
        return type(self)(quotient, context), type(self)(remainder, context)

    def __mul__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        other = self._coerce(other)
        bit_length = self._bit_length
        modulus = self._modulus
        selector = 1 << bit_length
        mask = selector - 1
        a = self._value
        b = other._value
        p = 0
        for _ in range(bit_length):
            if b & 1:
                p ^= a
            b >>= 1
            a <<= 1
            if a & selector:
                a ^= modulus
                a &= mask
        return type(self)(p, Context(bit_length, modulus))

    def __div__(self: SelfType, other: Union[SelfType, int]) -> SelfType:
        return self * ~other

    def __invert__(self: SelfType) -> SelfType:
        modulus = (1 << self._bit_length) | self._modulus
        context = Context(self._bit_length, self._modulus)
        t = type(self)(0, context)
        newt = type(self)(1, context)
        r = type(self)(modulus, context)
        newr = self
        while newr:
            quotient = divmod(r, newr)[0]
            # TODO: this needs to be polynomial multiplication, not field multiplication
            r, newr = newr, r - quotient * newr
            t, newt = newt, t - quotient * newt
            print("quotient:", quotient)
            print("r:", r, "newr:", newr)
            print("t:", t, "newt:", newt)
        # if r != 1:
        #     raise RuntimeError("zero element or modulus is not irreducible")
        # if t > modulus:
        #     t = divmod(t, modulus)[1]
        return t

    def __bool__(self) -> bool:
        return (
            divmod(
                self,
                type(self)(
                    (1 << self._bit_length) | self._modulus,
                    Context(self._bit_length, self._modulus),
                ),
            )[1]
            != 0
        )

    def __str__(self) -> str:
        context = getcontext()
        if self._bit_length == context.bit_length and self._modulus == context.modulus:
            return f"Element({bin(self._value)})"
        else:
            return f"Element({bin(self._value)} over {bin((1 << self._bit_length) | self._modulus)})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, (int, Element)):
            other = self._coerce(other)
            return self._value == other._value
        return False


# Don't contaminate the namespace
del contextvars
