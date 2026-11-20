import sys, time
from Xlib import X, display
d = display.Display(); root = d.screen().root
names = ['_KDE_NET_WM_STEREO_CONTENT','_KDE_NET_WM_STEREO_CONTENT_CHILDREN','_KDE_NET_WM_STEREO_DEPTH_LIMITS','_KDE_NET_WM_STEREO_CONTENT_ONE_VIEW_SIZE']
atoms = {n: d.intern_atom(n) for n in names}
def walk(w, depth=0):
    yield w, depth
    try:
        for c in w.query_tree().children:
            yield from walk(c, depth+1)
    except Exception:
        pass
t0 = time.time(); last = {}; watchids=set()
end = float(sys.argv[1]) if len(sys.argv) > 1 else 12
while time.time() - t0 < end:
    for w, depth in walk(root):
        for n, a in atoms.items():
            try:
                p = w.get_full_property(a, X.AnyPropertyType)
            except Exception:
                continue
            if p is None: continue
            key = (w.id, n); val = list(p.value)
            if last.get(key) != val:
                last[key] = val
                try: g = w.get_geometry(); geo = (g.width, g.height)
                except Exception: geo = None
                print("%.2f win %#x geo %s %s = %s" % (time.time()-t0, w.id, geo, n, val), flush=True)
    for w, depth in walk(root):
        if depth in (1,) or w.id in watchids:
            try:
                a = w.get_attributes()
                nm = w.get_wm_name()
                key = (w.id, 'map'); val = [a.map_state]
                if last.get(key) != val:
                    last[key] = val
                    print("%.2f win %#x name %s map_state %s" % (time.time()-t0, w.id, nm, a.map_state), flush=True)
            except Exception:
                pass
    time.sleep(0.05)
