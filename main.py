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


def split(args: Any) -> None:
    secret: GFE = args.secret
    k: int = args.needed
    n: int = args.shares
    salt: int = args.salt
    try:
        shares, v, c = shamir.split(secret, k, n, salt)
    except ValueError as e:
        print(e.args[0], file=sys.stderr, flush=True)
        sys.exit(1)
    for share in shares:
        print(
            to_mnemonic(share),
            file=sys.stdout,
            flush=True,
        )
    save_metadata(args, v, c)


def get_metadata(args: Any) -> tuple[list[GFE], list[GFE]]:
    metadata = json.load(args.file)
    modulus = gf.get_modulus(len(metadata["v"][0]) * 8)
    v = [
        gf.ModularBinaryPolynomial(bytes(v_i), modulus)
        for v_i in metadata["v"]
    ]
    c = [
        gf.ModularBinaryPolynomial(bytes(c_i), modulus)
        for c_i in metadata["c"]
    ]
    return v, c


def save_metadata(args: Any, v: list[GFE], c: list[GFE]) -> None:
    json.dump(
        {
            "v": [list(bytes(v_i)) for v_i in v],
            "c": [list(bytes(c_i)) for c_i in c],
        },
        args.file,
    )


def add_metadata_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--file",
        type=argparse.FileType("r"),
        help="File containing public share metadata",
    )


def verify(args: Any) -> None:
    share: GFE = args.share
    v, c = get_metadata(args)
    sys.exit(not shamir.verify(share, v, c))


def recover(args: Any) -> None:
    shares: list[GFE] = args.shares
    v, c = get_metadata(args)
    try:
        secret = shamir.recover(shares, v, c)
    except ValueError as e:
        print(e.args[0], file=sys.stderr, flush=True)
        for share in e.args[1]:
            print("\t" + to_mnemonic(share), file=sys.stderr, flush=True)
        sys.exit(1)
    print(
        to_mnemonic(secret),
        file=sys.stdout,
        flush=True,
    )


# fmt: off
parser = argparse.ArgumentParser()
parser.add_argument(
    "--salt",
    type=int,
    default=0,
    help="Salt to distinguish multiple splits of the same secret",
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
split_parser.add_argument(
    "--file",
    type=argparse.FileType("w"),
    default=sys.stdout,
    help="Write public verification metadata here",
)
split_parser.set_defaults(func=split)

verify_parser = subparsers.add_parser(
    "verify",
    help="Verify that a BIP-0039 mnemonic share belongs to a secret using the public metadata",
)
verify_parser.add_argument(
    "share",
    type=mnemonic,
    help="Mnemonic share produced from the original using `split`",
)
add_metadata_args(verify_parser)
verify_parser.set_defaults(func=verify)

recover_parser = subparsers.add_parser(
    "recover",
    help="Given BIP-0039 mnemonic shares, recover the original mnemonic they were split from",
)
recover_parser.add_argument(
    "shares",
    nargs="+",
    type=mnemonic,
    help="Mnemonics produced from the original using `split`",
)
add_metadata_args(recover_parser)
recover_parser.set_defaults(func=recover)

args = parser.parse_args()
args.func(args)
