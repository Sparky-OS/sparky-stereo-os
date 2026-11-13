#!/usr/bin/env python3
"""Check the optional drawing in an isolated CDP browser, including idle controls."""
import argparse
import base64
import json
import math
from pathlib import Path
import time
from urllib.parse import urlsplit
from browser_check import CDP

HOOK = r'''
(() => {
window.probe={draws:0,contexts:0,matrices:{},pending:new Set()};
const raf=requestAnimationFrame, cancel=cancelAnimationFrame;
window.requestAnimationFrame=fn=>{const id=raf(t=>{probe.pending.delete(id);fn(t)});probe.pending.add(id);return id};
window.cancelAnimationFrame=id=>{probe.pending.delete(id);cancel(id)};
const context=HTMLCanvasElement.prototype.getContext;
HTMLCanvasElement.prototype.getContext=function(kind,...rest){
  if(kind==='webgl'){probe.contexts++;if(window.noWebGL)return null;}
  const result=context.call(this,kind,...rest);if(kind==='webgl')probe.gl=result;return result;
};
const names=new WeakMap(), api=WebGLRenderingContext.prototype;
const location=api.getUniformLocation, matrix=api.uniformMatrix4fv, draw=api.drawArrays;
api.getUniformLocation=function(program,name){const result=location.call(this,program,name);if(result)names.set(result,name);return result};
api.uniformMatrix4fv=function(loc,transpose,value){probe.matrices[names.get(loc)]=Array.from(value);return matrix.call(this,loc,transpose,value)};
api.drawArrays=function(...args){probe.draws++;return draw.apply(this,args)};
})();
'''

STATE = r'''(()=>{const w=document.querySelector('.depth-decoration');return {
  ready:w.classList.contains('depth-ready'),draws:window.probe?.draws||0,
  contexts:window.probe?.contexts||0,pending:window.probe?.pending.size||0,
  fallback:getComputedStyle(w).display==='none' && (()=>{const r=document.querySelector('.hero img').getBoundingClientRect();return r.width>100 && r.top<innerHeight})(),
  hidden:document.hidden,cookie:document.cookie,text:document.body.innerText,
  matrices:window.probe?.matrices||{},
  bounds:JSON.parse(JSON.stringify(w.getBoundingClientRect()))
}})()'''

def levels(matrices, scene, sunk=10.0, popped=4.0):
    """Where the edition browser's second camera puts each plane, by its two rules for the screen plane.

    The published browser takes five times the camera's near distance and 2 percent of the canvas's width; the
    staged one takes the distance at which the nearest and the farthest part have equal and opposite parallax,
    2nf / (n + f), no further than n (1 + popped / sunk), and the person's sunk limit as the parallax of infinity.
    A point at distance z then has the parallax separation * (plane / z - 1), positive in front of the screen.
    """
    p = matrices['projectionMatrix']
    assert abs(p[11] + 1) < 1e-8 and p[15] == 0 and p[0] > 0, 'not a perspective camera the browser recognises'
    near = p[14] / (p[10] - 1)
    distance = {x['name']: x['distance'] for x in scene['planes']}
    first = 5 * near
    balanced = 2 * distance['popped'] * distance['sunk'] / (distance['popped'] + distance['sunk'])
    plane = min(balanced, distance['popped'] * (1 + popped / sunk))
    result = {'near': near, 'plane_published': first, 'plane_from_scene': plane, 'limits': [sunk, popped], 'planes': {}}
    for name, z in distance.items():
        result['planes'][name] = {'distance': z, 'published_percent_of_canvas': round(2 * (first / z - 1), 4),
                                  'px_at_1920_with_limits': round(sunk * (plane / z - 1), 4)}
    for rule in ('published_percent_of_canvas', 'px_at_1920_with_limits'):
        s, m, f = (result['planes'][n][rule] for n in ('sunk', 'screen', 'popped'))
        assert s < -1e-6, (rule, 'the sunk plane is not behind the screen', s)
        assert abs(m) < 1e-6, (rule, 'the window in use is not at the screen', m)
        assert f > 1e-6, (rule, 'the popped plane is not in front of the screen', f)
    assert result['planes']['popped']['px_at_1920_with_limits'] <= popped + 1e-6
    assert result['planes']['sunk']['px_at_1920_with_limits'] >= -sunk - 1e-6
    return result


def levels_control():
    """The drawing as first written (near 0.8, planes 4.05, 3.4 and 2.75 away) must fail the same check."""
    near, far = .8, 12
    old = {'projectionMatrix': [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, (far + near) / (near - far), -1, 0, 0, 2 * far * near / (near - far), 0]}
    scene = {'planes': [{'name': 'sunk', 'distance': 4.05}, {'name': 'screen', 'distance': 3.4}, {'name': 'popped', 'distance': 2.75}]}
    try:
        levels(old, scene)
    except AssertionError as error:
        return 'rejected: ' + str(error.args[0][1] if error.args and isinstance(error.args[0], tuple) else error)
    raise AssertionError('the control drawing passed; this check cannot fail')


def run(endpoint,base,output):
    output.mkdir(parents=True,exist_ok=True);browser=CDP(endpoint);results=[];plain=None
    for case in ('script-off','reduced-motion','no-webgl','moving-light','moving-dark','context-loss'):
        context=browser.call('Target.createBrowserContext')['browserContextId']
        target=browser.call('Target.createTarget',{'url':'about:blank','browserContextId':context})['targetId']
        session=browser.call('Target.attachToTarget',{'targetId':target,'flatten':True})['sessionId']
        try:
            for method in ('Page.enable','Network.enable','Runtime.enable'):browser.call(method,session=session)
            browser.call('Emulation.setDeviceMetricsOverride',{'width':1280,'height':960,'deviceScaleFactor':1,'mobile':False},session)
            browser.call('Emulation.setEmulatedMedia',{'features':[
                {'name':'prefers-reduced-motion','value':'reduce' if case=='reduced-motion' else 'no-preference'},
                {'name':'prefers-color-scheme','value':'dark' if case=='moving-dark' else 'light'}]},session)
            browser.call('Page.addScriptToEvaluateOnNewDocument',{'source':HOOK+('window.noWebGL=true;' if case=='no-webgl' else '')},session)
            if case=='script-off':browser.call('Emulation.setScriptExecutionDisabled',{'value':True},session)
            browser.events=[];browser.call('Page.navigate',{'url':base+'/'},session)
            deadline=time.monotonic()+10
            while time.monotonic()<deadline:
                if browser.evaluate('document.readyState',session)=='complete':break
                time.sleep(.1)
            else:raise RuntimeError('Decoration page did not load')
            time.sleep(.35);state=browser.evaluate(STATE,session)
            if plain is None:plain=state['text']
            assert state.pop('text')==plain,(case,'changed text')
            assert not state['cookie']
            if case in ('script-off','reduced-motion','no-webgl'):
                assert state['fallback'] and not state['ready'] and not state['draws'] and not state['pending'],state
            else:
                assert state['ready'] and state['draws']>0 and not state['fallback'],state
                # Decoration: never over the status or the next step, wherever the layout puts them.
                assert not browser.evaluate('''(()=>{const a=document.querySelector(".depth-decoration").getBoundingClientRect();
                    return [".status",".next-step"].some(q=>{const b=document.querySelector(q).getBoundingClientRect();
                    return a.left<b.right&&b.left<a.right&&a.top<b.bottom&&b.top<a.bottom})})()''',session)
                state['levels']=levels(state['matrices'],json.loads(browser.evaluate("document.querySelector('.depth-decoration canvas').dataset.scene",session)));state['levels']['control']=levels_control()
            if case!='context-loss':
                shot=browser.call('Page.captureScreenshot',{'format':'png'},session)
                (output/('decoration-'+case+'.png')).write_bytes(base64.b64decode(shot['data']))
            if case=='moving-light':
                # Exercise the application's visibility handler, independently
                # of the browser itself throttling a background tab's callbacks.
                browser.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))",session)
                before=browser.evaluate('probe.draws',session);time.sleep(.3)
                assert browser.evaluate('probe.draws',session)==before
                assert browser.evaluate('probe.pending.size',session)==0
                browser.evaluate("delete document.hidden;document.dispatchEvent(new Event('visibilitychange'))",session)
                browser.evaluate('scrollTo(0,document.body.scrollHeight)',session);time.sleep(.2)
                before=browser.evaluate('probe.draws',session);time.sleep(.3)
                assert browser.evaluate('probe.draws',session)==before
                assert browser.evaluate('probe.pending.size',session)==0
                browser.evaluate('scrollTo(0,0)',session)
                time.sleep(5.1)
                before=browser.evaluate('probe.draws',session);time.sleep(.3)
                assert browser.evaluate('probe.draws',session)==before
                assert browser.evaluate('probe.pending.size',session)==0
                state['idle_checks']=['visibility handler cancels','offscreen stops','animation ends with no pending frame']
                browser.call('Emulation.setEmulatedMedia',{'features':[{'name':'prefers-reduced-motion','value':'reduce'}]},session)
                time.sleep(.15);assert browser.evaluate(STATE,session)['fallback']
            if case=='context-loss':
                browser.evaluate("probe.gl.getExtension('WEBGL_lose_context').loseContext()",session);time.sleep(.15)
                after=browser.evaluate(STATE,session)
                assert after['fallback'] and not after['ready'] and not after['pending'],after
            requests=[e['params']['request']['url'] for e in browser.events if e.get('method')=='Network.requestWillBeSent' and e.get('sessionId')==session]
            assert all(urlsplit(u).netloc==urlsplit(base).netloc for u in requests),requests
            errors=[e for e in browser.events if e.get('method')=='Runtime.exceptionThrown' and e.get('sessionId')==session]
            assert not errors,errors
            state.update(case=case,requests=requests);results.append(state)
            print('PASS decoration:',case,flush=True)
        finally:browser.call('Target.disposeBrowserContext',{'browserContextId':context})
    (output/'decoration-checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print('PASS: decoration still form, local-only resources, no cookies, idle, the three levels by the browser\'s rules and their negative control',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--endpoint',default='http://127.0.0.1:9222')
    p.add_argument('--base-url',default='http://127.0.0.1:8000')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.endpoint,a.base_url,a.output)
