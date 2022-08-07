import collections
import unittest
from typing import MutableMapping

import gf


class TestBinaryPolynomialMul(unittest.TestCase):
    def setUp(self) -> None:
        self.a = gf.BinaryPolynomial(0b00110001)
        self.b = gf.BinaryPolynomial(0b00000110)
        self.expected = 0b10100110

    def test_mul(self) -> None:
        self.assertEqual(int(self.a * self.b), self.expected)


class TestBinaryPolynomialDivMod(unittest.TestCase):
    def setUp(self) -> None:
        self.a = gf.BinaryPolynomial(0b11100010110001)
        self.modulus = gf.get_modulus(8)
        self.expected = 0b00111010, 0b10001111

    def test_divmod(self) -> None:
        quotient, remainder = divmod(self.a, self.modulus)
        self.assertEqual(int(quotient), self.expected[0])
        self.assertEqual(int(remainder), self.expected[1])


class TestModularBinaryPolynomialMul(unittest.TestCase):
    def setUp(self) -> None:
        modulus = gf.get_modulus(8)
        self.a = gf.ModularBinaryPolynomial(0b110001, modulus)
        self.b = gf.ModularBinaryPolynomial(0b110, modulus)
        self.expected = 0b10100110

    def test_mul(self) -> None:
        self.assertEqual(int(self.a * self.b), self.expected)


class TestModularBinaryPolynomialInvert0(unittest.TestCase):
    def setUp(self) -> None:
        modulus = gf.get_modulus(8)
        self.a = gf.ModularBinaryPolynomial(0b1010011, modulus)
        self.expected = 0b11001010

    def test_invert(self) -> None:
        self.assertEqual(int(~self.a), self.expected)


class TestModularBinaryPolynomialInvert1(unittest.TestCase):
    def setUp(self) -> None:
        modulus = gf.get_modulus(8)
        self.a = gf.ModularBinaryPolynomial(0b110011, modulus)
        self.expected = 0b1101100

    def test_invert(self) -> None:
        self.assertEqual(int(~self.a), self.expected)


class TestModularBinaryPolynomialAddExhaustive(unittest.TestCase):
    def setUp(self) -> None:
        self.modulus = gf.get_modulus(8)

    def test_add_exhaustive(self) -> None:
        counts: MutableMapping[int, int] = collections.Counter()
        for x in range(1 << 8):
            for y in range(1 << 8):
                counts[
                    int(
                        gf.ModularBinaryPolynomial(x, self.modulus)
                        + gf.ModularBinaryPolynomial(y, self.modulus)
                    )
                ] += 1
        for i in range(1 << 8):
            with self.subTest(i=i):
                self.assertEqual(counts[i], 256)


class TestModularBinaryPolynomialMultiplyExhaustive(unittest.TestCase):
    def setUp(self) -> None:
        self.modulus = gf.get_modulus(8)

    def test_mul_exhaustive(self) -> None:
        counts: MutableMapping[int, int] = collections.Counter()
        for x in range(1 << 8):
            for y in range(1 << 8):
                counts[
                    int(
                        gf.ModularBinaryPolynomial(x, self.modulus)
                        * gf.ModularBinaryPolynomial(y, self.modulus)
                    )
                ] += 1
        for i in range(1, 1 << 8):
            with self.subTest(i=i):
                self.assertEqual(counts[i], 255)
        with self.subTest(i=i):
            self.assertEqual(counts[0], 511)


class TestModularBinaryPolynomialInvertExhaustive(unittest.TestCase):
    def setUp(self) -> None:
        self.modulus = gf.get_modulus(16)

    def test_invert_exhaustive(self) -> None:
        inverses: set[int] = set()
        for i in range(1, 1 << 16):
            with self.subTest(i=i):
                inverse = ~gf.ModularBinaryPolynomial(i, self.modulus)
                inverse_int = int(inverse)
                self.assertIn(inverse_int, range(1, 1 << 16))
                self.assertNotIn(inverse_int, inverses)
                inverses.add(inverse_int)
                self.assertEqual(int(i * inverse), 1)
