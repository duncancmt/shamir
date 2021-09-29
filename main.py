#!/usr/bin/env python3

import argparse
import json
import sys
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


def to_mnemonic(x: GFE) -> str:
    return bip39.encode(bytes(x))


def int_and_mnemonic(arg: str) -> tuple[GFE, GFE]:
    x, y = arg.split(",")
    y = mnemonic(y)
    x = y.coerce(int(x))
    return x, y


def split(args: Any) -> None:
    secret: GFE = args.secret
    k: int = args.needed
    n: int = args.shares
    try:
        shares, v, c = shamir.split(secret, k, n)
    except ValueError as e:
        print(e.args[0], file=sys.stderr, flush=True)
        sys.exit(1)
    for x, y in zip(range(1, n + 1), shares):
        print(
            x,
            bip39.encode(bytes(y)),
            sep=",",
            file=sys.stdout,
            flush=True,
        )
    json.dump(
        {
            "v": [to_mnemonic(v_i) for v_i in v],
            "c": [to_mnemonic(c_i) for c_i in c],
        },
        sys.stdout,
    )
    sys.stdout.write("\n")


def recover(args: Any) -> None:
    shares: list[tuple[GFE, GFE]] = args.shares
    metadata = json.load(args.file)
    v = [mnemonic(v_i) for v_i in metadata["v"]]
    c = [mnemonic(c_i) for c_i in metadata["c"]]
    try:
        secret = shamir.recover(shares, v, c)
    except ValueError as e:
        print(e.args[0], file=sys.stderr, flush=True)
        sys.exit(1)
    print(
        bip39.encode(bytes(secret)),
        file=sys.stdout,
        flush=True,
    )


# fmt: off
parser = argparse.ArgumentParser()
parser.add_argument(
    "--nonce",
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
    required=True,
    help="Number of shares to calculate and print"
)
split_parser.add_argument(
    "--needed",
    type=int,
    required=True,
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
public_group = recover_parser.add_mutually_exclusive_group(required=True)
public_group.add_argument(
    "--file",
    type=argparse.FileType("r"),
    default=sys.stdin,
    help="File containing public share metadata",
)
recover_parser.set_defaults(func=recover)

args = parser.parse_args()
args.func(args)
