import random
import secrets
import unittest

import gf
import shamir


class TestShamir(unittest.TestCase):
    def setUp(self) -> None:
        self.modulus = gf.get_modulus(16)
        self.secret = gf.ModularBinaryPolynomial(
            secrets.randbits(self.modulus.bit_length() - 1), self.modulus
        )
        self.k = 5
        self.n = 16
        self.version = 1

    def test_shamir(self) -> None:
        for i in range(1000):
            with self.subTest(i=i):
                shares = shamir.split(
                    self.secret, self.k, self.n, self.version
                )
                self.assertEqual(len(shares), self.n)
                shares = random.sample(shares, self.k)
                recovered = shamir.recover(shares, self.version)
                self.assertEqual(int(recovered), int(self.secret))
