import gf

a = 0b110001
b = 0b110

print("alleged:", bin(0b10100110))
print("actual:", bin(int(gf.BinaryPolynomial(a) * gf.BinaryPolynomial(b))))

##

context = gf.getcontext()
context.modulus = 0b100011011

###

m = 0b100011011
a = 0b11100010110001

q, r = divmod(gf.BinaryPolynomial(a), gf.BinaryPolynomial(m))
print("alleged:", bin(0b111010), bin(0b10001111))
print("actual:", bin(q._value), bin(r._value))

###

a = 0b110001
b = 0b110

print("alleged:", bin(0b10100110))
print("actual:", bin(int((gf.GFElement(a) * gf.GFElement(b))._value)))

###

a = 0b1010011

print("alleged:", bin(0b11001010))
actual = ~gf.GFElement(a)
print("actual:", bin(int((actual)._value)))

##

a = 0b110011

print("alleged:", bin(0b1101100))
actual = ~gf.GFElement(a)
print("actual:", bin(int((actual)._value)))


###

inverses = set()
for i in range(1, 256):
    i_inverse = ~gf.GFElement(i)
    inverses.add(int(i_inverse))
    assert i * i_inverse == 1
assert len(inverses) == 255
assert inverses == set(range(1, 256))

print("exhaustive test of AES modulus passed")
