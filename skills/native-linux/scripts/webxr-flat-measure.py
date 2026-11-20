"""measure.py CASEDIR...: from pair2.png (both eyes side by side, left eye first) and result.json, the centroid of the pure red and
pure green squares in each eye, their separation on the screen (right minus left, positive = behind the screen) and the prediction
from the session's own views (what the page was given)."""
import json, sys, numpy as np
from PIL import Image
def centroid(a, rgb, tol=30):
    m = (np.abs(a[..., 0].astype(int) - rgb[0]) < tol) & (np.abs(a[..., 1].astype(int) - rgb[1]) < tol) & (np.abs(a[..., 2].astype(int) - rgb[2]) < tol)
    ys, xs = np.nonzero(m)
    return (None if len(xs) < 20 else (float(xs.mean()), float(ys.mean()), int(len(xs))))
def proj(P, V, pt):
    p = np.array(list(pt) + [1.0]); v = np.array(V).reshape(4, 4).T @ p; c = np.array(P).reshape(4, 4).T @ v
    return c[0] / c[3]
for d in sys.argv[1:]:
    r = json.load(open(d + "/result.json")); im = np.array(Image.open(d + "/pair2.png").convert("RGB")); W = im.shape[1] // 2
    out = {"case": d.rstrip("/").split("/")[-1], "capture": list(im.shape[:2][::-1])}
    L, R = im[:, :W], im[:, W:]
    for name, rgb in (("red", (255, 0, 0)), ("green", (0, 255, 0))):
        cl, cr = centroid(L, rgb), centroid(R, rgb)
        out[name] = {"left": cl, "right": cr, "separation_px": (None if not (cl and cr) else round(cr[0] - cl[0], 2))}
    x = r.get("xr") or {}
    if x.get("views"):
        v = json.loads(x["views"]); c = json.loads(x["centres"]); fb = json.loads(x["fb"]); rect = (r.get("page") or {}).get("rect"); inline = "inline" in d or "xrinline" in d; Wc = rect[2] if (inline and rect) else W
        for name in ("red", "green"):
            xl = proj(v[0]["P"], v[0]["V"], c[name]); xr = proj(v[1]["P"], v[1]["V"], c[name])
            # the view's share of the buffer is half of fb; the picture of one eye is shown at W px wide on the screen
            out[name]["predicted_px_at_eye_width"] = round((xr - xl) / 2 * Wc, 2)
        out["fb"] = fb
    print(json.dumps(out))
