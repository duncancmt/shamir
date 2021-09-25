import os.path
import hashlib
from collections.abc import Iterable
import operator
import functools
import bisect
import unicodedata

wordlist: list[str] = []
with open(
    os.path.join(os.path.dirname(__file__), "bip-0039.txt"),
    "r",
    encoding="utf-8",
) as f:
    for l in f:
        wordlist.append(unicodedata.normalize("NFKD", l).strip())
del f
del l
assert len(wordlist) == 2048
assert wordlist == sorted(wordlist)


def checksum(entropy: bytes) -> int:
    assert len(entropy) in (16, 20, 24, 28, 32)
    checksum_bits = len(entropy) // 4
    checksum_bytes = (checksum_bits + 7) // 8
    h = hashlib.sha256()
    h.update(entropy)
    result = int.from_bytes(h.digest()[:checksum_bytes], "big")
    result >>= checksum_bytes * 8 - checksum_bits
    return result


def encode(entropy: bytes) -> tuple[str, ...]:
    checksum_bits = len(entropy) // 4
    checksummed = (int.from_bytes(entropy, "big") << checksum_bits) | checksum(
        entropy
    )
    result: list[str] = []
    for i in range(len(entropy) * 3 // 4 - 1, -1, -1):
        word_index = (checksummed >> (i * 11)) & 2047
        result.append(wordlist[word_index])
    return tuple(result)


def decode(words: Iterable[str]) -> bytes:
    raw: list[int] = []
    for word in words:
        raw.append(
            bisect.bisect_left(wordlist, unicodedata.normalize("NFKD", word))
        )
    assert len(raw) in (12, 15, 18, 21, 24)
    checksum_bits = len(raw) // 3
    entropy_bits = len(raw) * 11 - checksum_bits
    raw = functools.reduce(
        operator.or_,
        (x << (i * 11) for i, x in zip(range(len(raw) - 1, -1, -1), raw)),
    )
    entropy = (raw >> checksum_bits).to_bytes(entropy_bits // 8, "big")
    assert raw & ((1 << checksum_bits) - 1) == checksum(entropy)
    return entropy


__all__ = ["encode", "decode"]
