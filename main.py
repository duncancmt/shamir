import argparse
import sys
from collections.abc import Iterable

import bip39
import gf
import shamir

# Galois Field Element
GFE = gf.ModularBinaryPolynomial[gf.BinaryPolynomial]


def mnemonic(x: str) -> GFE:
    x = bip39.decode(x)
    x = gf.ModularBinaryPolynomial(x, gf.get_modulus(len(x) * 8))
    return x


def int_and_mnemonic(arg: str) -> tuple[GFE, GFE]:
    x, y = arg.split(",")
    y = mnemonic(y)
    x = y.coerce(int(x))
    return x, y


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(required=True, dest="subcommand")
split_parser = subparsers.add_parser("split")
split_parser.add_argument("secret", type=mnemonic)
split_parser.add_argument("--shares", type=int)
split_parser.add_argument("--needed", type=int)
split_parser.add_argument("--version", type=int, default=0)
recover_parser = subparsers.add_parser("recover")
recover_parser.add_argument("shares", nargs="+", type=int_and_mnemonic)
recover_parser.add_argument("--version", type=int, default=0)
args = parser.parse_args()

secret: GFE
shares: Iterable[tuple[GFE, GFE]]

if args.subcommand == "split":
    secret = args.secret
    try:
        shares = shamir.split(secret, args.needed, args.shares, args.version)
    except ValueError as e:
        print(e.args[0], file=sys.stderr, flush=True)
        sys.exit(1)
    for x, y in shares:
        print(
            int(x),
            bip39.encode(bytes(y)),
            sep=": ",
            file=sys.stdout,
            flush=True,
        )
elif args.subcommand == "recover":
    shares = args.shares
    try:
        secret = shamir.recover(shares, args.version)
    except ValueError as e:
        print(e.args[0], file=sys.stderr, flush=True)
        sys.exit(1)
    print(
        bip39.encode(bytes(secret)),
        file=sys.stdout,
        flush=True,
    )
