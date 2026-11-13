#!/usr/bin/env python3
"""Check catalogue provenance, HTML, links, anchors, assets and accessibility structure."""
import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
from build import Renderer
from model import ROOT, SITE, LANGUAGES, extract, load_catalogs, missing_report, page_path, source_anchors


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = []; self.refs = []; self.resources = []; self.headings = []
        self.errors = []; self.anchors = []; self.stack = []; self.lang = None
        self.menu = []; self.alternates = []; self.canonical = []
        self.feed(text)
    def handle_starttag(self, tag, attributes):
        a = dict(attributes)
        if 'id' in a: self.ids.append(a['id'])
        if tag == 'html': self.lang = a.get('lang')
        if re.fullmatch('h[1-6]',tag): self.headings.append(int(tag[1]))
        if tag in ('iframe','object','embed','form','video','audio'): self.errors.append('unexpected active element '+tag)
        if any(k.startswith('on') or k == 'style' for k in a): self.errors.append('inline script/style')
        if tag == 'a' and 'href' in a:
            self.refs.append(a['href']); self.anchors.append({'attrs':a,'text':''})
            self.stack.append(self.anchors[-1])
            if 'hreflang' in a:
                self.menu.append(a)
                if a.get('lang') != a['hreflang']: self.errors.append('link language differs from hreflang')
        if tag == 'script':
            if not a.get('src','').endswith('/assets/depth.js') or 'defer' not in a: self.errors.append('unexpected script')
            self.resources.append(a.get('src',''))
        if tag == 'canvas' and a.get('aria-hidden') != 'true': self.errors.append('unlabelled canvas')
        if tag == 'img':
            if not a.get('alt') and a.get('role') != 'presentation': self.errors.append('image has no useful alternative')
            if self.stack: self.stack[-1]['text'] += a.get('alt','')
            self.resources.append(a.get('src',''))
        if 'srcset' in a: self.errors.append('unexpected srcset needs explicit resource audit')
        if tag == 'link':
            rel = a.get('rel')
            if rel in ('stylesheet','icon'): self.resources.append(a['href'])
            elif rel == 'alternate': self.alternates.append(a)
            elif rel == 'canonical': self.canonical.append(a['href'])
            else: self.errors.append('unexpected resource link '+str(rel))
        if tag == 'meta' and a.get('http-equiv','').lower() in ('refresh','set-cookie'): self.errors.append('refresh or cookie')
    def handle_endtag(self, tag):
        if tag == 'a' and self.stack: self.stack.pop()
    def handle_data(self, text):
        if self.stack: self.stack[-1]['text'] += text


def local_target(url, current, output, cfg):
    p = urlsplit(url)
    if p.scheme or p.netloc: return None
    if p.path.startswith('/'):
        if not p.path.startswith(cfg['base_path']): raise ValueError('URL escapes base path: '+url)
        target = output / unquote(p.path[len(cfg['base_path']):])
    else: target = current.parent / unquote(p.path)
    if not p.path: target = current
    if target.is_dir(): target /= 'index.html'
    target = target.resolve()
    if not target.is_relative_to(output.resolve()): raise ValueError('URL escapes built folder: '+url)
    return target, unquote(p.fragment)


def contrast(a,b):
    def luminance(v):
        cs = [int(v[i:i+2],16)/255 for i in (1,3,5)]
        cs = [x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4 for x in cs]
        return sum(a*b for a,b in zip(cs,(.2126,.7152,.0722)))
    x,y = sorted((luminance(a),luminance(b)))
    return (y+.05)/(x+.05)


def check(output, report_dir=None, tidy=True):
    cfg = json.loads((output/'.site-build.json').read_text())
    catalogs = load_catalogs(); errors = []; notes = []
    if catalogs != extract(): errors.append('catalogue differs from source (including missing or English-substituted strings)')
    if missing_report(catalogs) != json.loads((SITE/'missing.json').read_text()): errors.append('unreported missing/extra key')
    renderer = Renderer(catalogs,cfg)
    paths = sorted(output.rglob('*.html'))
    pages = {p:Page(p.read_text()) for p in paths}
    expected = {page_path(l,k) for l,c in catalogs.items() for k in c['pages']} | {'404.html'}
    if {p.relative_to(output).as_posix() for p in paths} != expected: errors.append('built page set differs from available source languages')
    anchor_rows = ['source\theading_or_anchor\tsite_target']
    source_rows = ['source\tkey\tline\toutput']
    for lang,c in catalogs.items():
        for kind,doc in c['pages'].items():
            path = output/page_path(lang,kind)
            if not path.exists(): continue
            if path.read_text() != renderer.render(lang,kind): errors.append(str(path)+': generated content differs from its own language catalogue')
            page = pages[path]
            if page.lang != LANGUAGES[lang][0]: errors.append(str(path)+': wrong page language')
            available = {LANGUAGES[l][0] for l,v in catalogs.items() if kind in v['pages']}
            if {x['hreflang'] for x in page.menu} != available: errors.append(str(path)+': language list differs from source page availability')
            if {x['hreflang'] for x in page.alternates} != available | {'x-default'}: errors.append(str(path)+': alternate set differs')
            if page.canonical != [renderer.canonical(lang,kind)]: errors.append(str(path)+': wrong canonical')
            for a in page.alternates:
                target_lang = next((l for l,(tag,_,_) in LANGUAGES.items() if tag==a['hreflang']), 'en')
                if a['href'] != renderer.canonical(target_lang,kind): errors.append(str(path)+': alternate wrong page')
            for _,ident,heading in source_anchors((ROOT/doc['source']).read_text()):
                if ident not in page.ids: errors.append(f'{doc["source"]}: lost anchor {ident}')
                anchor_rows.append('\t'.join([doc['source'],heading+' #'+ident,page_path(lang,kind)+'#'+ident]))
            for b in doc['blocks']:
                if 'key' in b: source_rows.append(f'{doc["source"]}\t{b["key"]}\t{b["line"]}\t{page_path(lang,kind)}')
    references = resources = 0
    for path,page in pages.items():
        errors.extend(f'{path.relative_to(output)}: {e}' for e in page.errors)
        dup = [k for k,n in Counter(page.ids).items() if n>1]
        if dup: errors.append(str(path)+': duplicate IDs '+str(dup))
        if page.headings.count(1) != 1: errors.append(str(path)+': needs one h1')
        if any(b>a+1 for a,b in zip(page.headings,page.headings[1:])): errors.append(str(path)+': heading skips a level')
        for link in page.anchors:
            if not link['text'].strip() and not link['attrs'].get('aria-label'): errors.append(str(path)+': unnamed link')
        for ref in page.refs + page.resources:
            local = local_target(ref,path,output,cfg)
            if local is None:
                if ref in page.resources: errors.append(str(path)+': remote resource '+ref)
                continue
            target,fragment = local; references += 1
            if not target.is_file(): errors.append(str(path)+': broken local link '+ref)
            elif fragment and target.suffix=='.html' and fragment not in pages[target].ids: errors.append(str(path)+': broken anchor '+ref)
        resources += len(page.resources)
    css = (output/'assets/style.css').read_text()
    if re.search(r'url\s*\(|@import|@font-face',css,re.I): errors.append('CSS resource reference requires review')
    for svg in output.rglob('*.svg'):
        tree = ET.parse(svg)
        for el in tree.iter():
            tag = el.tag.split('}')[-1]
            if tag in ('script','foreignObject','image','use'): errors.append(str(svg)+': active/referencing SVG element '+tag)
            for key,value in el.attrib.items():
                if key.split('}')[-1] in ('href','src') and not value.startswith('#'): errors.append(str(svg)+': external SVG reference')
                if key.startswith('on') or re.search(r'url\s*\(\s*["\']?https?:',value): errors.append(str(svg)+': active SVG attribute')
    # Read actual CSS tokens, rather than retesting copied expected colours.
    palettes = re.findall(r':root\s*\{([^}]+)\}',css,re.S)
    for theme,body in zip(('light','dark'),palettes):
        tokens = dict(re.findall(r'--([a-z]+):\s*(#[0-9a-f]{6});',body))
        for fg in ('text','link','focus','border'):
            for bg in ('page','surface'):
                ratio = contrast(tokens[fg],tokens[bg]); threshold = 4.5 if fg in ('text','link') else 3
                if ratio < threshold: errors.append(f'{theme} {fg}/{bg}: {ratio:.2f} < {threshold}')
                notes.append(f'{theme} {fg}/{bg}: {ratio:.2f}:1 (minimum {threshold})')
    tidy_logs = []
    if tidy:
        version = subprocess.run(['tidy','-v'],capture_output=True,text=True,check=True).stdout.strip()
        for path in paths:
            run = subprocess.run(['tidy','-q','-e','-utf8',str(path)],capture_output=True,text=True)
            lines = run.stderr.splitlines()
            # Tidy 5.8 predates these standard HTML/ARIA attributes. Keep its
            # raw diagnostics and allow only these exact versioned warnings.
            unexpected = [x for x in lines if not re.fullmatch(r'line \d+ column \d+ - Warning: <(?:a|img)> proprietary attribute "(?:aria-current|decoding)"',x)]
            if unexpected or run.returncode not in (0,1): errors.append(f'{path.name}: tidy: '+str(unexpected))
            tidy_logs.extend([str(path.relative_to(output)),run.stderr])
        notes.append(f'{version}: {len(paths)} documents, no errors; recognized obsolete-checker attribute warnings retained')
    home = output/'index.html'; home_page=pages[home]
    home_files={home}
    for ref in home_page.resources:
        local=local_target(ref,home,output,cfg)
        if local:home_files.add(local[0])
    weight=sum(p.stat().st_size for p in home_files)
    script_bytes=(output/'assets/depth.js').stat().st_size
    if script_bytes>100000: errors.append('decoration script exceeds 100 KB')
    notes.append(f'English home: {home.stat().st_size} HTML bytes; {weight-script_bytes} bytes with script disabled; {weight} bytes with decoration script ({script_bytes} bytes); all images and CSS, uncompressed, cold cache')
    notes += [f'{len(paths)} HTML pages; {references} local references resolved; {resources} resource references all local',
              f'{len(anchor_rows)-1} original headings/explicit anchors retained; {len(source_rows)-1} source block mappings',
              'Catalogues match original Markdown; missing keys enumerated; each built page equals the rendering of its own catalogue (the words against the source: verify_text.py)',
              'Language menus, alternates, canonicals, heading order, link names and image alternatives checked']
    if report_dir:
        report_dir.mkdir(parents=True,exist_ok=True)
        (report_dir/'anchors.tsv').write_text('\n'.join(anchor_rows)+'\n')
        (report_dir/'source-map.tsv').write_text('\n'.join(source_rows)+'\n')
        (report_dir/'tidy.txt').write_text('\n'.join(tidy_logs))
        (report_dir/'checks.txt').write_text('\n'.join(notes+errors)+'\n')
    for note in notes: print(note)
    if errors:
        for error in errors: print('FAIL:',error)
        raise ValueError(f'{len(errors)} checks failed')
    print('PASS: static checks')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=SITE/'_build')
    parser.add_argument('--report-dir',type=Path)
    parser.add_argument('--skip-tidy',action='store_true',help='Only for controls; does not establish HTML validity')
    args=parser.parse_args()
    check(args.output.resolve(),args.report_dir,not args.skip_tidy)

if __name__=='__main__': main()
