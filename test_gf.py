import gf

a = 0b110001
b = 0b110

print("alleged:", bin(0b10100110))
print("actual:", bin(int(gf.BinaryPolynomial(a) * gf.BinaryPolynomial(b))))

##

context = gf.getcontext()
context.bit_length = 8
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
print("actual:", bin(int((gf.Element(a) * gf.Element(b))._value)))

###

a = 0b1010011
#a = 0b01010011

#print("alleged:", bin(0b1101100))
print("alleged:", bin(0b11001010))
actual = ~gf.Element(a)
print("actual:", bin(int((actual)._value)))
print(bin(int((actual * a)._value)))
