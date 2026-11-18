import json,sys
for l in sys.stdin:
    l=l.rstrip('\n')
    if l.startswith(('RESULT','DUMP')):
        try: d=json.loads(l.split(' ',1)[1])
        except Exception: print('UNPARSED',l[:80]); continue
        if 'ok' in d: print('RESULT ok=%s %s -> %s'%(d['ok'],d['what'],d['message'].get('text')))
        else:
            g=d['graph']
            print('DUMP',d['name'],'graph',{k:g.get(k) for k in('rate','allowedRates','quantum')},'user',json.dumps(d['user']),'system',json.dumps(d['system']))
            for dev in d['devices']: print('   ',dev['name'],'applied',dev.get('appliedFormat'),dev.get('appliedRate'),'person',dev['person'],'rates',dev['rates'],'formats',dev['formats'])
    elif 'dbus-run-session' in l: pass
    else: print(l[:300])
