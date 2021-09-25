import bisect
import functools
import hashlib
import operator
import os.path
import unicodedata

wordlist: list[str] = []
with open(
    os.path.join(os.path.dirname(__file__), "bip-0039.txt"),
    "r",
    encoding="utf-8",
) as f:
    for l in f:
        assert unicodedata.is_normalized("NFKD", l)
        wordlist.append(l.strip())
del f
del l
assert len(wordlist) == 2048
assert wordlist == sorted(wordlist)


def checksum(entropy: bytes) -> int:
    checksum_bits = len(entropy) // 4
    checksum_bytes = (checksum_bits + 7) // 8
    h = hashlib.sha256()
    h.update(entropy)
    result = int.from_bytes(h.digest()[:checksum_bytes], "big")
    result >>= checksum_bytes * 8 - checksum_bits
    return result


def encode(entropy: bytes, sep: str = " ") -> str:
    if unicodedata.normalize("NFKD", sep) != " ":
        if len(sep) != 0:
            raise ValueError(f"Multi-character ({len(sep)}) separator '{sep}'")
        raise ValueError(
            f"Separator '{sep}' ({unicodedata.name(sep)}) does not normalize to space"
        )
    if len(entropy) not in (16, 20, 24, 28, 32):
        raise ValueError(f"Invalid entropy length {len(entropy)}")
    num_words = len(entropy) * 3 // 4
    checksum_bits = len(entropy) // 4
    entropy_int = int.from_bytes(entropy, "big")
    to_encode = (entropy_int << checksum_bits) | checksum(entropy)
    result: list[str] = []
    for i in range(num_words - 1, -1, -1):
        word_index = (to_encode >> (i * 11)) & 2047
        result.append(wordlist[word_index])
    return sep.join(result)


def decode(words: str) -> bytes:
    words = unicodedata.normalize("NFKD", words).split(" ")
    raw: list[int] = []
    for word in words:
        i = bisect.bisect_left(wordlist, word)
        if not wordlist[i].startswith(word):
            raise ValueError(f"Invalid mnemonic word '{word}'")

        if (
            wordlist[i] != word
            and i + 1 < len(wordlist)  # superfluous for the English wordlist
            and wordlist[i + 1].startswith(word)
        ):
            raise ValueError(f"Ambiguous mnemonic word '{word}'")
        raw.append(i)
    if len(raw) not in (12, 15, 18, 21, 24):
        raise ValueError(f"Invalid mnemonic length {len(raw)}")
    checksum_bits = len(raw) // 3
    entropy_bits = len(raw) * 11 - checksum_bits
    raw = functools.reduce(
        operator.or_,
        (x << i for i, x in zip(range((len(raw) - 1) * 11, -1, -11), raw)),
    )
    entropy = (raw >> checksum_bits).to_bytes(entropy_bits // 8, "big")
    mask = (1 << checksum_bits) - 1
    if raw & mask != checksum(entropy):
        raise ValueError("Bad checksum")
    return entropy


__all__ = ["encode", "decode"]
