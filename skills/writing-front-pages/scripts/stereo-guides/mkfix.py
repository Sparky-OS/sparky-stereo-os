import os, sys, io, struct, zlib, importlib.util, importlib.machinery
from PIL import Image, ImageDraw, ImageFont
fx=W+'/fx/'
W=os.environ['WORK']; ALIGN=os.environ['ALIGN_SCRIPT']  # the installed /usr/lib/sparky-stereo/align/align
src=open(ALIGN).read()
src=src.replace('sys.exit(main())','')
g={'__name__':'alignmod'}; exec(compile(src,'align','exec'),g)
def label(color,text,shift):
    im=Image.new('RGB',(640,480),color); d=ImageDraw.Draw(im)
    f=ImageFont.load_default(size=72)
    d.text((60,60),text,fill='white',font=f)
    d.ellipse((220+shift,200,420+shift,400),outline='white',width=8)
    return im
L=label((200,30,30),'LEFT',+8); R=label((30,30,200),'RIGHT',-8)
L.save(fx+'lbl-left.png'); R.save(fx+'lbl-right.png')
tl=Image.open(W+'/samples/out/topo-left.png').convert('RGB'); tr=Image.open(W+'/samples/out/topo-right.png').convert('RGB')
for name,(a,b) in {'lbl':(L,R),'topo':(tl,tr)}.items():
    for fmt in ('jps','mpo','pns'):
        open(fx+f'{name}.{fmt}','wb').write(g['WRITERS'][fmt](a,b))
# unmarked packings, plain files
c=Image.new('RGB',(2*tl.width,tl.height)); c.paste(tl,(0,0)); c.paste(tr,(tl.width,0)); c.save(fx+'topo-sbs-unmarked.png')
t=Image.new('RGB',(tl.width,2*tl.height)); t.paste(tl,(0,0)); t.paste(tr,(0,tl.height)); t.save(fx+'topo-tb-unmarked.jpg',quality=95)
# half side by side: each eye squeezed to half width
h=Image.new('RGB',(tl.width,tl.height)); h.paste(tl.resize((tl.width//2,tl.height)),(0,0)); h.paste(tr.resize((tl.width//2,tl.height)),(tl.width//2,0)); h.save(fx+'topo-halfsbs-unmarked.png')
# ordinary 2D control
tl.save(fx+'flat-2d.png')
# swapped-eyes plain file (right eye first)
c2=Image.new('RGB',(2*tl.width,tl.height)); c2.paste(tr,(0,0)); c2.paste(tl,(tl.width,0)); c2.save(fx+'topo-sbs-righteyefirst-unmarked.png')
