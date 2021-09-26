```
$ ./main.py --help
usage: main.py [-h] [--nonce NONCE] {split,recover} ...

positional arguments:
  {split,recover}
    split            Split a BIP-0039 mnemonic into a sequence of shares that can be used to recover the original mnemonic
    recover          Given numbered BIP-0039 mnemonic shares, recover the original mnemonic they were split from

optional arguments:
  -h, --help         show this help message and exit
  --nonce NONCE      Nonce to distinguish multiple splits of the same secret
```

```
$ ./main.py split --help
usage: main.py split [-h] --shares SHARES --needed NEEDED secret

positional arguments:
  secret           BIP-0039 mnemonic

optional arguments:
  -h, --help       show this help message and exit
  --shares SHARES  Number of shares to calculate and print
  --needed NEEDED  Number of shares required to recover the secret
```

```
$ ./main.py split 'test test test test test test test test test test test junk' --needed 3 --shares 5
1: early dad before body scissors couch private goddess riot boost season quit
2: drop appear actress seat permit off cabin result chronic task purse column
3: supply token siren ahead sad involve hidden arrest evidence blouse rebel wide
4: document head evidence popular calm cram wine industry search two behind bounce
5: suspect lock major hungry dignity tail monkey silk police collect ankle snack
```

```
$ ./main.py recover --help
usage: main.py recover [-h] NUMBER,MNEMONIC [NUMBER,MNEMONIC ...]

positional arguments:
  NUMBER,MNEMONIC  Numbered mnemonics produced from the original using `split`

optional arguments:
  -h, --help       show this help message and exit
```

```
$ ./main.py recover 5,'suspect lock maj hung dign tai monkey silk poli coll ank snac' 2,'dro appe actress seat perm off cabi resu chr task purse colu' 3,'supply tok sir ahead sad involve hid arre evid blou rebe wide'
test test test test test test test test test test test junk
```
