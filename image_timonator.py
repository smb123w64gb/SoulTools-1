from PIL import Image
import struct,sys,os

def u8(file):
    return struct.unpack("B", file.read(1))[0]
def u16(file):
    return struct.unpack("<H", file.read(2))[0]
def u32(file):
    return struct.unpack("<I", file.read(4))[0]

leScalor = float(256.0/32.0)
def rgba551(file):
    color_data = u16(file)
    red   = int(float(color_data & 0x1F)*leScalor) & 0xFF
    green = int(float((color_data >> 5) & 0x1F)*leScalor) & 0xFF 
    blue  = int(float((color_data >> 10) & 0x1F )*leScalor) & 0xFF
    return [red,green,blue]

fye = open(sys.argv[1],'rb')
fye.seek(16)

palsize = u16(fye)
palcnt = u16(fye)

pallet8 = []
curPal = []
for y in range(palsize):
    curPal.extend(rgba551(fye))
pallet8.append(curPal)
fye.seek(20 + 0x200)
pallet4 = []
for x in range((palcnt-1)*16):
    curPal = []
    for y in range(16):
        curPal.extend(rgba551(fye))
    pallet4.append(curPal)


fye.close()

tim = open(sys.argv[2],'rb')
tim.seek(16)

stride = u16(tim)
height = u16(tim)
width = stride*2

img = Image.new('P', (width,height))

print(img.size)
img.putpalette(pallet8[0])
for x in range(height):
    for y in range(width):
        #print("%i,%i"%(x,y))
        img.putpixel((y,x),u8(tim))



for indx,palin in enumerate(pallet8):
    img.putpalette(palin)
    img.save(str("%s_image_pal8_%2i.png" %(sys.argv[1],indx)))

tim.seek(16)
width = width*2
img = Image.new('P', (width,height))
for x in range(height):
    for y in range(int(width/2)):
        #print("%i,%i"%(x,y))
        px = u8(tim)
        p1 = px & 15
        p2 = (px >> 4) & 15
        print("%i,%i"%(p1,p2))
        img.putpixel((y*2,x),p1)
        img.putpixel(((y*2)+1,x),p2)
for indx,palin in enumerate(pallet4):
    img.putpalette(palin)
    img.save(str("%s_image_pal4_%2i.png" %(sys.argv[1],indx)))

tim.close()