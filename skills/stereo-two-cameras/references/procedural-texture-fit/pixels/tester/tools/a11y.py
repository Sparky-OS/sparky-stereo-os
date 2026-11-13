#!/usr/bin/env python3
"""The accessibility checks of the Procedural Texture Rendering page (WCAG 2.2, level A and AA), run in Chromium
through the DevTools protocol inside the proof container. Each check names its success criterion, says what it
looked at and what it found, and passes or fails; nothing here can pass without the page being looked at.

a11y.py OUTDIR TAG DEVTOOLS-PORT SERVER-PORT TIMEOUT-S [unused]

Writes OUTDIR/TAG-a11y.json (every check), TAG-a11y.md (the table), TAG-axtree-LANG.txt (the panel as a screen
reader is given it: role, name, value and description of every node of the accessibility tree, in reading order),
and screenshots (light, dark, 320 pixels wide, 200 percent, text spacing, a focused control). Our code, BSD 2-clause."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import devtools  # noqa: E402

out, tag = sys.argv[1], sys.argv[2]
dport, sport = int(sys.argv[3]), int(sys.argv[4])
timeout = float(sys.argv[5]) if len(sys.argv) > 5 else 900
ws = devtools.WS(devtools.target(dport, sport))
for dom in ('Runtime', 'Page', 'DOM', 'Accessibility'):
    ws.call(dom + '.enable')
ev = lambda js, **k: devtools.evaluate(ws, js, **k)
checks = []
LANGS = ['en', 'pl', 'pt_BR', 'fr', 'de', 'es', 'ja', 'ko', 'zh_CN', 'zh_TW']
TAGS = {'en': 'en', 'pl': 'pl', 'pt_BR': 'pt-BR', 'fr': 'fr', 'de': 'de', 'es': 'es', 'ja': 'ja', 'ko': 'ko', 'zh_CN': 'zh-Hans', 'zh_TW': 'zh-Hant'}


def check(sc, what, ok, found):
    checks.append({'criterion': sc, 'check': what, 'pass': bool(ok), 'found': found})
    print('%s %s: %s -- %s' % ('PASS' if ok else 'FAIL', sc, what, str(found)[:300]), flush=True)


def shot(name):
    devtools.screenshot(ws, os.path.join(out, '%s-%s.png' % (tag, name)))


base = devtools.wait_for(ws, "location.protocol === 'http:' && !!document.getElementById('panel') && location.origin + location.pathname", timeout=30)
metrics_ready = True


def go(query, wait='document.getElementById("panel-title") && window.testerState && true', t=60):
    if 'lang=' not in query: query += '&lang=en'
    origin = ev('performance.timeOrigin')
    ws.call('Page.navigate', {'url': base + '?' + query})
    time.sleep(0.5)
    v = devtools.wait_for(ws, 'performance.timeOrigin !== ' + str(origin) + ' && (' + wait + ')', timeout=t)
    if v: ev('document.getElementById("measurements").open = true')
    return v


def media(scheme=None, motion=None):
    feats = []
    if scheme:
        feats.append({'name': 'prefers-color-scheme', 'value': scheme})
    if motion:
        feats.append({'name': 'prefers-reduced-motion', 'value': motion})
    ws.call('Emulation.setEmulatedMedia', {'media': '', 'features': feats})


def metrics(w, h, dsf=1):
    ws.call('Emulation.setDeviceMetricsOverride', {'width': w, 'height': h, 'deviceScaleFactor': dsf, 'mobile': False})


def key(k, code, vk, mods=0):
    # Enter and Space act through their text, as a keyboard's do
    text = {'Enter': '\r', ' ': ' '}.get(k)
    down = {'type': 'keyDown' if text else 'rawKeyDown', 'key': k, 'code': code, 'windowsVirtualKeyCode': vk, 'nativeVirtualKeyCode': vk, 'modifiers': mods}
    if text:
        down['text'] = text
    ws.call('Input.dispatchKeyEvent', down)
    ws.call('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': k, 'code': code, 'windowsVirtualKeyCode': vk, 'nativeVirtualKeyCode': vk, 'modifiers': mods})


CONTRAST_JS = r'''(() => {
  const parse = (c) => { const m = /rgba?\(([\d.]+)[, ]+([\d.]+)[, ]+([\d.]+)(?:[,/ ]+([\d.]+))?\)/.exec(c); return m ? { r: +m[1], g: +m[2], b: +m[3], a: m[4] == null ? 1 : +m[4] } : null; };
  const lin = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const lum = (c) => 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
  const ratio = (a, b) => { const la = lum(a), lb = lum(b); return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05); };
  const hex = (c) => '#' + [c.r, c.g, c.b].map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');
  const bgOf = (el) => { for (let e = el; e; e = e.parentElement) { const b = parse(getComputedStyle(e).backgroundColor); if (b && b.a > 0.99) return b; } return { r: 255, g: 255, b: 255, a: 1 }; };
  const visible = (el) => { const cs = getComputedStyle(el); const r = el.getBoundingClientRect(); return cs.visibility !== 'hidden' && cs.display !== 'none' && r.width > 1.5 && r.height > 1.5 && !el.closest('[hidden]'); };
  const text = [], nontext = [];
  const seen = new Set();
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    if (!n.nodeValue.trim()) continue;
    const el = n.parentElement;
    if (!el || seen.has(el) || el.closest('script,style,noscript,option')) continue;
    seen.add(el);
    if (!visible(el)) continue;
    const cs = getComputedStyle(el);
    const fg = parse(cs.color);
    let bgs = [bgOf(el)];
    if (el.matches('.bar > b')) { bgs = [bgOf(el.parentElement)]; const fill = el.parentElement.querySelector('i'); if (fill && fill.getBoundingClientRect().width > 0.5) bgs.push(parse(getComputedStyle(fill).backgroundColor)); }
    const size = parseFloat(cs.fontSize), bold = +cs.fontWeight >= 700;
    const need = (size >= 24 || (bold && size >= 18.66)) ? 3 : 4.5;
    const r = Math.min(...bgs.map((b) => ratio(fg, b)));
    text.push({ text: n.nodeValue.trim().slice(0, 48), where: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className ? '.' + String(el.className).split(' ')[0] : ''), fg: hex(fg), bg: bgs.map(hex).join(' and '), size, ratio: +r.toFixed(2), need });
  }
  for (const el of document.querySelectorAll('select, input, button')) {
    if (!visible(el)) continue;
    const cs = getComputedStyle(el);
    const own = parse(cs.backgroundColor), around = bgOf(el.parentElement);
    const ownBg = own && own.a > 0.99 ? own : around;
    if (el.type !== 'checkbox') text.push({ text: (el.value || el.textContent || '').trim().slice(0, 40) || '(control)', where: el.tagName.toLowerCase() + '#' + el.id, fg: hex(parse(cs.color)), bg: hex(ownBg), size: parseFloat(cs.fontSize), ratio: +ratio(parse(cs.color), ownBg).toFixed(2), need: 4.5 });
    if (el.type !== 'checkbox') nontext.push({ what: 'border of ' + el.tagName.toLowerCase() + '#' + el.id, a: hex(parse(cs.borderTopColor)), b: hex(around), ratio: +ratio(parse(cs.borderTopColor), around).toFixed(2), need: 3 });
  }
  for (const bar of document.querySelectorAll('.bar')) {
    if (!visible(bar)) continue;
    const fill = bar.querySelector('i');
    const track = parse(getComputedStyle(bar).backgroundColor), around = bgOf(bar.parentElement), edge = parse(getComputedStyle(bar).borderTopColor);
    nontext.push({ what: 'bar edge ' + (bar.id || bar.className), a: hex(edge), b: hex(around), ratio: +ratio(edge, around).toFixed(2), need: 3 });
    if (fill && fill.getBoundingClientRect().width > 0.5) { const f = parse(getComputedStyle(fill).backgroundColor); nontext.push({ what: 'bar fill ' + (bar.id || bar.className), a: hex(f), b: hex(track), ratio: +ratio(f, track).toFixed(2), need: 3 }); }
  }
  const css = getComputedStyle(document.documentElement);
  const v = (n) => { const d = document.createElement('i'); d.style.color = css.getPropertyValue(n).trim(); document.body.append(d); const c = parse(getComputedStyle(d).color); d.remove(); return c; };
  const panel = v('--panel');
  for (const n of ['--proc', '--down', '--blend', '--pic']) nontext.push({ what: 'timeline segment ' + n, a: hex(v(n)), b: hex(panel), ratio: +ratio(v(n), panel).toFixed(2), need: 3 });
  for (const n of ['--fg', '--muted', '--bad']) text.push({ text: 'timeline chart text ' + n, where: 'canvas#timeline', fg: hex(v(n)), bg: hex(panel), size: 12, ratio: +ratio(v(n), panel).toFixed(2), need: 4.5 });
  nontext.push({ what: 'focus outline against the panel', a: hex(v('--focus')), b: hex(panel), ratio: +ratio(v('--focus'), panel).toFixed(2), need: 3 });
  nontext.push({ what: 'focus outline against the page', a: hex(v('--focus')), b: hex(v('--bg')), ratio: +ratio(v('--focus'), v('--bg')).toFixed(2), need: 3 });
  return { text, nontext };
})()'''

OVERFLOW_JS = r'''(() => {
  const vw = document.documentElement.clientWidth;
  const wide = [], clipped = [];
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || el.closest('[hidden]') || el.classList.contains('sr') || el.closest('.sr') || el.classList.contains('skip')) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    if (r.right > vw + 1 || r.left < -1) wide.push(el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + ' ' + Math.round(r.left) + '..' + Math.round(r.right));
    const hasText = [...el.childNodes].some((n) => n.nodeType === 3 && n.nodeValue.trim());
    if (hasText && (cs.overflowX === 'hidden' || cs.overflowY === 'hidden' || cs.overflow === 'hidden') && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)) clipped.push(el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + ': ' + el.textContent.trim().slice(0, 30));
    // text inside a bar: the bar clips what does not fit
    if (el.matches('.bar > b') && (el.scrollWidth > el.parentElement.clientWidth + 1 || el.offsetHeight > el.parentElement.clientHeight + 1)) clipped.push('bar text: ' + el.textContent.trim().slice(0, 40));
  }
  return { viewport: vw, scrollWidth: document.documentElement.scrollWidth, wide: wide.slice(0, 12), clipped: clipped.slice(0, 12) };
})()'''

TARGETS_JS = r'''(() => {
  const small = [], all = [];
  for (const el of document.querySelectorAll('a[href], button, select, input, summary')) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || el.closest('[hidden]')) continue;
    let r = el.getBoundingClientRect();
    if (el.type === 'checkbox' && el.closest('label')) r = el.closest('label').getBoundingClientRect();   // the label is the target too
    if (r.width < 1) continue;
    const name = el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + ' ' + Math.round(r.width) + 'x' + Math.round(r.height);
    all.push(name);
    const inline = el.tagName === 'A' && el.closest('p');     // a link in a sentence: the Inline exception
    if ((r.width < 24 || r.height < 24) && !inline) small.push(name);
  }
  return { count: all.length, small, all };
})()'''

# ---------------------------------------------------------------- 1. the page, settled, in light and dark
if not devtools.wait_for(ws, 'window.testerResult && true', timeout=min(timeout, 300)):
    check('setup', 'the scene finished loading before the checks', False, ev('JSON.stringify(window.testerState && testerState())'))
check('first screen', 'Details and measurements starts closed', ev('document.getElementById("measurements").open') is False, ev('document.getElementById("measurements").open'))
ev('document.getElementById("measurements").open = true; document.getElementById("timeline-details").open = true')
time.sleep(0.6)
for scheme in ('light', 'dark'):
    media(scheme=scheme)
    time.sleep(0.6)
    r = ev(CONTRAST_JS)
    low = [x for x in r['text'] if x['ratio'] < x['need']]
    worst = min(r['text'], key=lambda x: x['ratio'] / x['need'])
    check('1.4.3 Contrast (Minimum)', '%s scheme: every text against what is behind it (%d texts, the bars\' text against track and fill)' % (scheme, len(r['text'])),
          not low, 'lowest %.2f:1 (%s, %s on %s); below the minimum: %s' % (worst['ratio'], worst['where'], worst['fg'], worst['bg'], json.dumps(low)[:400]))
    lown = [x for x in r['nontext'] if x['ratio'] < x['need']]
    worstn = min(r['nontext'], key=lambda x: x['ratio'])
    check('1.4.11 Non-text Contrast', '%s scheme: control borders, bar edges and fills, timeline segments, the focus outline (%d pairs)' % (scheme, len(r['nontext'])),
          not lown, 'lowest %.2f:1 (%s); below 3:1: %s' % (worstn['ratio'], worstn['what'], json.dumps(lown)[:400]))
    with open(os.path.join(out, '%s-contrast-%s.json' % (tag, scheme)), 'w') as f:
        json.dump(r, f, indent=1, ensure_ascii=False)
    shot('scheme-' + scheme)
media(scheme='light')

# ---------------------------------------------------------------- 2. the accessibility tree: what a screen reader is given
def ax_reading(lang):
    tree = ws.call('Accessibility.getFullAXTree')['nodes']
    by = {n['nodeId']: n for n in tree}
    val = lambda n, k: (n.get(k) or {}).get('value', '')
    prop = lambda n, name: next((p['value'].get('value') for p in n.get('properties', []) if p['name'] == name), None)
    lines, stats = [], {'unnamed': [], 'roles': {}}
    root = next(n for n in tree if not n.get('parentId'))

    def walk(n, depth):
        role = val(n, 'role')
        name = str(val(n, 'name')).strip()
        if not n.get('ignored') and role not in ('none', 'generic', 'InlineTextBox', 'LineBreak', 'StaticText', 'RootWebArea', 'ListMarker') or (role == 'StaticText' and name):
            if role == 'StaticText':
                lines.append('%s"%s"' % ('  ' * depth, name))
            else:
                extra = []
                v = val(n, 'value')
                if v not in ('', None):
                    extra.append('value: %s' % v)
                d = val(n, 'description')
                if d:
                    extra.append('description: %s' % str(d)[:300])
                for pn in ('checked', 'expanded', 'invalid', 'valuetext', 'level', 'live', 'required'):
                    pv = prop(n, pn)
                    if pv not in (None, '', False) and not (pn == 'invalid' and pv == 'false'):
                        extra.append('%s: %s' % (pn, pv))
                lines.append('%s[%s] %s%s' % ('  ' * depth, role, name, (' (' + '; '.join(extra) + ')') if extra else ''))
                stats['roles'][role] = stats['roles'].get(role, 0) + 1
                if role in ('button', 'checkbox', 'combobox', 'spinbutton', 'textbox', 'link', 'progressbar', 'image', 'img', 'table', 'region', 'slider', 'listbox', 'MenuListPopup') and not name and role != 'MenuListPopup':
                    stats['unnamed'].append(role)
        for c in n.get('childIds', []):
            if c in by:
                walk(by[c], depth + (0 if n.get('ignored') or val(n, 'role') in ('none', 'generic') else 1))

    walk(root, 0)
    # the reading of a text node repeats under its parent's name: keep the tree, drop a text line equal to the line above
    outl = []
    for ln in lines:
        if outl and ln.strip().strip('"') and ln.strip().strip('"') in outl[-1] and ln.strip().startswith('"'):
            continue
        outl.append(ln)
    with open(os.path.join(out, '%s-axtree-%s.txt' % (tag, lang)), 'w', encoding='utf-8') as f:
        f.write('\n'.join(outl) + '\n')
    return outl, stats


lines, stats = ax_reading('en')
check('4.1.2 Name, Role, Value', 'every control, progress bar, image, table and region of the accessibility tree has a name (%d nodes read)' % len(lines),
      not stats['unnamed'], 'unnamed: %s; roles: %s' % (stats['unnamed'], json.dumps(stats['roles'])))
joined = '\n'.join(lines)
need = ['[combobox] Connection speed', '[combobox] Connections', '[combobox] Limit applies to', '[combobox] Procedure to picture', '[spinbutton] Blend time (s)',
        '[button] Play again', '[checkbox] Detailed', '[checkbox] Camera motion', '[combobox] Language']
missing = [x for x in need if x not in joined]
check('1.3.1 Info and Relationships; 3.3.2 Labels or Instructions', 'each control is read with its visible label (label for=id)', not missing, 'not found in the reading: %s' % missing)
img = [l for l in lines if l.strip().startswith('[image]') or l.strip().startswith('[img]')]
check('1.1.1 Non-text Content', 'the 3D view and the timeline chart are images with a text alternative (the scene\'s also says what it shows now)',
      len(img) >= 2 and any('courtyard' in l for l in img) and any('chart' in l.lower() for l in img), [l.strip()[:260] for l in img])
tables = ev('''[...document.querySelectorAll('#panel table')].map((t) => ({ id: t.id, colHeaders: t.querySelectorAll('thead th[scope=col]').length, rowHeaders: t.querySelectorAll('tbody th[scope=row]').length, rows: t.querySelectorAll('tbody tr').length, hidden: !!t.closest('[hidden]') }))''')
tl = next((t for t in tables if t['id'] == 'timeline-table'), None)
check('1.1.1 Non-text Content; 1.3.1', 'the timeline\'s information is also a table: a row per texture with a row header, six column headers', tl and tl['colHeaders'] == 6 and tl['rows'] == 7 and tl['rowHeaders'] == 7, tables)
tlrow = ev('[...document.querySelector("#timeline-table tbody tr").children].map((c) => c.textContent)')
check('1.1.1 Non-text Content', 'the table\'s first row carries the times the chart draws (drawn from its procedure, download, blend, stopped, last work)', tlrow and all(tlrow) and 'not yet' not in ' '.join(tlrow[1:5]), tlrow)
heads = ev('[...document.querySelectorAll("h1,h2,h3")].filter((h) => !h.closest("[hidden]")).map((h) => h.tagName + ": " + h.textContent)')
levels = [int(h[1]) for h in heads]
check('1.3.1; 2.4.6 Headings and Labels', 'one h1, no heading level skipped, every heading has text', levels.count(1) == 1 and all(b - a <= 1 for a, b in zip(levels, levels[1:])) and all(h.split(': ', 1)[1].strip() for h in heads), heads)
check('2.4.2 Page Titled', 'the page has a title that says its topic', 'Procedural Texture Rendering' in (ev('document.title') or ''), ev('document.title'))
check('3.1.1 Language of Page', 'the html element declares the language', ev('document.documentElement.lang') == 'en', ev('document.documentElement.lang'))
optl = ev('[...document.querySelectorAll("#lang option")].map((o) => o.value + "=" + o.lang)')
check('3.1.2 Language of Parts', 'each language\'s own name in the language list carries its language', optl == ['%s=%s' % (l, TAGS[l]) for l in LANGS], optl)
live = ev('[...document.querySelectorAll("[role=status],[role=alert]")].map((e) => (e.id || e.className) + ":" + e.getAttribute("role"))')
check('4.1.3 Status Messages', 'the headline and the messages are status regions; the custom speed\'s error is an alert', 'headline:status' in live and 'msgs:status' in live and 'kbps-error:alert' in live, live)
bars = ev('[...document.querySelectorAll("[role=progressbar]")].filter((b) => !b.closest("[hidden]")).map((b) => [b.getAttribute("aria-label"), b.getAttribute("aria-valuenow"), b.getAttribute("aria-valuetext")])')
check('4.1.2; 1.4.1 Use of Color', 'every bar says its component, its value and its state in words (not by colour alone): %d bars' % len(bars), bars and all(b[0] and b[1] is not None and b[2] for b in bars), bars[:3])
legend = ev('[...document.querySelectorAll(".legend i")].map((i) => { const cs = getComputedStyle(i); return i.className + ": " + Math.round(i.getBoundingClientRect().width) + "x" + Math.round(i.getBoundingClientRect().height) + (cs.backgroundImage !== "none" ? " striped" : "") + (parseFloat(cs.borderTopWidth) > 1.5 ? " outlined" : ""); })')
check('1.4.1 Use of Color', 'the timeline\'s four states differ in shape as well as colour (filled bar, thin line, striped, outlined) and each is named in the legend', len(legend) == 5 and 'striped' in ' '.join(legend) and 'outlined' in ' '.join(legend), legend)
msgs = ev('[...document.querySelectorAll("#msgs div")].map((d) => d.className + ": " + d.textContent)')
check('1.4.1 Use of Color', 'a problem is marked by the word "Problem:" and weight, an information line is plain (this run has: %d lines)' % len(msgs), all((m.startswith('problem: Problem:') or m.startswith('info: ')) for m in msgs), msgs)

# ---------------------------------------------------------------- 3. the keyboard
ev('document.getElementById("timeline-details").open = false; window.scrollTo(0, 0); document.activeElement && document.activeElement.blur()')
order, focus = [], []
FOCUS_JS = r'''(() => { const e = document.activeElement; if (!e || e === document.body) return null; const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
  const cx = Math.min(Math.max(r.left + r.width / 2, 0), innerWidth - 1), cy = Math.min(Math.max(r.top + r.height / 2, 0), innerHeight - 1); const top = document.elementFromPoint(cx, cy);
  return { id: e.id || e.tagName.toLowerCase(), tag: e.tagName.toLowerCase(), outline: cs.outlineStyle + ' ' + cs.outlineWidth + ' ' + cs.outlineColor, width: parseFloat(cs.outlineWidth), style: cs.outlineStyle,
    inView: r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth, onTop: !!top && (top === e || e.contains(top) || top.contains(e) || (top.closest('label') && top.closest('label').contains(e))) }; })()'''
for _ in range(40):
    key('Tab', 'Tab', 9)
    time.sleep(0.12)
    f = ev(FOCUS_JS)
    if not f:
        break
    if f['id'] in order:
        break
    order.append(f['id'])
    focus.append(f)
expected = ev('''[...document.querySelectorAll('a[href], button, select, input, summary, [tabindex]:not([tabindex="-1"])')].filter((e) => { const cs = getComputedStyle(e); return !e.closest('[hidden]') && cs.display !== 'none' && cs.visibility !== 'hidden' && !e.disabled; }).map((e) => e.id || e.tagName.toLowerCase())''')
check('2.1.1 Keyboard; 2.4.3 Focus Order', 'Tab reaches every link and control, in the page\'s reading order (%d stops)' % len(order), order == expected, {'tab order': order, 'controls in the page': expected})
nofocus = [f['id'] for f in focus if not (f['style'] != 'none' and f['width'] >= 2)]
check('2.4.7 Focus Visible', 'every stop shows a focus outline of at least 2 pixels', not nofocus, 'without one: %s; an outline: %s' % (nofocus, focus[2]['outline'] if len(focus) > 2 else focus))
hiddenf = [f['id'] for f in focus if not (f['inView'] and f['onTop'])]
check('2.4.11 Focus Not Obscured (Minimum)', 'every focused stop is inside the window and nothing of ours lies over it', not hiddenf, 'obscured: %s' % hiddenf)
# no trap: Tab from the last stop came round to the first (the walk above ended there); Shift+Tab from a stop in the
# middle goes back one, and from every stop Tab went on
wrapped = (ev(FOCUS_JS) or {}).get('id')
mid = order[len(order) // 2] if order else None
ev('document.getElementById(%s).focus()' % json.dumps(mid))
key('Tab', 'Tab', 9, 8)
time.sleep(0.15)
back = (ev(FOCUS_JS) or {}).get('id')
check('2.1.2 No Keyboard Trap', 'Tab moves on from every stop and leaves the page after the last (or comes round to the first); Shift+Tab goes back one', len(order) > 2 and wrapped in (None, order[0]) and back == order[len(order) // 2 - 1], 'after the last stop: %s; Shift+Tab from %s: %s' % (wrapped or 'out of the page, to the browser', mid, back))
# operate: the speed select by arrow key, the checkbox by Space, the table's disclosure by Enter, the custom speed's error
ev('document.getElementById("speed").focus()')
before = ev('document.getElementById("speed").value + " | " + document.querySelector("#panel table tbody tr:nth-child(2) td:last-child").textContent')
key('ArrowDown', 'ArrowDown', 40)
time.sleep(0.5)
after = ev('document.getElementById("speed").value + " | " + document.querySelector("#panel table tbody tr:nth-child(2) td:last-child").textContent')
check('2.1.1 Keyboard', 'the arrow key changes the detailed speed and marks it as pending', before != after and ev('!document.getElementById("speed-pending").hidden'), '%s -> %s' % (before, after))
check('3.2.2 On Input', 'changing the detailed speed does not reload or move focus; it explicitly waits for Play again', ev('document.activeElement.id') == 'speed' and ev('window.testerResult && true'), ev('document.activeElement.id'))
ev('document.getElementById("detailed").focus()')
key(' ', 'Space', 32)
time.sleep(0.4)
hid = ev('document.getElementById("detail").hidden')
key(' ', 'Space', 32)
time.sleep(0.4)
check('2.1.1 Keyboard', 'Space on "Detailed" hides the component table, Space again shows it', hid is True and ev('document.getElementById("detail").hidden') is False, 'hidden after the first press: %s' % hid)
ev('document.querySelector("#timeline-details summary").focus()')
key('Enter', 'Enter', 13)
time.sleep(0.3)
check('2.1.1 Keyboard', 'Enter on "The timeline as a table" opens it', ev('document.getElementById("timeline-details").open') is True, ev('document.getElementById("timeline-details").open'))
ev('(() => { const s = document.getElementById("speed"); s.value = "custom"; s.dispatchEvent(new Event("change")); })()')
time.sleep(0.3)
ev('(() => { const k = document.getElementById("kbps"); k.value = "0"; k.dispatchEvent(new Event("change")); })()')
time.sleep(0.3)
err = ev('(() => { const e = document.getElementById("kbps-error"), k = document.getElementById("kbps"); return { shown: !e.hidden, text: e.textContent, invalid: k.getAttribute("aria-invalid"), describedby: k.getAttribute("aria-describedby"), label: k.getAttribute("aria-label") }; })()')
check('3.3.1 Error Identification', 'a custom speed of 0 is refused in words beside the field, which is marked invalid and described by the message', err['shown'] and 'above 0' in err['text'] and err['invalid'] == 'true' and 'kbps-error' in err['describedby'].split(), err)
shot('focus')
tg = ev(TARGETS_JS)
check('2.5.8 Target Size (Minimum)', 'every link, button, list, field and checkbox (with its label) is at least 24 by 24 CSS pixels, links inside a sentence apart (%d targets)' % tg['count'], not tg['small'], 'smaller: %s; all: %s' % (tg['small'], tg['all']))

# ---------------------------------------------------------------- 4. small windows, zoom, text spacing
go('speed=none&conns=6&fps=5&detailed=1', wait='window.testerState && testerState().settled && true', t=120)
ev('document.getElementById("measurements").open = true; document.getElementById("timeline-details").open = true')
metrics(320, 640)
time.sleep(1.0)
o = ev(OVERFLOW_JS)
check('1.4.10 Reflow', 'at 320 CSS pixels wide nothing needs sideways scrolling and no text is cut', o['scrollWidth'] <= o['viewport'] + 1 and not o['wide'] and not o['clipped'], o)
shot('reflow-320')
narrow = ws.call('Accessibility.getFullAXTree')['nodes']
roles = {}
for n in narrow:
    r = (n.get('role') or {}).get('value')
    if not n.get('ignored'):
        roles[r] = roles.get(r, 0) + 1
check('1.3.1 Info and Relationships', 'at 320 pixels, where the wide tables are laid out as blocks, they are still tables with rows, headers and cells in the accessibility tree', roles.get('table', 0) >= 3 and roles.get('row', 0) >= 30 and roles.get('columnheader', 0) >= 10 and roles.get('rowheader', 0) >= 12, {k: roles.get(k, 0) for k in ('table', 'row', 'columnheader', 'rowheader', 'cell', 'gridcell')})
tg = ev(TARGETS_JS)
check('2.5.8 Target Size (Minimum)', 'the same at 320 pixels wide', not tg['small'], 'smaller: %s' % tg['small'])
metrics(640, 480, 2)
time.sleep(1.0)
o = ev(OVERFLOW_JS)
check('1.4.4 Resize Text', 'at 200 percent (a 1280 by 960 window: 640 by 480 CSS pixels) nothing is cut and nothing scrolls sideways', o['scrollWidth'] <= o['viewport'] + 1 and not o['wide'] and not o['clipped'], o)
shot('zoom-200')
metrics(1280, 900)
ev('''(() => { const s = document.createElement('style'); s.id = 'spacing-test'; s.textContent = '* { line-height: 1.5 !important; letter-spacing: 0.12em !important; word-spacing: 0.16em !important; } p { margin-bottom: 2em !important; }'; document.head.append(s); })()''')
time.sleep(1.0)
o = ev(OVERFLOW_JS)
check('1.4.12 Text Spacing', 'with line height 1.5, paragraph spacing 2, letter spacing 0.12 and word spacing 0.16 no text is cut', o['scrollWidth'] <= o['viewport'] + 1 and not o['wide'] and not o['clipped'], o)
shot('text-spacing')
ev('document.getElementById("spacing-test").remove()')
ws.call('Emulation.clearDeviceMetricsOverride')

# ---------------------------------------------------------------- scene-first controls and comparisons
metrics(1280,900)
go('speed=dsl8&conns=6&fps=5&motion=0&lang=en&proof=1', wait='window.testerResult && testerState().comparison.ready && true', t=120)
ev('document.getElementById("measurements").open = false; window.scrollTo(0,0)')
check('4.1.3 Status Messages', 'the visible scene state is atomic and a status region',
      ev('document.getElementById("scene-state").getAttribute("role") === "status" && document.getElementById("scene-state").getAttribute("aria-atomic") === "true"'), ev('document.getElementById("scene-state").textContent'))
check('1.4.1 Use of Color', 'each of seven visible surface labels says photograph in words',
      ev('document.querySelectorAll("#surface-states li").length === 7 && [...document.querySelectorAll("#surface-states li")].every(e=>e.textContent.includes("photograph"))'),ev('document.getElementById("surface-states").textContent'))
import hashlib,base64

def scene_png():
    rect=ev('(()=>{const r=document.getElementById("scene").getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,scale:1};})()')
    return base64.b64decode(ws.call('Page.captureScreenshot',{'format':'png','clip':rect})['data'])

a=scene_png()
ev('document.getElementById("compare-hold").focus({preventScroll:true})')
key_down={'type':'keyDown','key':' ','code':'Space','text':' ','windowsVirtualKeyCode':32}
ws.call('Input.dispatchKeyEvent',key_down)
time.sleep(.4)
b=scene_png()
check('1.1.1; 4.1.3', 'held comparison describes the saved computed view in its state, labels and image alternative', ev('document.getElementById("scene-state").textContent.includes("saved computed") && document.getElementById("scene-text").textContent.includes("saved computed") && [...document.querySelectorAll("#surface-states li")].every(e=>e.dataset.state==="procedure")'),ev('document.getElementById("scene-state").textContent'))
held=ev('testerState().comparison.holding && document.getElementById("compare-hold").getAttribute("aria-pressed") === "true"')
ws.call('Input.dispatchKeyEvent',{'type':'keyUp','key':' ','code':'Space','windowsVirtualKeyCode':32})
time.sleep(.4)
c=scene_png()
check('2.1.1; 4.1.2', 'Space holds the saved computed scene, keyup restores the photographs pixel for pixel', held and a!=b and a==c,
      {'photograph':hashlib.sha256(a).hexdigest(),'held':hashlib.sha256(b).hexdigest(),'restored':hashlib.sha256(c).hexdigest()})
ev('document.getElementById("compare-method").focus()')
key('ArrowDown','ArrowDown',40)
time.sleep(.4)
d=scene_png()
check('2.1.1', 'the keyboard selects split comparison, with a named range control', ev('testerState().comparison.method === "split" && !document.getElementById("split-control").hidden && !!document.querySelector("label[for=split-position]")') and d!=a and d!=b, hashlib.sha256(d).hexdigest())
check('1.1.1; 4.1.3', 'split comparison describes both views in words', ev('document.getElementById("scene-state").textContent.includes("left") && document.getElementById("scene-state").textContent.includes("right") && [...document.querySelectorAll("#surface-states li")].every(e=>e.textContent.includes("computed / photograph"))'),ev('document.getElementById("scene-state").textContent'))
ev('document.getElementById("split-position").focus()')
before=ev('document.getElementById("split-position").value')
key('ArrowRight','ArrowRight',39)
check('2.1.1', 'the split position works with arrow keys',ev('document.getElementById("split-position").value')!=before,ev('document.getElementById("split-position").value'))
# Return to Hold, check cancel/blur and verify no procedure work was restarted.
ev('(()=>{const s=document.getElementById("compare-method");s.value="hold";s.dispatchEvent(new Event("change"));})()')
ev('document.getElementById("compare-hold").focus({preventScroll:true})')
subs=ev('testerState().submissions')
ws.call('Input.dispatchKeyEvent',key_down)
ev('document.getElementById("quick-speed").focus({preventScroll:true})')
check('2.5.2 Pointer Cancellation; 2.1.1', 'leaving the hold control releases comparison', not ev('testerState().comparison.holding'), ev('document.getElementById("compare-hold").getAttribute("aria-pressed")'))
ws.call('Input.dispatchKeyEvent',{'type':'keyUp','key':' ','code':'Space','windowsVirtualKeyCode':32})
# Pointer down is reversed by pointer up, including release away from the button.
r=ev('(()=>{const r=document.getElementById("compare-hold").getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()')
ws.call('Input.dispatchMouseEvent',{'type':'mousePressed','x':r['x'],'y':r['y'],'button':'left','buttons':1,'clickCount':1})
pointer_held=ev('testerState().comparison.holding')
ws.call('Input.dispatchMouseEvent',{'type':'mouseReleased','x':1,'y':600,'button':'left','buttons':0,'clickCount':1})
check('2.5.2 Pointer Cancellation', 'pointer down previews and pointer up away from the control reverses it', pointer_held and not ev('testerState().comparison.holding'),{'held':pointer_held,'released':not ev('testerState().comparison.holding')})
check('five-step contract', 'comparison never restarts the procedure player', ev('testerState().playerOff != null && testerState().submissions')==subs, {'submissions':subs,'after':ev('testerState().submissions')})
for width,height in [(360,800),(320,640)]:
    metrics(width,height);time.sleep(.4)
    boxes=ev('Object.fromEntries(["scene","scene-state","quick-speed","restart"].map(id=>{const r=document.getElementById(id).getBoundingClientRect();return [id,[r.top,r.bottom,r.width]];}))')
    check('first screen',f'{width}px: scene, state, speed and Play again are visible without scrolling', all(v[0]>=0 and v[1]<=height for v in boxes.values()),boxes)
metrics(1280,900)
ev('document.getElementById("measurements").open = true')
for id,value in [('conns','2'),('limit','everything'),('blend','cross'),('blendsec','0.7')]:
    ev('(()=>{const e=document.getElementById(%s);e.value=%s;e.dispatchEvent(new Event("change"));})()' % (json.dumps(id),json.dumps(value)))
check('3.3.2', 'every changed deferred setting has a visible pending message', ev('["conns","limit","blend","blendsec"].every(id=>!document.getElementById(id+"-pending").hidden)'),True)
ev('(()=>{const e=document.getElementById("lang");e.value="pt_BR";e.dispatchEvent(new Event("change"));})()')
devtools.wait_for(ws,'document.documentElement.lang === "pt-BR"',20)
pending=ev('({values:["conns","limit","blend","blendsec"].map(id=>document.getElementById(id).value),open:document.getElementById("measurements").open})')
check('settings preservation', 'language preserves all pending values and the open measurements disclosure', pending['values']==['2','everything','cross','0.7'] and pending['open'],pending)
ev('document.getElementById("measurements").open = false; (()=>{const e=document.getElementById("lang");e.value="fr";e.dispatchEvent(new Event("change"));})()')
devtools.wait_for(ws,'document.documentElement.lang === "fr"',20)
check('settings preservation', 'language also preserves a closed disclosure and every pending value', ev('document.getElementById("measurements").open === false && ["conns","limit","blend","blendsec"].map(id=>document.getElementById(id).value).join(",") === "2,everything,cross,0.7"'),ev('document.getElementById("measurements").open'))
# Keep supplied and unknown address parameters across a real replay.
ev('(()=>{const q=new URLSearchParams(location.search);for(const [k,v] of Object.entries({proof:"1",tag:"kept",fps:"5",full:"2048",tile:"512",first:"256",nostop:"0",extra:"keep"}))q.set(k,v);history.replaceState(null,"",location.pathname+"?"+q);})()')
ev('document.getElementById("restart").focus()')
origin=ev('performance.timeOrigin')
key('Enter','Enter',13)
ok=devtools.wait_for(ws, 'performance.timeOrigin !== '+str(origin)+' && window.testerState && testerState().firstFrame != null',120)
params=ev('Object.fromEntries(new URLSearchParams(location.search))')
check('settings preservation', 'Play again keeps proof, frame and unknown URL parameters and applies pending settings', ok and all(params.get(k)==v for k,v in {'proof':'1','tag':'kept','fps':'5','full':'2048','tile':'512','first':'256','nostop':'0','extra':'keep','conns':'2','limit':'everything','blend':'cross','blendsec':'0.7'}.items()),params)
# The first-screen speed choice must actually reload and preserve those same parameters.
ev('document.getElementById("quick-speed").focus()')
origin=ev('performance.timeOrigin')
ev('(()=>{const e=document.getElementById("quick-speed");e.value="dsl8";e.dispatchEvent(new Event("change"));})()')
ok=devtools.wait_for(ws, 'performance.timeOrigin !== '+str(origin)+' && window.testerState && testerState().firstFrame != null',120)
check('3.2.2; first screen', 'the speed choice is advised to replay, really restarts, and retains the proof tag',ok and ev('new URLSearchParams(location.search).get("tag") === "kept"') and ev('!!document.getElementById("quick-hint").textContent'),ev('location.search'))

# ---------------------------------------------------------------- 5. motion
go('speed=dsl8&conns=6&fps=10', wait='window.testerState && testerState().firstFrame && true', t=120)
time.sleep(1.5)
a = ev('testerState().motionClock')
time.sleep(1.0)
b = ev('testerState().motionClock')
ev('(() => { const m = document.getElementById("motion"); m.focus(); })()')
key(' ', 'Space', 32)
time.sleep(0.5)
c = ev('testerState().motionClock')
time.sleep(1.0)
d = ev('testerState().motionClock')
check('2.2.2 Pause, Stop, Hide', 'the camera moves on its own for more than five seconds, so "Camera motion" stops it (by keyboard): its clock runs, then stands', b > a and abs(d - c) < 1 and ev('document.getElementById("motion").checked') is False, 'clock %.0f -> %.0f ms running, %.0f -> %.0f ms stopped' % (a, b, c, d))
media(scheme='light', motion='reduce')
go('speed=dsl8&conns=6&fps=10', wait='window.testerState && testerState().settled && true', t=180)
st = json.loads(ev('JSON.stringify(testerState())'))
# a texture whose picture arrived after it was drawn from its procedure must have blended (a picture that came first has nothing to blend from)
eligible = [x for x in st['textures'] if x['times']['procFirst'] is not None and x['times']['picArrived'] is not None and x['times']['procFirst'] < x['times']['picArrived']]
blended = [x['name'] for x in eligible if x['times']['blendStart'] is not None and x['times']['stop'] is not None and x['times']['stop'] - x['times']['blendStart'] > 1000]
note = ev('[...document.querySelectorAll("#panel p.note")].map((p) => p.textContent).filter((s) => s.includes("reduced motion"))')
check('prefers-reduced-motion (2.3.3 is level AAA; asked by the brief)', 'with reduced motion asked the camera stands still from the start, the panel says why, and every blend still happens',
      st['motion'] is False and st['motionClock'] == 0 and len(eligible) >= 3 and len(blended) == len(eligible) and len(note) == 1, {'motion': st['motion'], 'clock': st['motionClock'], 'blended': '%d of the %d textures drawn from their procedure before their picture came' % (len(blended), len(eligible)), 'note': note})
media(scheme='light', motion='no-preference')

# ---------------------------------------------------------------- 6. the ten languages
langs = {}
for l in LANGS:
    go('speed=none&conns=6&fps=5&lang=' + l, wait='document.getElementById("panel-title") && window.testerState && testerState().firstFrame && true', t=90)
    time.sleep(0.4)
    langs[l] = ev('''({ lang: document.documentElement.lang, title: document.title, h1: document.getElementById('h-title').textContent, panel: document.getElementById('panel-title').textContent,
      restart: document.getElementById('restart').textContent, lead: document.getElementById('h-lead').textContent.slice(0, 60), leftover: document.body.innerText.includes('undefined'),
      messages: testerState().messages.length, chosen: document.getElementById('lang').value })''')
    if l in ('ja', 'de'):
        ax_reading(l)
        metrics(320, 640)
        time.sleep(0.8)
        o = ev(OVERFLOW_JS)
        check('1.4.10 Reflow', 'at 320 pixels wide in %s nothing scrolls sideways and no text is cut' % l, o['scrollWidth'] <= o['viewport'] + 1 and not o['wide'] and not o['clipped'], o)
        shot('reflow-320-' + l)
        ws.call('Emulation.clearDeviceMetricsOverride')
ok = all(langs[l]['lang'] == TAGS[l] and langs[l]['chosen'] == l and not langs[l]['leftover'] for l in LANGS)
distinct = len({langs[l]['restart'] for l in LANGS}) >= 9 and len({langs[l]['panel'] for l in LANGS}) >= 9
check('3.1.1 Language of Page', 'in each of the ten languages the html element declares that language and the panel\'s words are that language\'s', ok and distinct, {l: [langs[l]['lang'], langs[l]['panel'], langs[l]['restart']] for l in LANGS})
# changing the language in the page: by keyboard, without a reload, the focus stays on the list
go('speed=none&conns=6&fps=5&lang=en', wait='document.getElementById("panel-title") && window.testerState && testerState().firstFrame && true', t=90)
ev('window.__mark = 1; document.getElementById("lang").focus()')
key('ArrowDown', 'ArrowDown', 40)
changed = devtools.wait_for(ws, 'document.documentElement.lang === "pl" && document.getElementById("panel-title").textContent', timeout=10)
check('3.2.2 On Input', 'choosing another language changes the page\'s words in place: no reload, and the focus stays on the language list', bool(changed) and ev('window.__mark') == 1 and ev('document.activeElement.id') == 'lang', {'panel title': changed, 'focus': ev('document.activeElement.id'), 'html lang': ev('document.documentElement.lang')})

origin=ev('performance.timeOrigin')
ws.call('Page.navigate',{'url':base+'?speed=none&conns=6&lang=en&fps=5&proof=1#panel'})
ok=devtools.wait_for(ws,'performance.timeOrigin !== '+str(origin)+' && window.testerState && testerState().firstFrame != null',90)
check('address compatibility', 'the old #panel fragment opens the new measurements disclosure', ok and ev('document.getElementById("measurements").open'),ev('location.hash'))

with open(os.path.join(out, tag + '-a11y.json'), 'w', encoding='utf-8') as f:
    json.dump({'checks': checks, 'languages': langs}, f, indent=1, ensure_ascii=False)
with open(os.path.join(out, tag + '-a11y.md'), 'w', encoding='utf-8') as f:
    f.write('| criterion | check | result |\n|---|---|---|\n')
    for c in checks:
        f.write('| %s | %s | %s |\n' % (c['criterion'], c['check'].replace('|', '/'), 'pass' if c['pass'] else 'FAIL: ' + str(c['found'])[:200].replace('|', '/').replace('\n', ' ')))
with open(os.path.join(out, tag + '-console.json'), 'w') as f:
    json.dump(ws.events, f, indent=1)
bad = [c for c in checks if not c['pass']]
print('%d checks, %d failed' % (len(checks), len(bad)), flush=True)
with open(os.path.join(out, 'DONE'), 'w') as f:
    f.write('ok' if not bad else 'failed')
