import itertools
import random
import unittest

import gf
import shamir


class TestShamir(unittest.TestCase):
    def setUp(self) -> None:
        self.modulus = gf.get_modulus(256)

    def test_degenerate(self) -> None:
        for salt in range(10):
            with self.subTest(salt=salt):
                secret = gf.ModularBinaryPolynomial(
                    random.getrandbits(self.modulus.bit_length() - 1),
                    self.modulus,
                )
                shares, v, c, _ = shamir.split((secret,), 1, 1, salt)
                self.assertEqual(int(shares[0]), int(secret))

    def test_verify(self) -> None:
        for salt in range(10):
            for k in range(2, 9):
                for n in range(k, 24, 4):
                    with self.subTest(k=k, n=n, salt=salt):
                        secret = gf.ModularBinaryPolynomial(
                            random.getrandbits(self.modulus.bit_length() - 1),
                            self.modulus,
                        )
                        shares, v, c = shamir.split(secret, k, n, salt)
                        for i, share in enumerate(shares):
                            with self.subTest(i=i):
                                self.assertEqual(
                                    shamir.verify(share, v, c), i + 1
                                )

    def test_recover(self) -> None:
        for salt in range(10):
            for k in range(2, 9):
                for n in range(k, 128, 8):
                    with self.subTest(k=k, n=n, salt=salt):
                        secret = gf.ModularBinaryPolynomial(
                            random.getrandbits(self.modulus.bit_length() - 1),
                            self.modulus,
                        )
                        shares, v, c = shamir.split(secret, k, n, salt)
                        for i in range(10):
                            with self.subTest(i=i):
                                subset = random.sample(shares, k)
                                self.assertEqual(
                                    int(shamir.recover(subset, v, c)),
                                    int(secret),
                                )

    def test_lagrange_interpolate(self) -> None:
        for salt in range(3):
            for k in range(2, 9):
                for n in range(k, 2 * k):
                    with self.subTest(k=k, n=n, salt=salt):
                        secret = gf.ModularBinaryPolynomial(
                            random.getrandbits(self.modulus.bit_length() - 1),
                            self.modulus,
                        )
                        shares, v, c = shamir.split(secret, k, n, salt)
                        points = list(
                            zip(map(secret.coerce, itertools.count(1)), shares)
                        )
                        for i in range(10):
                            with self.subTest(i=i):
                                subset = random.sample(points, k)
                                self.assertEqual(
                                    int(
                                        shamir._lagrange_interpolate(subset, 0)
                                    ),
                                    int(secret),
                                )
                                for x in range(1, n + 1):
                                    self.assertEqual(
                                        int(
                                            shamir._lagrange_interpolate(
                                                subset, x
                                            )
                                        ),
                                        int(shares[x - 1]),
                                    )
