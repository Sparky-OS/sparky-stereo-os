#!/usr/bin/env python3
"""shift.py A B x y w h: horizontal shift (px, sub-pixel by parabola) that best aligns B to A in the box, by SSD over -30..30."""
import sys, numpy as np
from PIL import Image
def gray(p): return np.array(Image.open(p).convert('L')).astype(float)
def best(a,b,x,y,w,h):
    ref=a[y:y+h,x:x+w]; res=[]
    for s in range(-30,31):
        cand=b[y:y+h,x+s:x+s+w]; res.append(((ref-cand)**2).mean())
    i=int(np.argmin(res)); 
    if 0<i<len(res)-1:
        d=(res[i-1]-2*res[i]+res[i+1]); off=0.5*(res[i-1]-res[i+1])/d if d else 0
    else: off=0
    return i-30+off
if __name__=='__main__':
    print(best(gray(sys.argv[1]),gray(sys.argv[2]),*[int(v) for v in sys.argv[3:7]]))
