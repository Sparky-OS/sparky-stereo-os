#!/usr/bin/python3
import sys, time, subprocess, json, os
from pathlib import Path
import pyatspi
from PIL import ImageGrab
result = Path(sys.argv[1]); result.mkdir(parents=True, exist_ok=True)
steps = sys.argv[2:]

def nodes(obj):
    yield obj
    try:
        for child in obj:
            yield from nodes(child)
    except Exception:
        pass

def tree():
    rows=[]
    def walk(o,d):
        try:
            rows.append('  '*d+f'{o.getRoleName()} | {o.name}')
            for c in o: walk(c,d+1)
        except Exception: pass
    walk(pyatspi.Registry.getDesktop(0),0)
    return rows

def snap(name):
    (result/(name+'.txt')).write_text('\n'.join(tree())+'\n')
    ImageGrab.grab().save(result/(name+'.png'))
    print('snap',name)

def find(name, role=None, nth=0):
    hits=[o for o in nodes(pyatspi.Registry.getDesktop(0)) if o.name==name and (role is None or o.getRoleName()==role)]
    if len(hits)<=nth: raise AssertionError(f'missing {name} {role}')
    return hits[nth]

def press(obj):
    r=obj.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
    subprocess.run(['xdotool','mousemove',str(r.x+r.width//2),str(r.y+r.height//2),'click','1'],check=True)
    time.sleep(1.5)

def resize():
    for w in subprocess.run(['xdotool','search','--onlyvisible','--classname','systemsettings'],capture_output=True,text=True).stdout.split():
        subprocess.run(['xdotool','windowsize',w,os.environ.get('PG_W','1300'),os.environ.get('PG_H','1450')]); subprocess.run(['xdotool','windowmove',w,'0','0'])
    time.sleep(1)
resize()
time.sleep(2)
for st in steps:
    if st.startswith('snap:'): snap(st[5:])
    elif st.startswith('press:'):
        parts=st[6:].split('|'); press(find(parts[0], parts[1] if len(parts)>1 and parts[1] else None, int(parts[2]) if len(parts)>2 else 0))
    elif st.startswith('key:'): subprocess.run(['xdotool','key']+st[4:].split(),check=True); time.sleep(1)
    elif st.startswith('click:'):
        x,y=st[6:].split(','); subprocess.run(['xdotool','mousemove',x,y,'click','1'],check=True); time.sleep(1.5)
    elif st.startswith('scroll:'):
        subprocess.run(['xdotool','mousemove','800','700']); [subprocess.run(['xdotool','click','5']) for _ in range(int(st[7:]))]; time.sleep(1.5)
    elif st=='resize': resize()
    elif st=='wins':
        for w in subprocess.run(['xdotool','search','--name',''],capture_output=True,text=True).stdout.split(): print('WIN',w,subprocess.run(['xdotool','getwindowgeometry',w],capture_output=True,text=True).stdout.replace('\n',' '))
        print(subprocess.run(['xdotool','search','--onlyvisible','--classname','systemsettings'],capture_output=True,text=True).stdout)
    elif st.startswith('sleep:'): time.sleep(float(st[6:]))
    elif st=='list':
        for r in tree():
            if any(k in r for k in ('combo box','check box','push button','radio button','spin button','label')): print(r)
