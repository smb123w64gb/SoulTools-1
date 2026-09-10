import model_fmt_sc1_dc
import sys
import json


f = open(sys.argv[1],'rb')
input = model_fmt_sc1_dc.MDL()
freader = model_fmt_sc1_dc.FRead(f)
input.read(freader)

for x in input.meshes:
    for y in x.pos:
        print("Index %04x : %03f"%(y.index,y.scale))