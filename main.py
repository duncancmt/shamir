#!/usr/bin/env python3

import argparse
import json
import sys
from collections.abc import Iterable, Sequence
from typing import Any, Optional, Type, Union

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


def save_metadata(
    args: Any,
    v: Iterable[bytes],
    c: shamir.FiniteFieldPolynomial,
    s: Iterable[int],
) -> None:
    json.dump(
        {
            "v": [list(v_i) for v_i in reversed(v)],
            "c": [list(bytes(c_i)) for c_i in c],
            "s": list(s),
        },
        args.file,
    )


def split(args: Any) -> None:
    secret: Union[tuple[GFE], tuple[GFE, GFE]] = tuple(args.secret)  # type: ignore
    k: int = args.needed
    n: int = args.shares
    salt: int = args.salt
    try:
        shares, v, c, s = shamir.split(secret, k, n, salt)
    except ValueError as e:
        print(e.args[0], file=sys.stderr, flush=True)
        sys.exit(1)
    for share in shares:
        print(
            to_mnemonic(share),
            file=sys.stdout,
            flush=True,
        )
    save_metadata(args, v, c, s)


def get_metadata(
    args: Any,
) -> tuple[list[bytes], shamir.FiniteFieldPolynomial, list[int]]:
    metadata = json.load(args.file)
    v = [bytes(v_i) for v_i in reversed(metadata["v"])]
    modulus = gf.get_modulus(len(metadata["c"][0]) * 8)
    c = shamir.FiniteFieldPolynomial(
        gf.ModularBinaryPolynomial(bytes(c_i), modulus)
        for c_i in metadata["c"]
    )
    s = list(metadata["s"])
    return v, c, s


def add_metadata_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--file",
        type=argparse.FileType("r"),
        help="File containing public share metadata",
    )


def verify(args: Any) -> None:
    share: GFE = args.share
    v, c, _ = get_metadata(args)
    try:
        shamir.verify(share, v, c)
    except ValueError:
        sys.exit(1)
    else:
        sys.exit(0)


def recover(args: Any) -> None:
    shares: list[GFE] = args.shares
    v, c, s = get_metadata(args)
    try:
        secret = shamir.recover(shares, v, c, s)
    except ValueError as e:
        print(e.args[0], file=sys.stderr, flush=True)
        for share in e.args[1]:
            print("\t" + to_mnemonic(share), file=sys.stderr, flush=True)
        sys.exit(1)
    for i in secret:
        print(
            to_mnemonic(i),
            file=sys.stdout,
            flush=True,
        )


def required_length(nmin: int, nmax: int) -> Type[argparse.Action]:
    class RequiredLength(argparse.Action):
        def __call__(
            self,
            parser: argparse.ArgumentParser,
            args: argparse.Namespace,
            values: Union[str, Sequence[Any], None],
            option_string: Optional[str] = None,
        ) -> None:
            if values is None:
                parser.error(f'argument "{self.dest}" is required')
            if isinstance(values, str):
                values = [values]
            if not nmin <= len(values) <= nmax:
                parser.error(
                    f'argument "{self.dest}" requires between {nmin} and {nmax} arguments'
                )
            setattr(args, self.dest, values)

    return RequiredLength


# fmt: off
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(required=True)

split_parser = subparsers.add_parser(
    "split",
    help="Split a BIP-0039 mnemonic into a sequence of shares that can be used to recover the original mnemonic",
)
split_parser.add_argument(
    "secret",
    nargs="+",
    type=mnemonic,
    action=required_length(1, 2),
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
split_parser.add_argument(
    "--salt",
    type=int,
    default=0,
    help="Salt to distinguish multiple splits of the same secret",
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
