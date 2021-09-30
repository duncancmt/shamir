# Usage

```
$ ./main.py --help
usage: main.py [-h] [--salt SALT] {split,verify,recover} ...

positional arguments:
  {split,verify,recover}
    split               Split a BIP-0039 mnemonic into a sequence of shares that can be used to recover the original mnemonic
    verify              Verify that a BIP-0039 mnemonic share belongs to a secret using the public metadata
    recover             Given BIP-0039 mnemonic shares, recover the original mnemonic they were split from

optional arguments:
  -h, --help            show this help message and exit
  --salt SALT           Salt to distinguish multiple splits of the same secret
```

## Split

```
$ ./main.py split --help
usage: main.py split [-h] --shares SHARES --needed NEEDED [--file FILE] secret

positional arguments:
  secret           BIP-0039 mnemonic

optional arguments:
  -h, --help       show this help message and exit
  --shares SHARES  Number of shares to calculate and print
  --needed NEEDED  Number of shares required to recover the secret
  --file FILE      Write public verification metadata here
```

### Correct usage

```
$ ./main.py split 'test test test test test test test test test test test junk' --needed 3 --shares 5
welcome protect burst shine vote dose enact hundred atom worth scheme zebra
atom text certain wife three virus level endorse bus drill brave normal
chuckle prosper top they slice hedgehog bind west song gauge afford ball
aspect egg sing stadium arch steel pride convince story logic royal divide
close curious amount sister cannon enroll detect palace also peanut phone return
{"v": [[22, 83, 183, 179, 77, 22, 204, 1, 216, 133, 143, 215, 183, 110, 125, 18], [83, 234, 0, 89, 69, 143, 241, 151, 1, 113, 178, 158, 82, 45, 98, 28], [91, 146, 32, 253, 29, 161, 247, 202, 141, 99, 175, 174, 122, 214, 138, 62], [5, 131, 205, 204, 24, 192, 98, 203, 113, 65, 231, 132, 14, 192, 18, 206], [13, 82, 195, 20, 102, 197, 230, 122, 105, 150, 240, 33, 35, 62, 241, 27]], "c": [[156, 190, 176, 202, 140, 215, 111, 131, 61, 35, 88, 231, 101, 84, 98, 216], [15, 176, 167, 166, 218, 100, 117, 154, 144, 111, 191, 30, 197, 32, 255, 20], [164, 188, 73, 65, 223, 36, 25, 213, 16, 60, 56, 70, 44, 141, 83, 135]]}
```

### Abbreviated

```
$ ./main.py split 'tes tes tes tes tes tes tes tes tes tes tes junk' --needed 3 --shares 5 --file=meta.json
welcome protect burst shine vote dose enact hundred atom worth scheme zebra
atom text certain wife three virus level endorse bus drill brave normal
chuckle prosper top they slice hedgehog bind west song gauge afford ball
aspect egg sing stadium arch steel pride convince story logic royal divide
close curious amount sister cannon enroll detect palace also peanut phone return
```

### Too much abbreviation

```
$ ./main.py split 'tes tes tes tes tes tes tes tes tes tes tes jun' --needed 3 --shares 5
usage: main.py split [-h] --shares SHARES --needed NEEDED [--file FILE] secret
main.py split: error: argument secret: invalid mnemonic value: 'tes tes tes tes tes tes tes tes tes tes tes jun'
```

### Bad checksum

```
$ ./main.py split 'test test test test test test test test test test test abandon' --needed 3 --shares 5
usage: main.py split [-h] --shares SHARES --needed NEEDED [--file FILE] secret
main.py split: error: argument secret: invalid mnemonic value: 'test test test test test test test test test test test abandon'
```

## Verify

```
$ ./main.py verify 'welcome protect burst shine vote dose enact hundred atom worth scheme zebra' --file=meta.json ; echo $?
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
$ ./main.py recover --file=meta.json 'wel prot burs shin vot dos enac hundred atom worth scheme zebr' \
> 'asp egg sing stadium arch stee prid convince stor log roya divi' \
> 'chuckle pros top they slic hed bind wes song gauge affo ball'
test test test test test test test test test test test junk
```

### Not enough shares

```
$ ./main.py recover --file=meta.json 'wel prot burs shin vot dos enac hundred atom worth scheme zebr' \
> 'asp egg sing stadium arch stee prid convince stor log roya divi'
Too few valid shares. Invalid shares:
```

### Wrong share

```
$ ./main.py recover --file=meta.json 'wel prot burs shin vot dos enac hundred atom worth scheme zebr' \
> 'asp egg sing stadium arch stee prid convince stor log roya divi' \
> 'test test test test test test test test test test test junk'
Too few valid shares. Invalid shares:
        test test test test test test test test test test test junk
```

### Bad checksum

```
$ ./main.py recover --file=meta.json 'wel prot burs shin vot dos enac hundred atom worth scheme zebr' \
> 'asp egg sing stadium arch stee prid convince stor log roya divi' \
> 'chuckle pros top they slic hed bind wes song gauge affo abandon'
usage: main.py recover [-h] --file FILE shares [shares ...]
main.py recover: error: argument shares: invalid mnemonic value: 'chuckle pros top they slic hed bind wes song gauge affo abandon'
```
