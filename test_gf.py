import gf

context = gf.getcontext()
context.bit_length = 8
context.modulus = 0b11011

###

m = 0b100011011
a = 0b11100010110001

q, r = divmod(gf.Element(a), gf.Element(m))
print("alleged:", bin(0b111010), bin(0b10001111))
print("actual:", bin(q._value), bin(r._value))

###

a = 0b110001
b = 0b110

print("alleged:", bin(0b10100110))
print("actual:", bin((gf.Element(a) * gf.Element(b))._value))

###

#a = 0b110011
a = 0b01010011

#print("alleged:", bin(0b1101100))
print("alleged:", bin(0b11001010))
print("actual:", bin((~gf.Element(a))._value))
