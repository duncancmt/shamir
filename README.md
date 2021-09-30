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
illegal bullet bone shuffle parrot achieve resemble accident bundle depend world another
wild nice potato alone umbrella purse vacant height card effort cactus sell
few feel host bulk need ignore obvious reform today phrase acquire rate
idea history surge soul meadow armor just nothing tenant peasant song father
ten pulse broken struggle wagon stick balance else burst elder unfair capital
{"v": [[65, 209, 18, 109, 233, 218, 160, 191, 79, 88, 122, 73, 76, 158, 58, 48], [13, 90, 243, 220, 5, 138, 243, 123, 190, 74, 200, 120, 132, 230, 238, 77], [154, 143, 61, 185, 16, 178, 249, 69, 112, 81, 159, 167, 239, 244, 190, 134], [45, 147, 78, 199, 246, 214, 17, 174, 117, 139, 152, 146, 94, 48, 156, 44], [236, 196, 65, 188, 21, 113, 42, 218, 94, 125, 184, 35, 84, 53, 241, 131]], "c": [[74, 26, 185, 243, 234, 239, 58, 151, 6, 221, 22, 131, 148, 192, 93, 85], [26, 199, 252, 108, 232, 200, 89, 130, 33, 66, 227, 224, 192, 37, 188, 107], [27, 181, 166, 192, 53, 94, 105, 101, 160, 60, 66, 169, 77, 252, 125, 239]]}
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
illegal bullet bone shuffle parrot achieve resemble accident bundle depend world another
wild nice potato alone umbrella purse vacant height card effort cactus sell
few feel host bulk need ignore obvious reform today phrase acquire rate
idea history surge soul meadow armor just nothing tenant peasant song father
ten pulse broken struggle wagon stick balance else burst elder unfair capital
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
$ ./main.py verify 'illegal bullet bone shuffle parrot achieve resemble accident bundle depend world another' --file=meta.json ; echo $?
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
$ ./main.py recover --file=meta.json 'ille bull bone shu parrot ach rese acci bund depend worl ano' \
> 'idea his surge soul mead armo just noth tena peasant son fath' \
> 'few feel host bulk nee ign obvious refo toda phr acquire rate'
test test test test test test test test test test test junk
```

### Not enough shares

```
$ ./main.py recover --file=meta.json 'ille bull bone shu parrot ach rese acci bund depend worl ano' \
> 'idea his surge soul mead armo just noth tena peasant son fath'
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
$ ./main.py recover --file=meta.json 'ille bull bone shu parrot ach rese acci bund depend worl ano' \
> 'idea his surge soul mead armo just noth tena peasant son fath' \
> 'few feel host bulk nee ign obvious refo toda phr acquire abandon'
usage: main.py recover [-h] --file FILE shares [shares ...]
main.py recover: error: argument shares: invalid mnemonic value: 'few feel host bulk nee ign obvious refo toda phr acquire abandon'
```
