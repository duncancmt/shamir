# Usage

```
$ ./main.py --help
usage: main.py [-h] {split,verify,recover} ...

positional arguments:
  {split,verify,recover}
    split               Split a BIP-0039 mnemonic into a sequence of shares that can be used to recover the original mnemonic
    verify              Verify that a BIP-0039 mnemonic share belongs to a secret using the public metadata
    recover             Given BIP-0039 mnemonic shares, recover the original mnemonic they were split from

optional arguments:
  -h, --help            show this help message and exit
```

## Split

```
$ ./main.py split --help
usage: main.py split [-h] --shares SHARES --needed NEEDED [--file FILE] [--salt SALT] secret [secret ...]

positional arguments:
  secret           BIP-0039 mnemonic

optional arguments:
  -h, --help       show this help message and exit
  --shares SHARES  Number of shares to calculate and print
  --needed NEEDED  Number of shares required to recover the secret
  --file FILE      Write public verification metadata here
  --salt SALT      Salt to distinguish multiple splits of the same secret
```

### Correct usage

```
$ ./main.py split 'test test test test test test test test test test test junk' --needed 3 --shares 5
barely embody glimpse above position that inch detail believe there nothing almost
inquiry nothing tip bulk faculty town hedgehog hat business twin job already
right abuse funny scissors chaos tower shrug medal stage stand course juice
erosion stumble reduce penalty dust emotion audit insect aisle online dutch rival
like doctor anger laugh crisp emerge people nothing soldier pink artwork shell
{"v": [[90, 228, 230, 87, 100, 207, 222, 192, 127, 57, 219, 41, 53, 224, 93, 95, 9, 180, 133, 221, 233, 5, 46, 175, 124, 140, 222, 36, 112, 176, 121, 89], [222, 53, 106, 235, 229, 109, 171, 208, 203, 27, 66, 73, 16, 120, 114, 121, 229, 63, 126, 98, 35, 122, 100, 76, 122, 94, 78, 218, 165, 26, 234, 205], [58, 138, 225, 32, 148, 108, 248, 23, 135, 54, 46, 189, 92, 40, 198, 117, 250, 177, 70, 198, 239, 9, 60, 93, 75, 79, 204, 25, 41, 57, 98, 203], [143, 221, 79, 95, 157, 12, 3, 178, 150, 81, 53, 72, 51, 61, 146, 150, 121, 137, 13, 233, 132, 67, 132, 50, 203, 13, 232, 236, 212, 219, 35, 98], [42, 35, 97, 59, 129, 77, 93, 214, 224, 22, 29, 235, 155, 108, 224, 179, 190, 174, 6, 211, 23, 43, 30, 211, 53, 84, 22, 42, 115, 26, 226, 250]], "c": [[214, 241, 120, 169, 235, 208, 82, 52, 62, 2, 217, 249, 109, 164, 170, 149], [18, 87, 194, 89, 183, 10, 198, 246, 93, 55, 156, 195, 119, 139, 143, 52], [234, 197, 13, 127, 13, 50, 115, 102, 255, 254, 31, 98, 72, 131, 161, 45]], "s": [2]}
```

Distribute the mnemonics _privately_ to the shareholders. The JSON blob at the
end should be published somewhere conspicuous so that the shareholders can
publicly agree on its value and verify their shares against it. It is also
needed during the secret recovery step, so it should be retained durably
somewhere. Publishing it to IPFS and storing it durably in Filecoin seems like a
good solution.

### Abbreviated

```
$ ./main.py split 'tes tes tes tes tes tes tes tes tes tes tes junk' --needed 3 --shares 5 --file=meta.json
barely embody glimpse above position that inch detail believe there nothing almost
inquiry nothing tip bulk faculty town hedgehog hat business twin job already
right abuse funny scissors chaos tower shrug medal stage stand course juice
erosion stumble reduce penalty dust emotion audit insect aisle online dutch rival
like doctor anger laugh crisp emerge people nothing soldier pink artwork shell
```

### Too much abbreviation

```
$ ./main.py split 'tes tes tes tes tes tes tes tes tes tes tes jun' --needed 3 --shares 5
usage: main.py split [-h] --shares SHARES --needed NEEDED [--file FILE] [--salt SALT] secret [secret ...]
main.py split: error: argument secret: invalid mnemonic value: 'tes tes tes tes tes tes tes tes tes tes tes jun'
```

### Bad checksum

```
$ ./main.py split 'test test test test test test test test test test test abandon' --needed 3 --shares 5
usage: main.py split [-h] --shares SHARES --needed NEEDED [--file FILE] [--salt SALT] secret [secret ...]
main.py split: error: argument secret: invalid mnemonic value: 'test test test test test test test test test test test abandon'
```

## Verify

```
$ ./main.py verify --help
usage: main.py verify [-h] --file FILE share

positional arguments:
  share        Mnemonic share produced from the original using `split`

optional arguments:
  -h, --help   show this help message and exit
  --file FILE  File containing public share metadata
```

```
$ ./main.py verify 'erosion stumble reduce penalty dust emotion audit insect aisle online dutch rival' --file=meta.json ; echo $?
0
```

```
$ ./main.py verify 'test test test test test test test test test test test junk' --file=meta.json ; echo $?
1
```

## Recover

```
$ ./main.py recover --help
usage: main.py recover [-h] --file FILE shares [shares ...]

positional arguments:
  shares       Mnemonics produced from the original using `split`

optional arguments:
  -h, --help   show this help message and exit
  --file FILE  File containing public share metadata
```

### Correct usage

Note the mixed abbreviation and in some cases extreme abbreviation of some
mnemonic words. As long as it's unambiguous, the program will accept it. Order
also doesn't matter.

```
$ ./main.py recover --file=meta.json 'eros stumble red pena dust emo audit insect ais onli dutch rival' \
> 'bare embo glimpse abov posi that inch deta believe there noth alm' \
> 'inq noth tip bulk faculty town hed hat busi twin job already'
test test test test test test test test test test test junk
```

### Not enough shares

```
$ ./main.py recover --file=meta.json 'eros stumble red pena dust emo audit insect ais onli dutch rival' \
> 'bare embo glimpse abov posi that inch deta believe there noth alm'
Too few valid shares. Invalid shares:
```

### Wrong share

```
$ ./main.py recover --file=meta.json 'eros stumble red pena dust emo audit insect ais onli dutch rival' \
> 'bare embo glimpse abov posi that inch deta believe there noth alm' \
> 'test test test test test test test test test test test junk'
Too few valid shares. Invalid shares:
        test test test test test test test test test test test junk
```

### Bad checksum

```
$ ./main.py recover --file=meta.json 'eros stumble red pena dust emo audit insect ais onli dutch rival' \
> 'bare embo glimpse abov posi that inch deta believe there noth alm' \
> 'inq noth tip bulk faculty town hed hat busi twin job abandon'
usage: main.py recover [-h] --file FILE shares [shares ...]
main.py recover: error: argument shares: invalid mnemonic value: 'inq noth tip bulk faculty town hed hat busi twin job abandon'
```
