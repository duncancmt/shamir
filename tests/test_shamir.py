import random
import secrets
import unittest

import gf
import shamir


class TestShamir(unittest.TestCase):
    def setUp(self) -> None:
        self.modulus = gf.get_modulus(256)

    def test_degenerate(self) -> None:
        for nonce in range(10):
            with self.subTest(nonce=nonce):
                secret = gf.ModularBinaryPolynomial(
                    secrets.randbits(self.modulus.bit_length() - 1),
                    self.modulus,
                )
                shares = shamir.split(secret, 1, 1, nonce)
                self.assertEqual(int(shares[0][1]), int(secret))

    def test_shamir(self) -> None:
        for k in range(2, 9):
            for n in range(k + 1, 128, 8):
                for nonce in range(10):
                    with self.subTest(k=k, n=n, nonce=nonce):
                        secret = gf.ModularBinaryPolynomial(
                            secrets.randbits(self.modulus.bit_length() - 1),
                            self.modulus,
                        )
                        shares = shamir.split(secret, k, n, nonce)
                        self.assertEqual(len(shares), n)
                        shares = random.sample(shares, k)
                        recovered = shamir.recover(shares, nonce)
                        self.assertEqual(int(recovered), int(secret))
