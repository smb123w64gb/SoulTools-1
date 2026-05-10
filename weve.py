import sys

r0 = open(sys.argv[1],'rb')
r1 = open(sys.argv[2],'rb')
w0 = open(sys.argv[3],'wb')

r0.seek(0,2)
end = r0.tell()
r0.seek(0)

for x in range(end):
    w0.write(r0.read(1))
    w0.write(r1.read(1))
w0.close()
r0.close()
r1.close()