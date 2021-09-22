import unittest

import gf


class TestBinaryPolynomialMul(unittest.TestCase):
    def setUp(self) -> None:
        gf.setfield(8)
        self.a = gf.BinaryPolynomial(0b00110001)
        self.b = gf.BinaryPolynomial(0b00000110)
        self.expected = 0b10100110

    def test_mul(self) -> None:
        self.assertEqual(int(self.a * self.b), self.expected)


class TestBinaryPolynomialDivMod(unittest.TestCase):
    def setUp(self) -> None:
        gf.setfield(8)
        self.a = gf.BinaryPolynomial(0b11100010110001)
        self.expected = 0b00111010, 0b10001111

    def test_divmod(self) -> None:
        quotient, remainder = divmod(self.a, gf.getcontext().modulus)
        self.assertEqual(int(quotient), self.expected[0])
        self.assertEqual(int(remainder), self.expected[1])


class TestGFElementMul(unittest.TestCase):
    def setUp(self) -> None:
        gf.setfield(8)
        self.a = gf.GFElement(0b110001)
        self.b = gf.GFElement(0b110)
        self.expected = 0b10100110

    def test_mul(self) -> None:
        self.assertEqual(int(self.a * self.b), self.expected)


class TestGFElementInvert0(unittest.TestCase):
    def setUp(self) -> None:
        gf.setfield(8)
        self.a = gf.GFElement(0b1010011)
        self.expected = 0b11001010

    def test_invert(self) -> None:
        self.assertEqual(int(~self.a), self.expected)


class TestGFElementInvert1(unittest.TestCase):
    def setUp(self) -> None:
        gf.setfield(8)
        self.a = gf.GFElement(0b110011)
        self.expected = 0b1101100

    def test_invert(self) -> None:
        self.assertEqual(int(~self.a), self.expected)


class TestGFElementInvertExhaustive(unittest.TestCase):
    def setUp(self) -> None:
        gf.setfield(16)

    def test_invert_exhaustive(self) -> None:
        inverses = set()
        for i in range(1, 1<<16):
            with self.subTest(i=i):
                inverse = ~gf.GFElement(i)
                self.assertNotIn(inverse, inverses)
                inverses.add(inverse)
                self.assertEqual(int(i * inverse), 1)
