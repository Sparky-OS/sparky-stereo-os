#!/usr/bin/env python3
"""eyes.py CAPTURE.png [x0 y0 x1 y1]: split a stereo capture into its two eyes (left half, right half), report mean RGB in a box and the pixel difference between eyes."""
import sys, numpy as np
from PIL import Image
im=np.array(Image.open(sys.argv[1]).convert('RGB')).astype(int); h,w,_=im.shape; e=w//2
L,R=im[:,:e],im[:,e:]
box=[int(v) for v in sys.argv[2:6]] if len(sys.argv)>=6 else [400,250,880,550]
x0,y0,x1,y1=box
ml=L[y0:y1,x0:x1].reshape(-1,3).mean(0); mr=R[y0:y1,x0:x1].reshape(-1,3).mean(0)
diff=(np.abs(L-R).sum(2)>0).sum()
print(f'{sys.argv[1].split("/")[-1]} size={w}x{h} left_mean={ml.round(0).tolist()} right_mean={mr.round(0).tolist()} differing_px_total={int(diff)} ({100*diff/(e*h):.2f}%)')
