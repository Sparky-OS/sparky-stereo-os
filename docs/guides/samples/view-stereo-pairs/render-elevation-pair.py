#!/usr/bin/env python3
"""render-elevation-pair.py ELEVATION.tif MAX_DISPARITY_PX: a left and a right picture from an elevation model.

Shaded relief (light from the north-west, 40 degrees up) tinted by height; each picture is the shaded relief with every
column moved sideways by its height, so high ground has crossed disparity (it comes in front of the screen) and low
ground uncrossed (it sinks behind). Writes out/topo-left.png and out/topo-right.png, each the size of the model.
Make the MPO afterwards with the edition's Align stereo pair, or with the writers of sparky-stereo-align.
"""
import os, sys, numpy as np
from PIL import Image
dem=np.array(Image.open(sys.argv[1]),dtype=np.float64)
H,W=dem.shape
gy,gx=np.gradient(dem,30.0,30.0)  # ~30 m posting (0.2 deg lon ~ 15 km / 800 px = ~19 m); only shading
az=np.radians(315); alt=np.radians(40)
slope=np.arctan(np.hypot(gx,gy)*0.6); aspect=np.arctan2(-gx,gy)
shade=np.cos(np.pi/2-alt)*np.cos(slope)+np.sin(np.pi/2-alt)*np.sin(slope)*np.cos(az-aspect)
shade=np.clip(shade,0,1)
t=(dem-dem.min())/(dem.max()-dem.min())
stops=[(0,(46,94,52)),(0.25,(120,140,70)),(0.5,(176,160,110)),(0.75,(210,200,190)),(1,(255,255,255))]
rgb=np.zeros((H,W,3))
for c in range(3):
    rgb[...,c]=np.interp(t,[s[0] for s in stops],[s[1][c] for s in stops])
img=(rgb*(0.35+0.65*shade[...,None])).clip(0,255)
maxd=float(sys.argv[2])
d=(t-0.5)*2*maxd   # near (high) = crossed disparity, pops in front
xs=np.arange(W)[None,:].repeat(H,0).astype(np.float64)
def warp(sign):
    sx=np.clip(xs-sign*d,0,W-1)
    x0=np.floor(sx).astype(int); x1=np.clip(x0+1,0,W-1); f=(sx-x0)[...,None]
    r=np.arange(H)[:,None]
    return img[r,x0]*(1-f)+img[r,x1]*f
L=warp(+1); R=warp(-1)
os.makedirs('out',exist_ok=True)
Image.fromarray(L.astype(np.uint8)).save('out/topo-left.png')
Image.fromarray(R.astype(np.uint8)).save('out/topo-right.png')
print(W,H,'max disparity px',maxd)
