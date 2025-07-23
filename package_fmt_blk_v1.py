import struct,datetime,sys,os

def u8(file):
    return struct.unpack("B", file.read(1))[0]
def u16(file):
    return struct.unpack("<H", file.read(2))[0]
def u32(file):
    return struct.unpack("<I", file.read(4))[0]
def rR(f,o,l):#Read n Return, Takes file,offset,size returns data
    c = f.tell()
    f.seek(o)
    d = f.read(l)
    f.seek(c)
    return d

class OLK(object):
    class ENT(object):
        def __init__(self):
            self.addr = 0
            self.size = 0
            self.data = bytearray()
        def read(self,f):
            self.addr = u32(f)
            self.size = u32(f)
            u32(f)
            u32(f)
    def __init__(self):
        self.files = []
        self.magic = bytearray('blnk','utf-8')
        self.info = self.ENT()
    def read(self,f):
        count = u32(f)
        self.magic = f.read(4)
        f.seek(0x10)
        for a in range(count):
            ent = self.ENT()
            self.files.append(ent)
            ent.read(f)
        startof = f.tell()
        for _a,e in enumerate(self.files):
            f.seek(startof + e.addr)
            fil = open(str(_a) + ".bin",'wb')
            fout = f.read(e.size)
            fil.write(fout)
            fil.close()

olk_file = open(sys.argv[1], "rb")
olk_in = OLK()
olk_in.read(olk_file)
olk_file.close()