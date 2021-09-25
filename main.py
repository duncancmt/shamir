import sys

import bip39
import gf
import shamir

# Galois Field Element
GFE = gf.ModularBinaryPolynomial[gf.BinaryPolynomial]

try:
    if sys.argv[1] == "split":
        mnemonic = sys.argv[2]
        entropy = bip39.decode(mnemonic)
        to_recover = int(sys.argv[3])
        num_shares = int(sys.argv[4])
        try:
            version = int(sys.argv[5])
        except:
            version = 0
        secret = gf.ModularBinaryPolynomial(
            entropy, gf.get_modulus(len(entropy) * 8)
        )
        for x, y in shamir.split(secret, to_recover, num_shares, version):
            print(
                int(x),
                bip39.encode(bytes(y)),
                sep=": ",
                file=sys.stdout,
                flush=True,
            )
    elif sys.argv[1] == "recover":
        shares: list[tuple[GFE, GFE]] = []
        for i, share in shamir.grouper(sys.argv[2:], 2):
            decoded = bip39.decode(share)
            group_element = gf.ModularBinaryPolynomial(
                decoded, gf.get_modulus(len(decoded) * 8)
            )
            shares.append((group_element.coerce(int(i)), group_element))
        try:
            version = int(sys.argv[-1])
        except:
            version = 0
        print(
            bip39.encode(bytes(shamir.recover(shares, version))),
            file=sys.stdout,
            flush=True,
        )
except ValueError as e:
    print(e.args[0], file=sys.stderr, flush=True)
    sys.exit(1)
