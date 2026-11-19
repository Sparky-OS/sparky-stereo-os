#!/usr/bin/env python3
"""Independent mark check: JPS descriptor (VRex 1997), MPO via Pillow's MPO reader, PNG sTER chunk (PNG ext 1.4.0 3.6). Exit 1 on any failure."""
import struct, sys, zlib, io
from PIL import Image
import numpy as np
def jps(p):
    d=open(p,'rb').read(); i=2
    while d[i]==0xFF:
        m=d[i+1]; n=struct.unpack('>H',d[i+2:i+4])[0]
        if m==0xE3 and d[i+4:i+12]==b'_JPSJPS_':
            ln,desc=struct.unpack('>HI',d[i+12:i+18]); typ=desc&255; lay=(desc>>8)&255
            return dict(len=ln,type=typ,layout=lay,left_first=bool(desc>>18&1),half_w=bool(desc>>17&1),half_h=bool(desc>>16&1))
        if m==0xDA: break
        i+=2+n
    raise SystemExit(p+': no _JPSJPS_ APP3')
def png(p):
    d=open(p,'rb').read(); assert d[:8]==b'\x89PNG\r\n\x1a\n'; i=8; order=[]; mode=None
    while i<len(d):
        n=struct.unpack('>I',d[i:i+4])[0]; t=d[i+4:i+8]; body=d[i+8:i+8+n]; crc=struct.unpack('>I',d[i+8+n:i+12+n])[0]
        assert zlib.crc32(t+body)==crc,(p,t,'bad CRC'); order.append(t.decode())
        if t==b'sTER': mode=body[0]
        i+=12+n
    assert order[0]=='IHDR' and order[1]=='sTER' and 'IDAT' in order and order.index('sTER')<order.index('IDAT'),order
    return dict(order=order[:3],mode=mode)
def mpo(p):
    im=Image.open(p); n=getattr(im,'n_frames',1); fr=[]
    for k in range(n):
        im.seek(k); fr.append(np.array(im.convert('RGB')))
    return n,fr
for p in sys.argv[1:]:
    if p.endswith('.jps'): print(p,jps(p))
    elif p.endswith('.pns'): print(p,png(p))
    elif p.endswith('.mpo'):
        n,fr=mpo(p); print(p,'frames',n,[f.shape for f in fr]); assert n==2
    else: print(p,'unmarked (no check)')
