import zlib
import sys

f = open(sys.argv[1],'rb')
f.seek(0x20)
o = open(sys.argv[1]+"dec",'wb')

o.write(zlib.decompress(f.read()))
o.close()
f.close()