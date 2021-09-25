import random
import secrets
import unittest

import gf
import shamir


class TestShamir(unittest.TestCase):
    def setUp(self) -> None:
        self.modulus = gf.get_modulus(256)

    def test_shamir(self) -> None:
        for k in range(1, 9):
            for n in range(k + 1, 128, 8):
                for version in range(10):
                    with self.subTest(k=k, n=n, version=version):
                        secret = gf.ModularBinaryPolynomial(
                            secrets.randbits(self.modulus.bit_length() - 1), self.modulus
                        )
                        shares = shamir.split(secret, k, n, version)
                        self.assertEqual(len(shares), n)
                        shares = random.sample(shares, k)
                        recovered = shamir.recover(shares, version)
                        self.assertEqual(int(recovered), int(secret))
