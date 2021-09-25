import argparse
import sys
from collections.abc import Iterable
from typing import Any

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


def split(args: Any) -> None:
    secret: GFE = args.secret
    k: int = args.needed
    n: int = args.shares
    version: int = args.version
    try:
        shares = shamir.split(secret, k, n, version)
    except ValueError as e:
        print(e.args[0], file=sys.stderr, flush=True)
        exit(1)
    for x, y in shares:
        print(
            int(x),
            bip39.encode(bytes(y)),
            sep=": ",
            file=sys.stdout,
            flush=True,
        )


def recover(args: Any) -> None:
    shares: Iterable[tuple[GFE, GFE]] = args.shares
    version: int = args.version
    try:
        secret = shamir.recover(shares, version)
    except ValueError as e:
        print(e.args[0], file=sys.stderr, flush=True)
        exit(1)
    print(
        bip39.encode(bytes(secret)),
        file=sys.stdout,
        flush=True,
    )


# fmt: off
parser = argparse.ArgumentParser()
parser.add_argument(
    "--version",
    type=int,
    default=0,
    help="Nonce to distinguish multiple splits of the same secret",
)
subparsers = parser.add_subparsers(required=True)

split_parser = subparsers.add_parser(
    "split",
    help="Split a BIP-0039 mnemonic into a sequence of shares that can be used to recover the original mnemonic",
)
split_parser.add_argument(
    "secret",
    type=mnemonic,
    help="BIP-0039 mnemonic"
)
split_parser.add_argument(
    "--shares",
    type=int,
    help="Number of shares to calculate and print"
)
split_parser.add_argument(
    "--needed",
    type=int,
    help="Number of shares required to recover the secret",
)
split_parser.set_defaults(func=split)

recover_parser = subparsers.add_parser(
    "recover",
    help="Given numbered BIP-0039 mnemonic shares, recover the original mnemonic they were split from",
)
recover_parser.add_argument(
    "shares",
    nargs="+",
    type=int_and_mnemonic,
    metavar="NUMBER,MNEMONIC",
    help="Numbered mnemonics produced from the original using `split`",
)
recover_parser.set_defaults(func=recover)

args = parser.parse_args()
args.func(args)
