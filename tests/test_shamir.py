import unittest
import random

import shamir
import gf


class TestShamir(unittest.TestCase):
    def setUp(self) -> None:
        self.modulus = gf.get_modulus(16)
        self.secret = gf.random(self.modulus)
        self.n = 16
        self.k = 5

    def test_shamir(self) -> None:
        for i in range(1000):
            with self.subTest(i=i):
                shares = shamir.split(self.secret, self.n, self.k)
                shares = random.sample(shares, self.k)
                recovered = shamir.recover(shares)
                self.assertEqual(int(recovered), int(self.secret))
