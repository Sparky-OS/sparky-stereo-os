import os, sys, importlib, numpy as np
from PIL import Image
W=os.environ['WORK']; ALIGN=os.environ['ALIGN_SCRIPT']  # the installed /usr/lib/sparky-stereo/align/align
src=open(ALIGN).read().replace('sys.exit(main())','')
g={'__name__':'alignmod'}; exec(compile(src,'align','exec'),g)
cap=W+'/cap/'; out=os.environ.get('OUT', W+'/out/')
sel={ '01-gwenview-opens-a-marked-pair':'gw1.a',
 '02-gwenview-3d-input-format-menu':'gw9.6-menu-swap-ticked',
 '03-after-choosing-top-and-bottom':'gw9.3-after-top-bottom-left-first',
 '04-dolphin-thumbnails-in-3d':'dol2.a',
 '05-showfoto-shows-a-jps':'t-showfoto.a',
 '06-kolourpaint-shows-a-pns':'t-kolour.a',
 '07-sview-shows-an-mpo':'t-sview.a',
 '08-dolphin-align-stereo-pair-menu':'dctx.menu'}
for name,c in sel.items():
    im=Image.open(cap+c+'.png').convert('RGB'); w=im.width//2
    L=im.crop((0,0,w,im.height)); R=im.crop((w,0,2*w,im.height))
    open(out+name+'.mpo','wb').write(g['WRITERS']['mpo'](L,R))
    a=np.array(L).copy(); a[...,1:]=np.array(R)[...,1:]
    Image.fromarray(a).save(out+name+'-anaglyph.jpg',quality=86)
print('ok')
