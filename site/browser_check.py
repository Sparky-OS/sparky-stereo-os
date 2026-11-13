#!/usr/bin/env python3
"""Capture the static preview with CDP. Run only against an isolated container browser.

Uses only the Python standard library. JavaScript expressions below inspect the
page through the debugger, independently of the optional local decoration script.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import struct
import time
from urllib.parse import urlsplit
from urllib.request import urlopen


class CDP:
    def __init__(self, endpoint):
        deadline=time.monotonic()+20
        while True:
            try:
                with urlopen(endpoint+'/json/version',timeout=2) as r: info=json.load(r)
                break
            except OSError:
                if time.monotonic()>=deadline:raise
                time.sleep(.2)
        self.version=info['Browser']
        p=urlsplit(info['webSocketDebuggerUrl'])
        self.sock=socket.create_connection((p.hostname,p.port),10)
        self.sock.settimeout(15)
        key=base64.b64encode(os.urandom(16)).decode()
        request=(f'GET {p.path} HTTP/1.1\r\nHost: {p.netloc}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n')
        self.sock.sendall(request.encode()); self.buffer=b''
        while b'\r\n\r\n' not in self.buffer:self.buffer+=self.sock.recv(4096)
        headers,self.buffer=self.buffer.split(b'\r\n\r\n',1)
        if not headers.startswith(b'HTTP/1.1 101'):raise RuntimeError(headers.decode())
        expected=base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest())
        if expected.lower() not in headers.lower():raise RuntimeError('WebSocket handshake not authenticated')
        self.sequence=0;self.events=[]
    def read(self,n):
        while len(self.buffer)<n:
            chunk=self.sock.recv(max(4096,n-len(self.buffer)))
            if not chunk:raise RuntimeError('CDP socket closed')
            self.buffer+=chunk
        data,self.buffer=self.buffer[:n],self.buffer[n:];return data
    def send(self,data,opcode=1):
        raw=data.encode() if isinstance(data,str) else data
        mask=os.urandom(4);size=len(raw)
        prefix=bytes([0x80|opcode,0x80|(size if size<126 else 126 if size<65536 else 127)])
        if size>=126:prefix+=struct.pack('!H' if size<65536 else '!Q',size)
        self.sock.sendall(prefix+mask+bytes(c^mask[i%4] for i,c in enumerate(raw)))
    def receive(self):
        fragments=[]
        while True:
            a,b=self.read(2);op=a&15;size=b&127
            if size==126:size=struct.unpack('!H',self.read(2))[0]
            elif size==127:size=struct.unpack('!Q',self.read(8))[0]
            mask=self.read(4) if b&128 else None
            raw=self.read(size)
            if mask:raw=bytes(c^mask[i%4] for i,c in enumerate(raw))
            if op==9:self.send(raw,10);continue
            if op==8:raise RuntimeError('CDP closed WebSocket')
            fragments.append(raw)
            if a&128:return json.loads(b''.join(fragments))
    def call(self,method,params=None,session=None):
        self.sequence+=1;ident=self.sequence
        packet={'id':ident,'method':method,'params':params or {}}
        if session:packet['sessionId']=session
        self.send(json.dumps(packet))
        while True:
            msg=self.receive()
            if msg.get('id')==ident:
                if 'error' in msg:raise RuntimeError(method+': '+str(msg['error']))
                return msg.get('result',{})
            self.events.append(msg)
    def evaluate(self,expression,session):
        answer=self.call('Runtime.evaluate',{'expression':expression,'returnByValue':True,'awaitPromise':True},session)
        if 'exceptionDetails' in answer:raise RuntimeError(str(answer))
        return answer.get('result',{}).get('value')


def run(endpoint,base,output):
    output.mkdir(parents=True,exist_ok=True)
    browser=CDP(endpoint);results=[]
    print('Browser:',browser.version,flush=True)
    for lang,folder in [('en',''),('pt_BR','pt-BR/'),('ja','ja/'),('es','es/')]:
        for name,width,height in [('wide',1280,960),('phone',390,844)]:
            for theme in ['light','dark']:
                context=browser.call('Target.createBrowserContext')['browserContextId']
                target=browser.call('Target.createTarget',{'url':'about:blank','browserContextId':context})['targetId']
                session=browser.call('Target.attachToTarget',{'targetId':target,'flatten':True})['sessionId']
                try:
                    for method in ['Page.enable','Network.enable','Runtime.enable']:
                        browser.call(method,session=session)
                    browser.call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':False},session)
                    browser.call('Emulation.setEmulatedMedia',{'features':[{'name':'prefers-color-scheme','value':theme}]},session)
                    browser.call('Emulation.setScriptExecutionDisabled',{'value':True},session)
                    browser.events=[]
                    url=base.rstrip('/')+'/'+folder
                    browser.call('Page.navigate',{'url':url},session)
                    deadline=time.monotonic()+12
                    while time.monotonic()<deadline:
                        if browser.evaluate('document.readyState',session)=='complete':break
                        time.sleep(.1)
                    else:raise RuntimeError('Page did not finish loading')
                    # Load every lazy image, then return to the first screen.
                    browser.evaluate('window.scrollTo(0,document.body.scrollHeight)',session)
                    time.sleep(.3)
                    browser.evaluate('window.scrollTo(0,0)',session)
                    deadline=time.monotonic()+10
                    while time.monotonic()<deadline:
                        if browser.evaluate('Array.from(document.images).every(x=>x.complete && x.naturalWidth>0)',session):break
                        time.sleep(.1)
                    else:raise RuntimeError('An image did not load')
                    browser.evaluate('document.fonts.ready',session)
                    measure=browser.evaluate('''JSON.parse(JSON.stringify({
                        width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,
                        lang:document.documentElement.lang,background:getComputedStyle(document.body).backgroundColor,
                        rootBackground:getComputedStyle(document.documentElement).backgroundColor,
                        scripts:document.scripts.length,cookie:document.cookie,
                        imageTop:document.querySelector('.hero img').getBoundingClientRect().top,
                        statusTop:document.querySelector('.status').getBoundingClientRect().top,
                        pageText:document.body.innerText,
                        menuCount:document.querySelectorAll('.lang li a').length,
                        failedImages:Array.from(document.images).filter(x=>!x.complete||!x.naturalWidth).map(x=>x.src)
                    }))''',session)
                    assert measure['scrollWidth']<=width,(lang,name,'overflow',measure)
                    assert measure['scripts']==1 and measure['cookie']=='',(lang,'script/cookie')
                    assert measure['menuCount']==10,(lang,'missing language')
                    requests=[e['params']['request']['url'] for e in browser.events if e.get('method')=='Network.requestWillBeSent' and e.get('sessionId')==session]
                    assert all(urlsplit(u).netloc==urlsplit(base).netloc for u in requests),requests
                    bad_responses=[e['params']['response']['status'] for e in browser.events if e.get('method')=='Network.responseReceived' and e.get('sessionId')==session and e['params']['response']['status']>=400]
                    assert not bad_responses,bad_responses
                    # Screenshot with site script execution disabled.
                    shot=browser.call('Page.captureScreenshot',{'format':'png'},session)
                    filename=f'{lang}-{name}-{theme}.png'
                    (output/filename).write_bytes(base64.b64decode(shot['data']))
                    size=browser.call('Page.getLayoutMetrics',session=session)['cssContentSize']
                    full=browser.call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':True,
                        'clip':{'x':0,'y':0,'width':width,'height':size['height'],'scale':1}},session)
                    (output/f'{lang}-{name}-{theme}-full.png').write_bytes(base64.b64decode(full['data']))
                    assert measure['imageTop'] < height - 100, (lang,name,'picture not sufficiently in first screen')
                    # Real keyboard input, not a scripted .click(), opens details.
                    browser.evaluate('document.activeElement.blur()',session)
                    keys=[]
                    for _ in range(4):
                        browser.call('Input.dispatchKeyEvent',{'type':'keyDown','key':'Tab','code':'Tab','windowsVirtualKeyCode':9},session)
                        browser.call('Input.dispatchKeyEvent',{'type':'keyUp','key':'Tab','code':'Tab','windowsVirtualKeyCode':9},session)
                        focus=browser.evaluate('document.activeElement.tagName',session);keys.append(focus)
                        if focus=='SUMMARY':break
                    assert focus=='SUMMARY',keys
                    browser.call('Input.dispatchKeyEvent',{'type':'keyDown','key':'Enter','code':'Enter','windowsVirtualKeyCode':13,'text':'\r','unmodifiedText':'\r'},session)
                    browser.call('Input.dispatchKeyEvent',{'type':'keyUp','key':'Enter','code':'Enter','windowsVirtualKeyCode':13},session)
                    assert browser.evaluate('document.querySelector("details.lang").open',session)
                    menu_box=browser.evaluate('(()=>{let r=document.querySelector(".lang ul").getBoundingClientRect();return {left:r.left,right:r.right,bottom:r.bottom}})()',session)
                    assert menu_box['left']>=0 and menu_box['right']<=width and menu_box['bottom']<=height,menu_box
                    browser.call('Input.dispatchKeyEvent',{'type':'keyDown','key':'Tab','code':'Tab','windowsVirtualKeyCode':9},session)
                    browser.call('Input.dispatchKeyEvent',{'type':'keyUp','key':'Tab','code':'Tab','windowsVirtualKeyCode':9},session)
                    focused=browser.evaluate('({tag:document.activeElement.tagName,href:document.activeElement.href,outline:getComputedStyle(document.activeElement).outlineStyle})',session)
                    assert focused['tag']=='A' and focused['outline']=='solid',focused
                    if lang=='en' and name=='phone':
                        shot=browser.call('Page.captureScreenshot',{'format':'png'},session)
                        (output/f'menu-{theme}.png').write_bytes(base64.b64decode(shot['data']))
                    browser.call('Input.dispatchKeyEvent',{'type':'keyDown','key':'Enter','code':'Enter','windowsVirtualKeyCode':13,'text':'\r','unmodifiedText':'\r'},session)
                    browser.call('Input.dispatchKeyEvent',{'type':'keyUp','key':'Enter','code':'Enter','windowsVirtualKeyCode':13},session)
                    time.sleep(.2)
                    assert browser.evaluate('location.href',session)==focused['href']
                    # The same document with JavaScript enabled has identical
                    # visible text; the separate decoration check executes the local script.
                    browser.call('Page.navigate',{'url':url},session)
                    time.sleep(.2)
                    browser.call('Emulation.setScriptExecutionDisabled',{'value':False},session)
                    assert browser.evaluate('document.body.innerText',session)==measure.pop('pageText')
                    # 320 CSS pixels is the WCAG reflow width, additional to the captures.
                    browser.call('Emulation.setDeviceMetricsOverride',{'width':320,'height':844,'deviceScaleFactor':1,'mobile':False},session)
                    assert browser.evaluate('document.documentElement.scrollWidth<=320',session)
                    measure.update({'capture':filename,'theme':theme,'layout':name,'requests':requests,
                                    'keyboard':keys+['Enter opens','Tab reaches link','Enter navigates'],
                                    'javascript_equivalent':True,'reflow_320':True})
                    results.append(measure)
                    print('PASS',filename,'first picture y=',round(measure['imageTop']),flush=True)
                finally:
                    browser.call('Target.disposeBrowserContext',{'browserContextId':context})
    # Audit every source page at the reflow width with enlarged text spacing.
    from model import load_catalogs, page_path
    audits=[]
    for lang,catalog in load_catalogs().items():
        for kind in catalog['pages']:
            context=browser.call('Target.createBrowserContext')['browserContextId']
            target=browser.call('Target.createTarget',{'url':'about:blank','browserContextId':context})['targetId']
            session=browser.call('Target.attachToTarget',{'targetId':target,'flatten':True})['sessionId']
            try:
                browser.call('Page.enable',session=session)
                browser.call('Emulation.setDeviceMetricsOverride',{'width':320,'height':844,'deviceScaleFactor':1,'mobile':False},session)
                browser.call('Emulation.setScriptExecutionDisabled',{'value':True},session)
                browser.call('Page.navigate',{'url':base.rstrip('/')+'/'+page_path(lang,kind)},session)
                deadline=time.monotonic()+10
                while time.monotonic()<deadline:
                    if browser.evaluate('document.readyState',session)=='complete':break
                    time.sleep(.1)
                else:raise RuntimeError('Audit page did not load')
                before=browser.evaluate('document.body.innerText',session)
                normal=browser.evaluate('document.documentElement.scrollWidth',session)
                assert normal<=320,(lang,kind,'normal reflow',normal)
                browser.evaluate('''document.body.style.lineHeight='2';
                    document.body.style.letterSpacing='.12em';document.body.style.wordSpacing='.16em';
                    document.querySelectorAll('p').forEach(p=>p.style.marginBottom='2em')''',session)
                spaced=browser.evaluate('document.documentElement.scrollWidth',session)
                assert spaced<=320,(lang,kind,'spaced reflow',spaced)
                assert browser.evaluate('document.body.innerText',session)==before
                expected=sum(kind in c['pages'] for c in load_catalogs().values())
                actual=browser.evaluate('document.querySelectorAll(".lang li a").length',session)
                assert actual==expected,(lang,kind,actual,expected)
                audits.append({'page':page_path(lang,kind),'normal_width':normal,'spaced_width':spaced,'menu_count':actual})
                print('PASS reflow and text spacing:',page_path(lang,kind),flush=True)
            finally:browser.call('Target.disposeBrowserContext',{'browserContextId':context})
    (output/'all-pages-audit.json').write_text(json.dumps(audits,ensure_ascii=False,indent=2)+'\n')
    (output/'browser-results.json').write_text(json.dumps({'browser':browser.version,'results':results},ensure_ascii=False,indent=2)+'\n')
    print('PASS: 16 capture contexts, 32 page captures, 2 keyboard-menu captures; 22 additional reflow/spacing contexts',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--endpoint',default='http://127.0.0.1:9222')
    p.add_argument('--base-url',default='http://127.0.0.1:8000')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.endpoint,a.base_url,a.output)

if __name__=='__main__':main()
