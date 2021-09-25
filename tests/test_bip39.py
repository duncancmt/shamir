import secrets
import unittest
import operator

import bip39


class TestBIP39(unittest.TestCase):
    def setUp(self) -> None:
        self.vectors = [
            (
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
            ),
            (
                b"\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f",
                "legal winner thank year wave sausage worth useful legal winner thank yellow",
            ),
            (
                b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80",
                "letter advice cage absurd amount doctor acoustic avoid letter advice cage above",
            ),
            (
                b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff",
                "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong",
            ),
            (
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon agent",
            ),
            (
                b"\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f",
                "legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal will",
            ),
            (
                b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80",
                "letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter always",
            ),
            (
                b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff",
                "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo when",
            ),
            (
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art",
            ),
            (
                b"\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f",
                "legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth title",
            ),
            (
                b"\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80",
                "letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic bless",
            ),
            (
                b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff",
                "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo vote",
            ),
            (
                b"\x9e\x88\x5d\x95\x2a\xd3\x62\xca\xeb\x4e\xfe\x34\xa8\xe9\x1b\xd2",
                "ozone drill grab fiber curtain grace pudding thank cruise elder eight picnic",
            ),
            (
                b"\x66\x10\xb2\x59\x67\xcd\xcc\xa9\xd5\x98\x75\xf5\xcb\x50\xb0\xea\x75\x43\x33\x11\x86\x9e\x93\x0b",
                "gravity machine north sort system female filter attitude volume fold club stay feature office ecology stable narrow fog",
            ),
            (
                b"\x68\xa7\x9e\xac\xa2\x32\x48\x73\xea\xcc\x50\xcb\x9c\x6e\xca\x8c\xc6\x8e\xa5\xd9\x36\xf9\x87\x87\xc6\x0c\x7e\xbc\x74\xe6\xce\x7c",
                "hamster diagram private dutch cause delay private meat slide toddler razor book happy fancy gospel tennis maple dilemma loan word shrug inflict delay length",
            ),
            (
                b"\xc0\xba\x5a\x8e\x91\x41\x11\x21\x0f\x2b\xd1\x31\xf3\xd5\xe0\x8d",
                "scheme spot photo card baby mountain device kick cradle pact join borrow",
            ),
            (
                b"\x6d\x9b\xe1\xee\x6e\xbd\x27\xa2\x58\x11\x5a\xad\x99\xb7\x31\x7b\x9c\x8d\x28\xb6\xd7\x64\x31\xc3",
                "horn tenant knee talent sponsor spell gate clip pulse soap slush warm silver nephew swap uncle crack brave",
            ),
            (
                b"\x9f\x6a\x28\x78\xb2\x52\x07\x99\xa4\x4e\xf1\x8b\xc7\xdf\x39\x4e\x70\x61\xa2\x24\xd2\xc3\x3c\xd0\x15\xb1\x57\xd7\x46\x86\x98\x63",
                "panda eyebrow bullet gorilla call smoke muffin taste mesh discover soft ostrich alcohol speed nation flash devote level hobby quick inner drive ghost inside",
            ),
            (
                b"\x23\xdb\x81\x60\xa3\x1d\x3e\x0d\xca\x36\x88\xed\x94\x1a\xdb\xf3",
                "cat swing flag economy stadium alone churn speed unique patch report train",
            ),
            (
                b"\x81\x97\xa4\xa4\x7f\x04\x25\xfa\xea\xa6\x9d\xee\xbc\x05\xca\x29\xc0\xa5\xb5\xcc\x76\xce\xac\xc0",
                "light rule cinnamon wrap drastic word pride squirrel upgrade then income fatal apart sustain crack supply proud access",
            ),
            (
                b"\x06\x6d\xca\x1a\x2b\xb7\xe8\xa1\xdb\x28\x32\x14\x8c\xe9\x93\x3e\xea\x0f\x3a\xc9\x54\x8d\x79\x31\x12\xd9\xa9\x5c\x94\x07\xef\xad",
                "all hour make first leader extend hole alien behind guard gospel lava path output census museum junior mass reopen famous sing advance salt reform",
            ),
            (
                b"\xf3\x0f\x8c\x1d\xa6\x65\x47\x8f\x49\xb0\x01\xd9\x4c\x5f\xc4\x52",
                "vessel ladder alter error federal sibling chat ability sun glass valve picture",
            ),
            (
                b"\xc1\x0e\xc2\x0d\xc3\xcd\x9f\x65\x2c\x7f\xac\x2f\x12\x30\xf7\xa3\xc8\x28\x38\x9a\x14\x39\x2f\x05",
                "scissors invite lock maple supreme raw rapid void congress muscle digital elegant little brisk hair mango congress clump",
            ),
            (
                b"\xf5\x85\xc1\x1a\xec\x52\x0d\xb5\x7d\xd3\x53\xc6\x95\x54\xb2\x1a\x89\xb2\x0f\xb0\x65\x09\x66\xfa\x0a\x9d\x6f\x74\xfd\x98\x9d\x8f",
                "void come effort suffer camp survey warrior heavy shoot primary clutch crush open amazing screen patrol group space point ten exist slush involve unfold",
            ),
        ]

    def test_vectors(self) -> None:
        for i, (entropy, mnemonic) in enumerate(self.vectors):
            with self.subTest(i=i, entropy=entropy, mnemonic=mnemonic):
                self.assertEqual(" ".join(bip39.encode(entropy)), mnemonic)
                self.assertEqual(bip39.decode(mnemonic), entropy)

    def test_random(self) -> None:
        for l in (16, 20, 24, 28, 32):
            for i in range(10000):
                with self.subTest(l=l, i=i):
                    entropy = secrets.randbits(l * 8).to_bytes(l, "big")
                    mnemonic = bip39.encode(entropy)
                    mnemonic = map("".join, map(operator.itemgetter(slice(4)), mnemonic))
                    mnemonic = " ".join(mnemonic)
                    self.assertEqual(bip39.decode(mnemonic), entropy)
