import struct

class FRead(object): #Generic file reader
    def __init__(self,f,big_endian=False):
        self.endian='<'
        if(big_endian):
            self.endian ='>'
        self.file = f
    def swapEndian(self):
        if(self.endian == '>'):
            self.endian = '<'
        else:
            self.endian = '>'
    def u32(self):
        return struct.unpack(self.endian+'I', self.file.read(4))[0]
    def u16(self):
        return struct.unpack(self.endian+'H', self.file.read(2))[0]
    def u8(self):
        return struct.unpack(self.endian+'B', self.file.read(1))[0]
    def u8_4(self):
        return struct.unpack(self.endian+'BBBB', self.file.read(4))[0:4]
    def s32(self):
        return struct.unpack(self.endian+'i', self.file.read(4))[0]
    def s16(self):
        return struct.unpack(self.endian+'h', self.file.read(2))[0]
    def s8(self):
        return struct.unpack(self.endian+'b', self.file.read(1))[0]
    def f16(self):
        v = struct.unpack("<H", file.read(2))[0] << 16
        vv = struct.unpack("<f", v.to_bytes(4, byteorder='little'))[0]
        return vv
    def f16_2(self):
        val = [self.f16(),self.f16()]
        return val
    def g16(self):
        val = struct.unpack(self.endian+'h', self.file.read(2))[0]
        val = val/8192
        return val
    def g16_2(self):
        val = [self.g16(),self.g16()]
        return val
    def g16_3(self):
        val = [self.g16(),self.g16(),self.g16()]
        return val
    def f32(self):
        return struct.unpack(self.endian+'f', self.file.read(4))[0]
    def f32_4(self):
        return struct.unpack(self.endian+'ffff', self.file.read(16))[0:4]
    def f32_3(self):
        return struct.unpack(self.endian+'fff', self.file.read(12))[0:3]
    def f32_2(self):
        return struct.unpack(self.endian+'ff', self.file.read(8))[0:2]
    def seek(self,offset,whence=0):
        self.file.seek(offset,whence)
    def tell(self):
        return self.file.tell()
    def read(self,x):
        return self.file.read(x)
    def getString(self,offset = 0):
        if(offset):
            ret = self.file.tell()
            self.seek(offset)
        result = ""
        tmpChar = self.file.read(1)
        while ord(tmpChar) != 0:
            result += tmpChar.decode("utf-8")
            tmpChar = self.file.read(1)
        if(offset):
            self.seek(ret)
        return result
    def getStringSpecal(self,offset = 0):
        if(offset):
            ret = self.file.tell()
            self.seek(offset)
        result = ""
        tmpChar = chr(self.u8()-0x40)
        while ord(tmpChar) != 0:
            result += tmpChar
            tmpChar = chr(self.u8()-0x40)
        if(offset):
            self.seek(ret)
        return result
class FWrite(object): #Generic file writer
    def __init__(self,f,big_endian=False):
        self.endian='<'
        if(big_endian):
            self.endian ='>'
        self.file = f
    def swapEndian(self):
        if(self.endian == '>'):
            self.endian = '<'
        else:
            self.endian = '>'
    def u32(self,val):
        self.file.write(struct.pack(self.endian+'I', val))
    def u16(self,val):
        self.file.write(struct.pack(self.endian+'H', val))
    def u8(self,val):
        self.file.write(struct.pack(self.endian+'B', val))
    def u8_4(self,val):
        self.file.write(struct.pack(self.endian+'BBBB', val[0],val[1],val[2],val[3]))
    def s32(self,val):
        self.file.write(struct.pack(self.endian+'i', val))
    def s16(self,val):
        self.file.write(struct.pack(self.endian+'h', val))
    def s8(self,val):
        self.file.write(struct.pack(self.endian+'b', val))
    def f16(self,val):
        self.file.write(struct.pack(self.endian+'e', val))
    def f32(self,val):
        self.file.write(struct.pack(self.endian+'f', val))
    def f32_4(self,val):
        self.file.write(struct.pack(self.endian+'ffff',val[0],val[1],val[2],val[3]))
    def f32_3(self,val):
        self.file.write(struct.pack(self.endian+'fff',val[0],val[1],val[2]))
    def f32_2(self,val):
        self.file.write(struct.pack(self.endian+'ff',val[0],val[1]))
    def f16(self,val):
        v = struct.pack(self.endian+'f', val) >> 16
        self.file.write(v)
    def f16_2(self,val):
        self.f16(val[0])
        self.f16(val[1])
    def seek(self,offset,whence=0):
        self.file.seek(offset,whence)
    def tell(self):
        return self.file.tell()
    def write(self,x):
        return self.file.write(x)
    def getString(self,offset = 0):
        if(offset):
            ret = self.file.tell()
            self.seek(offset)
        result = ""
        tmpChar = self.file.read(1)
        while ord(tmpChar) != 0:
            result += tmpChar.decode("utf-8")
            tmpChar = self.file.read(1)
        if(offset):
            self.seek(ret)
        return result
class MTX(object):
    def __init__(self):
        self.matrix = [[0.0,0.0,0.0,0.0]*4]
    def read(self,f):
        tmp = []
        for x in range(4):
            tmp.append(f.f32_4())
        self.matrix = tmp
    def write(self,f):
        for x in self.matrix:
            f.f32_4(x)

class MDL(object):
    class Header(object):
        def __init__(self):
            self.filename = b'\x00'*0x18
            self.tristrip_offset = 0
            self.meshc_ount = 0
            self.strip_count = 0
        def read(self,f: FRead):
            self.filename = f.read(0x18)
            self.tristrip_offset = f.u32()
            self.mesh_count = f.u16()
            self.strip_count = f.u16()
        def write(self,f: FWrite):
            f.write(self.filename)
            f.u32(self.tristrip_offset)
            f.u16(self.mesh_count)
            f.u16(self.strip_count)
    class Mesh(object):
        class Cords(object):
            def __init__(self):
                self.position = [0.0]*3
                self.index = 0
                self.scale = 1.0
            def read(self,f:FRead):
                self.position = f.f32_3()
                self.index = f.u16()
                self.scale = f.f16()
            def write(self,f:FWrite):
                f.f32_3(self.position)
                f.u16(self.index)
                f.f16(self.scale)
        def __init__(self):
            self.bone_id0 = 0
            self.bone_id1 = 0 
            self.unk4 = 0 
            self.unk5 = 0      
            self.vertex_list_pointer = 0 
            self.unknown = 0 
            self.vertex_count = 0 
            self.normal_count = 0 
            self.bone_rotation_x = 0 
            self.bone_rotation_y = 0 
            self.bone_rotation_z = 0 
            self.unknown1 = 0 
            self.bone_position_x = 0
            self.bone_position_y = 0
            self.bone_position_z = 0
            self.parent_bone_id = 0
            self.pos = []
            self.nor = []
        def read(self,f:FRead):
            self.bone_id0 = f.u8()
            self.bone_id1 = f.u8()
            self.unk4 = f.u8()
            self.unk5 = f.u8()
            self.vertex_list_pointer = f.u32()
            self.unknown = f.u32()
            self.vertex_count = f.u16()
            self.normal_count = f.u16()
            self.bone_rotation_x = f.s16()
            self.bone_rotation_y = f.s16()
            self.bone_rotation_z = f.s16()
            self.unknown1 = f.s16()
            self.bone_position_x = f.s16()
            self.bone_position_y = f.s16()
            self.bone_position_z = f.s16()
            self.parent_bone_id = f.s16()
            ret = f.tell()
            f.seek(self.vertex_list_pointer)
            for x in range(self.vertex_count):
                v = self.Cords()
                v.read(f)
                self.pos.append(v)
            for x in range(self.normal_count):
                v = self.Cords()
                v.read(f)
                self.nor.append(v)
        def write(self,f : FWrite):
            f.u8(self.bone_id0)
            f.u8(self.bone_id1)
            f.u8(self.unk4)
            f.u8(self.unk5)
            f.u32(self.vertex_list_pointer)
            f.u32(self.unknown)
            f.u16(self.vertex_count)
            f.u16(self.normal_count)
            f.s16(self.bone_rotation_x)
            f.s16(self.bone_rotation_y)
            f.s16(self.bone_rotation_z)
            f.s16(self.unknown1)
            f.s16(self.bone_position_x)
            f.s16(self.bone_position_y)
            f.s16(self.bone_position_z)
            f.s16(self.parent_bone_id)
    

