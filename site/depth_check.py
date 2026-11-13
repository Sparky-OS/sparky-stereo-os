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
  fallback:getComputedStyle(w.querySelector('img')).display!=='none',
  hidden:document.hidden,cookie:document.cookie,text:document.body.innerText,
  matrices:window.probe?.matrices||{},
  bounds:JSON.parse(JSON.stringify(w.getBoundingClientRect()))
}})()'''

def project(m, v):
    return [sum(m[col*4+row]*v[col] for col in range(4)) for row in range(4)]

def geometry(matrices):
    """Compare an off-axis camera translation with the independent pinhole rule."""
    p=matrices['projectionMatrix']; view=matrices['modelViewMatrix']
    assert abs(p[11]+1)<1e-8 and p[15]==0 and p[0]>0
    separation=.06; plane=3.4; worst=vertical=0; signs=set(); count=0
    for ix in range(-8,9):
        for iy in range(-5,6):
            for z in (-.65,0,.65):
                eye=project(view,[ix*.1,iy*.1,z,1]); depth=-eye[2]
                eyes=[]
                for offset in (-separation/2,separation/2):
                    shifted=eye.copy();shifted[0]-=offset
                    projection=p.copy();projection[8]-=p[0]*offset/plane
                    q=project(projection,shifted);eyes.append((q[0]/q[3],q[1]/q[3]))
                disparity=eyes[0][0]-eyes[1][0]
                expected=p[0]*separation*(1/depth-1/plane)
                worst=max(worst,abs(disparity-expected));vertical=max(vertical,abs(eyes[0][1]-eyes[1][1]))
                if depth<plane-.1: assert disparity>0; signs.add('near crossed')
                if depth>plane+.1: assert disparity<0; signs.add('far uncrossed')
                if abs(expected)>.001:
                    assert abs(-disparity-expected)>.001 # swapped-eye control fails
                    assert abs(0-expected)>.001 # flat-eye control fails
                count+=1
    assert worst<1e-12 and vertical==0 and len(signs)==2
    return {'points':count,'maximum_ndc_error':worst,'vertical_disparity':vertical,
            'controls':['swapped eyes rejected','flat eyes rejected'],
            'scope':'matrix geometry, not a capture from the edition browser or physical display'}

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
                assert state['bounds']['bottom']<browser.evaluate('document.querySelector(".status").getBoundingClientRect().top',session)
                state['geometry']=geometry(state['matrices'])
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
    print('PASS: decoration fallback, local-only resources, no cookies, idle, geometry and negative controls',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--endpoint',default='http://127.0.0.1:9222')
    p.add_argument('--base-url',default='http://127.0.0.1:8000')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.endpoint,a.base_url,a.output)
