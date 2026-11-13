#!/usr/bin/env python3
"""Capture the scene-first UI's real stages at two CSS viewport sizes."""
import json
from pathlib import Path
import sys
import time
from devtools import WS, target, evaluate, wait_for, screenshot

out, tag = Path(sys.argv[1]), sys.argv[2]
ws = WS(target(int(sys.argv[3]), int(sys.argv[4])))
timeout = float(sys.argv[5])
ws.call('Page.enable')
ws.call('Runtime.enable')
assert wait_for(ws, '!!window.testerState', 30), 'no page state'
ws.call('Emulation.setDeviceMetricsOverride', {'width':1280,'height':900,'deviceScaleFactor':1,'mobile':False})
stages = {}
start = time.monotonic()


def ev(s):
    return evaluate(ws, s)


def captures(stage):
    records = {}
    for width, height in [(1280,900),(360,800)]:
        ws.call('Emulation.setDeviceMetricsOverride', {'width':width,'height':height,'deviceScaleFactor':1,'mobile':False})
        ev('window.scrollTo(0,0)')
        time.sleep(.35)
        records[str(width)] = ev('''({state:testerState(),text:document.getElementById('scene-state').textContent,
          viewport:[innerWidth,innerHeight],rects:Object.fromEntries(['scene','scene-state','quick-speed','restart'].map(id=>{
            const r=document.getElementById(id).getBoundingClientRect();return [id,{x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom}];}))})''')
        screenshot(ws,str(out/f'{tag}-{stage}-{width}.png'))
    ws.call('Emulation.setDeviceMetricsOverride', {'width':1280,'height':900,'deviceScaleFactor':1,'mobile':False})
    stages[stage] = records
    (out/f'{tag}-stages.json').write_text(json.dumps(stages,ensure_ascii=False,indent=2)+'\n')


while time.monotonic()-start < timeout:
    state = ev('testerState()')
    modes = [t['mode'] for t in state['textures']]
    count = modes.count('picture')
    if state['firstFrame'] is not None and modes and all(m=='procedure' for m in modes) and 'computed' not in stages:
        captures('computed')
    if 0 < count < len(modes) and 'partial' not in stages:
        captures('partial')
    result = ev('window.testerResult')
    if result:
        (out/f'{tag}-result.json').write_text(result+'\n')
        captures('all')
        if ev('testerState().comparison.ready'):
            # Real keyboard down/up on the momentary compare button.
            ev("document.getElementById('compare-hold').focus({preventScroll:true})")
            ws.call('Input.dispatchKeyEvent',{'type':'keyDown','key':' ','code':'Space','text':' ','windowsVirtualKeyCode':32})
            time.sleep(.4)
            assert ev('testerState().comparison.holding'), 'keyboard hold did not activate'
            captures('held')
            ws.call('Input.dispatchKeyEvent',{'type':'keyUp','key':' ','code':'Space','windowsVirtualKeyCode':32})
            assert not ev('testerState().comparison.holding'), 'keyboard release did not restore photographs'
            ev("(()=>{const s=document.getElementById('compare-method');s.value='split';s.dispatchEvent(new Event('change'));})()")
            time.sleep(.4)
            captures('split')
        (out/f'{tag}-state.json').write_text(json.dumps(ev('testerState()'),indent=2)+'\n')
        (out/'DONE').write_text('ok\n')
        print(tag, 'captured', ', '.join(stages),flush=True)
        break
    time.sleep(.1 if time.monotonic()-start<30 else .5)
else:
    raise TimeoutError('page did not finish within the proof timeout')
