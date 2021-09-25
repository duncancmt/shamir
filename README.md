```
$ ./main.py --help
usage: main.py [-h] [--version VERSION] {split,recover} ...

positional arguments:
  {split,recover}
    split            Split a BIP-0039 mnemonic into a sequence of shares that can be used to recover the original mnemonic
    recover          Given numbered BIP-0039 mnemonic shares, recover the original mnemonic they were split from

optional arguments:
  -h, --help         show this help message and exit
  --version VERSION  Nonce to distinguish multiple splits of the same secret
```


```
$ ./main.py split --help
usage: main.py split [-h] [--shares SHARES] [--needed NEEDED] secret

positional arguments:
  secret           BIP-0039 mnemonic

optional arguments:
  -h, --help       show this help message and exit
  --shares SHARES  Number of shares to calculate and print
  --needed NEEDED  Number of shares required to recover the secret
```

```
$ ./main.py recover --help
usage: main.py recover [-h] NUMBER,MNEMONIC [NUMBER,MNEMONIC ...]

positional arguments:
  NUMBER,MNEMONIC  Numbered mnemonics produced from the original using `split`

optional arguments:
  -h, --help       show this help message and exit
```