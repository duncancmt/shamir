# Usage

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

## Split

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

### Correct usage

```
$ ./main.py split 'test test test test test test test test test test test junk' --needed 3 --shares 5
1: early dad before body scissors couch private goddess riot boost season quit
2: drop appear actress seat permit off cabin result chronic task purse column
3: supply token siren ahead sad involve hidden arrest evidence blouse rebel wide
4: document head evidence popular calm cram wine industry search two behind bounce
5: suspect lock major hungry dignity tail monkey silk police collect ankle snack
```

### Bad checksum

```
$ ./main.py split 'test test test test test test test test test test test abandon' --needed 3 --shares 5
usage: main.py split [-h] --shares SHARES --needed NEEDED secret
main.py split: error: argument secret: invalid mnemonic value: 'test test test test test test test test test test test abandon'
```

## Recover

```
$ ./main.py recover --help
usage: main.py recover [-h] NUMBER,MNEMONIC [NUMBER,MNEMONIC ...]

positional arguments:
  NUMBER,MNEMONIC  Numbered mnemonics produced from the original using `split`

optional arguments:
  -h, --help       show this help message and exit
```

### Correct usage

Note the mixed abbreviation and in some cases extreme abbreviation of some
mnemonic words. As long as it's unambiguous, the program will accept it.

```
$ ./main.py recover 5,'suspect lock maj hung dign tai monkey silk poli coll ank snac' \
> 2,'dro appe actress seat perm off cabi resu chr task purse colu' \
> 3,'supply tok sir ahead sad involve hid arre evid blou rebe wide'
test test test test test test test test test test test junk
```

### Not enough shares

```
$ ./main.py recover 5,'suspect lock major hungry dignity tail monkey silk police collect ankle snack' \
> 2,'drop appear actress seat permit off cabin result chronic task purse column'
Invalid/malicious share
```

### Wrong share

```
$ ./main.py recover 5,'suspect lock major hungry dignity tail monkey silk police collect ankle snack' \
> 2,'drop appear actress seat permit off cabin result chronic task purse column' \
> 3,'test test test test test test test test test test test junk'
Invalid/malicious share
```

### Not enumerating shares

```
$ ./main.py recover 'suspect lock major hungry dignity tail monkey silk police collect ankle snack' \
> 'drop appear actress seat permit off cabin result chronic task purse column' \
> 'supply token siren ahead sad involve hidden arrest evidence blouse rebel wide'
usage: main.py recover [-h] NUMBER,MNEMONIC [NUMBER,MNEMONIC ...]
main.py recover: error: argument NUMBER,MNEMONIC: invalid int_and_mnemonic value: 'suspect lock major hungry dignity tail monkey silk police collect ankle snack'
```

### Bad checksum

```
$ ./main.py recover 5,'suspect lock maj hung dign tai monkey silk poli coll ank aban' \
> 2,'dro appe actress seat perm off cabi resu chr task purse colu' \
> 3,'supply tok sir ahead sad involve hid arre evid blou rebe wide'
main.py recover: error: argument NUMBER,MNEMONIC: invalid int_and_mnemonic value: '5,suspect lock maj hung dign tai monkey silk poli coll ank aban'
```
