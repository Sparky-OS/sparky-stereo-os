#!/usr/bin/env python3
"""Generate a static site from the imported source catalogues."""
import argparse
from collections import Counter
from html import escape, unescape
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import posixpath
import re
import shutil
from string import Template
from urllib.parse import quote, unquote, urlsplit
from model import (ROOT, SITE, LANGUAGES, KINDS, SOURCE, bracket_end, dump,
                   extract, load_catalogs, missing_report, page_path, source_anchors)

REPO_URL = 'https://github.com/Sparky-OS/sparky-stereo-os'


def config(origin, base_path):
    parsed = urlsplit(origin)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.path not in ('', '/') or parsed.query or parsed.fragment or parsed.username:
        raise ValueError('--origin must be an HTTP(S) origin without a path')
    if not re.fullmatch(r'/(?:[A-Za-z0-9_-]+/)*', base_path):
        raise ValueError('--base-path must be / or /repository/ (slash-terminated segments)')
    return {'origin': origin.rstrip('/'), 'base_path': base_path}


def expand(value, strings):
    return re.sub(r'\{\{([^}]+)\}\}', lambda m: strings[m.group(1)], value)


def picture_size(path):
    """Width and height of a PNG, GIF, JPEG or sized SVG read from the file itself, or None."""
    data = path.read_bytes()
    if data[:8] == b'\x89PNG\r\n\x1a\n' and data[12:16] == b'IHDR':
        return int.from_bytes(data[16:20], 'big'), int.from_bytes(data[20:24], 'big')
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return int.from_bytes(data[6:8], 'little'), int.from_bytes(data[8:10], 'little')
    if data.lstrip()[:1] == b'<':  # an SVG: its size in pixels, or the shape of its view box
        root = re.search(rb'<svg\b[^>]*>', data[:4096])
        w = root and re.search(rb'\bwidth="(\d+(?:\.\d+)?)(?:px)?"', root.group(0))
        h = root and re.search(rb'\bheight="(\d+(?:\.\d+)?)(?:px)?"', root.group(0))
        if w and h: return round(float(w.group(1))), round(float(h.group(1)))
        box = root and re.search(rb'\bviewBox="[\d.+-]+[ ,]+[\d.+-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', root.group(0))
        return (round(float(box.group(1))), round(float(box.group(2)))) if box else None  # its shape, at least
    if data[:2] == b'\xff\xd8':
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xff: return None
            marker = data[i + 1]
            if marker == 0xff: i += 1; continue
            if 0xd0 <= marker <= 0xd9 or marker == 0x01: i += 2; continue
            if marker in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf):
                return int.from_bytes(data[i + 7:i + 9], 'big'), int.from_bytes(data[i + 5:i + 7], 'big')
            i += 2 + int.from_bytes(data[i + 2:i + 4], 'big')
    return None


def counted_figures():
    """Numbers for the trial figures row, each counted now from the repository's own record, never typed.

    Returns (anchor of the home page's existing link that names the thing, count, record, counted unit).
    """
    merges = (ROOT/'docs/upstream-merges.md').read_text(encoding='utf-8').splitlines()
    start, end = merges.index('**Merged:**'), merges.index('**In review:**')
    programs = [l for l in (ROOT/'docs/programs.md').read_text(encoding='utf-8').splitlines()
                if re.match(r'\*\*[^*]+\*\*(?:,| and| \()', l)]
    branches = [l for l in (ROOT/'docs/kde-branches.md').read_text(encoding='utf-8').splitlines()
                if l.startswith('| ') and not re.match(r'\| *(Project|-)', l)]
    return [('programs-the-edition-changes-for-stereo-3d-and-deep-colour', len(programs), 'docs/programs.md',
             'paragraphs that open with a program\'s name, none marked Coming or Planned'),
            ('our-branches-on-kdes-gitlab', len(branches), 'docs/kde-branches.md', 'rows of the table'),
            ('merged-outside-sparky-stereo', sum(l.startswith('- ') for l in merges[start:end]), 'docs/upstream-merges.md',
             'entries between "Merged:" and "In review:"; one entry can hold several pull requests')]


CHAIN = ('<div class="chain" data-added="chain" aria-hidden="true">'
         '<span class="chain-program"><i>&nbsp;</i></span><b>→</b>'
         '<span class="chain-pair"><i>&nbsp;</i><i>&nbsp;</i></span><b>→</b>'
         '<span class="chain-desktop"><i>&nbsp;</i><i>&nbsp;</i><i>&nbsp;</i></span><b>→</b>'
         '<span class="chain-screens"><i>&nbsp;</i><i>&nbsp;</i><i>&nbsp;</i></span></div>')


class Renderer:
    def __init__(self, catalogs, cfg):
        self.catalogs = catalogs
        self.cfg = cfg
        self.assets = {}
        self.asset_paths = {}
        self.routes = {source: (lang, kind) for lang, c in catalogs.items()
                       for kind, d in c['pages'].items() for source in [d['source']]}
        self.external_assets = json.loads((SITE/'assets.json').read_text())

    def url(self, path):
        return self.cfg['base_path'] + quote(path, safe='/')

    def canonical(self, lang, kind):
        path = page_path(lang, kind)
        if path.endswith('index.html'): path = path[:-10]
        return self.cfg['origin'] + self.url(path)

    def asset(self, target, source):
        if urlsplit(target).scheme:
            entry = self.external_assets[target]
            if entry.get('text_only'):
                return None
            path = SITE / entry['file']
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError('Changed downloaded asset: ' + target)
            dest = 'assets/' + path.name
        else:
            rel = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(target)))
            path = ROOT / rel
            if not path.resolve().is_relative_to(ROOT): raise ValueError('Asset outside checkout')
            if not path.is_file(): raise ValueError('Missing asset: ' + rel)
            dest = 'assets/media/' + rel
        self.assets[dest] = path
        self.asset_paths[self.url(dest)] = path
        return self.url(dest)

    def link(self, target, source):
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc:
            if parsed.scheme not in ('http', 'https', 'mailto'): raise ValueError('Unsupported link: ' + target)
            return target
        if not parsed.path:
            return '#' + quote(unquote(parsed.fragment), safe='-_.')
        rel = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(parsed.path)))
        if rel in self.routes:
            lang, kind = self.routes[rel]
            result = self.url(page_path(lang, kind))
        else:
            path = ROOT/rel
            if not path.exists(): raise ValueError(f'{source}: missing linked source {target}')
            # Documents outside this preview remain links to their real GitHub pages.
            result = REPO_URL + ('/tree/main/' if path.is_dir() else '/blob/main/') + quote(rel, safe='/')
        if parsed.query: result += '?' + parsed.query
        if parsed.fragment: result += '#' + quote(unquote(parsed.fragment), safe='-_.')
        return result

    def image(self, src, alt, source, width=None):
        url = self.asset(src, source)
        if url is None:
            return '<span class="badge-link">' + escape(alt) + '</span>'
        cls = 'screenshot' if not urlsplit(src).scheme else 'badge'
        # GitHub permits percentage widths in its Markdown HTML. HTML itself
        # requires integer dimensions; responsive sizing belongs in the CSS.
        # Each picture says its real size, read from its file, so the page keeps
        # its place before it arrives; a width the source gives in pixels wins.
        dims = ''; size = picture_size(self.asset_paths[url])
        if width and width.isdigit():
            dims = f' width="{width}"' + (f' height="{round(int(width) * size[1] / size[0])}"' if size else '')
        elif size:
            dims = f' width="{size[0]}" height="{size[1]}"'
        return f'<img class="{cls}" src="{escape(url, quote=True)}" alt="{escape(alt, quote=True)}"{dims} loading="lazy" decoding="async">'

    def inline(self, value, source):
        parts = []; i = 0
        while i < len(value):
            if value[i] == '<':
                end = value.find('>', i)
                tag = value[i:end + 1]
                parser = TagParser(); parser.feed(tag)
                if tag.startswith('</'):
                    name = tag[2:-1].strip()
                    if name in ('a', 'picture'): parts.append('</a>' if name == 'a' else '')
                    else: raise ValueError('Unsupported HTML close tag: ' + tag)
                else:
                    name, attrs = parser.tag, parser.attrs
                    if name == 'a':
                        if 'href' in attrs:
                            parts.append('<a href="' + escape(self.link(attrs['href'], source), quote=True) + '">')
                        elif 'id' in attrs or 'name' in attrs:
                            parts.append('<a id="' + escape(attrs.get('id',attrs.get('name')),quote=True) + '">')
                        else: raise ValueError('Anchor with no destination')
                    elif name == 'img': parts.append(self.image(attrs['src'], attrs['alt'], source, attrs.get('width')))
                    elif name in ('picture', 'source'): pass  # Same badge becomes a labelled link; no remote theme request.
                    elif name == 'br': parts.append('<br>')
                    else: raise ValueError('Unsupported HTML: ' + tag)
                i = end + 1; continue
            is_image = value.startswith('![', i)
            start = i + 1 if is_image else i
            if value[start:start + 1] == '[':
                end = bracket_end(value, start)
                if value[end + 1:end + 2] == '(':
                    close = bracket_end(value, end + 1, '(', ')')
                    label, target = value[start + 1:end], value[end + 2:close]
                    if is_image:
                        parts.append(self.image(target, label, source))
                    else:
                        # The language's native name labels existing flag-only sign-up links.
                        native = next(((tag, name) for tag, flag, name in LANGUAGES.values() if label == flag), None)
                        attributes = ''
                        if native:
                            attributes = ' lang="' + native[0] + '" aria-label="' + escape(label + ' ' + native[1],quote=True) + '"'
                        parts.append('<a href="' + escape(self.link(target, source),quote=True) + '"' + attributes + '>' + self.inline(label, source) + '</a>')
                    i = close + 1; continue
            delimiter = next((d for d in ('**', '*', '`') if value.startswith(d, i)), None)
            if delimiter:
                end = value.find(delimiter, i + len(delimiter))
                if end < 0: raise ValueError('Unclosed inline delimiter: ' + value[i:i+60])
                tag = {'**':'strong', '*':'em', '`':'code'}[delimiter]
                raw = value[i + len(delimiter):end]
                content = escape(raw) if delimiter == '`' else self.inline(raw, source)
                parts.append(f'<{tag}>' + content + f'</{tag}>'); i = end + len(delimiter); continue
            end = i + 1
            while end < len(value) and value[end] not in '<[!*`': end += 1
            parts.append(escape(unescape(value[i:end]))); i = end
        return ''.join(parts)

    def figures(self, catalog, source):
        """A trial row under the first screen: a counted number beside a label this language's page already has."""
        items = []
        for anchor, count, _, _ in counted_figures():
            label = next(v for k, v in catalog['strings'].items()
                         if k.startswith('home.more-about-the-edition.item') and f'<a id="{anchor}"></a>' in v)
            link = self.inline(expand(label.replace(f'<a id="{anchor}"></a>', ''), catalog['strings']), source)
            items.append(f'<li><strong>{count}</strong> {link}</li>')
        return '<ul class="figures" data-added="figures">' + ''.join(items) + '</ul>'

    def content(self, catalog, kind):
        doc = catalog['pages'][kind]; source = doc['source']; strings = catalog['strings']
        # The home page's first screen is one group: the opening, then the drawing
        # with the pictures and their caption, then status and next step, in the
        # source's order. The stylesheet sets the group in two columns on a wide screen.
        output = ['<div class="first"><div class="opening-copy">'] if kind == 'home' else []; footer = []; active = output; list_type = None; used_ids = set()
        if kind == 'home' and not all(f'home.intro.paragraph0{n}' in strings for n in range(1, 8)):
            raise ValueError(f'{source}: the first screen needs its seven opening paragraphs')
        def anchor(value):
            if value in used_ids: return ''
            used_ids.add(value)
            return '<a id="' + escape(value,quote=True) + '"></a>'
        def close_list():
            nonlocal list_type
            if list_type: active.append('</' + list_type + '>'); list_type = None
        for b in doc['blocks']:
            typ = b['type']
            if typ == 'anchors':
                close_list()
                active.append(''.join(anchor(x) for x in re.findall(r'(?:id|name)="([^"]+)"',b['raw'])))
                continue
            if b.get('within'): continue  # drawn inside its paragraph, at its source line
            key = b['key']; value = expand(strings[key], strings)
            if b.get('inserts'):
                # A later source addition keeps its own key and its place in the paragraph.
                lines = value.split('\n')
                for after, inserted in reversed(b['inserts']):
                    lines.insert(after, expand(strings[inserted], strings))
                value = '\n'.join(lines)
            if typ == 'heading':
                close_list()
                if kind == 'home' and '.credit.' in key: active = footer
                aliases = [b['id'], b['english_id']]
                lead = ''.join(anchor(x) for x in dict.fromkeys(aliases))
                level = b['level']
                active.append(lead + f'<h{level}>' + self.inline(value, source) + f'</h{level}>')
                continue
            if typ in ('item', 'step'):
                desired = 'ol' if typ == 'step' else 'ul'
                if list_type != desired:
                    close_list(); list_type = desired
                    cls = ' class="doors"' if kind == 'home' and '.intro.' in key else (' class="more-links"' if kind == 'home' and '.more-about-the-edition.' in key else '')
                    active.append('<' + desired + cls + '>')
                paragraphs = value.split('\n\n')
                inner = self.inline(paragraphs[0],source)
                inner += ''.join('<p>' + self.inline(p,source) + '</p>' for p in paragraphs[1:])
                active.append('<li>' + inner + '</li>')
            else:
                close_list()
                if typ == 'table':
                    rows = value.splitlines()
                    # The source uses an empty header for this two-column list
                    # of maintainers. Use a definition list, not an empty table.
                    active.append('<dl class="maintainers">')
                    for row in rows[2:]:
                        cells = [x.strip() for x in row.strip('|').split('|')]
                        if len(cells) != 2: raise ValueError('Unsupported table shape')
                        active.append('<dt>' + self.inline(cells[0],source) + '</dt><dd>' + self.inline(cells[1],source) + '</dd>')
                    active.append('</dl>')
                elif typ == 'quote':
                    active.append('<blockquote><p>' + self.inline(value,source) + '</p></blockquote>')
                elif typ == 'paragraph':
                    if kind == 'home' and key == 'home.intro.paragraph03':
                        # The drawing's place holds no picture of its own: where no drawing
                        # can run, the stylesheet removes the place and the front page's own
                        # picture, which follows, is the first thing after the opening.
                        active.append('</div><div class="art"><div class="depth-decoration" aria-hidden="true"><canvas aria-hidden="true"></canvas></div>')
                    css = ''
                    if kind == 'home' and '.intro.paragraph' in key:
                        css = {'01':'lead intro-copy','02':'intro-copy','03':'hero','04':'gallery','05':'caption','06':'status','07':'next-step'}.get(key[-2:], '')
                    if '<img ' in value and not css: css = 'gallery' if value.count('<img ')>1 else 'hero'
                    rendered = self.inline(value,source)
                    if kind == 'home' and key == 'home.how-it-works.paragraph01':
                        active.append(CHAIN)  # a wordless strip over the section's own sentence
                    if kind == 'home' and key == 'home.intro.paragraph03':
                        rendered = rendered.replace(' loading="lazy"', '')  # the first screen's picture loads at once
                    active.append('<div class="'+css+'">' + rendered + '</div>' if css in ('hero','gallery') else '<p' + (f' class="{css}"' if css else '') + '>' + self.inline(value,source) + '</p>')
                    if kind == 'home' and key in ('home.intro.paragraph05', 'home.intro.paragraph07'):
                        active.append('</div>')  # the caption ends the pictures' column; the next step ends the first screen
                    if kind == 'home' and key == 'home.intro.paragraph07':
                        active.append(self.figures(catalog, source))
                else: raise ValueError('Unsupported block: ' + typ)
        close_list()
        if kind != 'home':
            credit = expand(strings['home.credit.paragraph01'], strings).split('\n',1)[0]
            footer.append('<p>' + self.inline(credit,catalog['pages']['home']['source']) + '</p>')
        # English aliases supplement rather than replace every original anchor.
        # IDs inside body strings must not duplicate heading aliases.
        text = '\n'.join(output); foot = '\n'.join(footer)
        seen = set()
        def dedupe(m):
            value = m.group(1)
            if value in seen: return ''
            seen.add(value); return m.group(0)
        text = re.sub(r'<a id="([^"]+)"></a>',dedupe,text)
        foot = re.sub(r'<a id="([^"]+)"></a>',dedupe,foot)
        return text, foot

    def description(self, catalog, kind):
        """The page's own first sentence as its description: the source's words, without their markup."""
        lines = expand(catalog['strings'][f'{kind}.intro.paragraph01'], catalog['strings']).split('\n')
        first = lines[0]
        for line in lines[1:]:  # a bold lead that closes on a later line is one lead
            if not first.startswith('**') or first.count('**') % 2 == 0: break
            first += ' ' + line
        first = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', re.sub(r'<[^>]+>', '', first))
        return escape(unescape(first.replace('**', '').replace('`', '')).strip(), quote=True)

    def render(self, lang, kind):
        catalog = self.catalogs[lang]
        title = expand(catalog['strings'][f'{kind}.intro.heading01'],catalog['strings'])
        body, footer = self.content(catalog,kind)
        document = Template((SITE/'templates'/f'{kind}.html').read_text()).substitute(body=body,footer=footer)
        available = [l for l,c in self.catalogs.items() if kind in c['pages']]
        menu = ['<details class="lang"><summary>' + catalog['strings']['site.language.flag'] + ' 🌐🗣️<span class="visually-hidden"> ' + catalog['strings']['site.language.name'] + '</span></summary><ul>']
        alternates = []
        for target in available:
            tag = LANGUAGES[target][0]
            flag = self.catalogs[target]['strings']['site.language.flag']
            name = self.catalogs[target]['strings']['site.language.name']
            current = ' aria-current="page"' if target == lang else ''
            menu.append(f'<li><a href="{self.url(page_path(target,kind))}" hreflang="{tag}" lang="{tag}"{current}>{flag} {name}</a></li>')
            alternates.append(f'<link rel="alternate" hreflang="{tag}" href="{self.canonical(target,kind)}">')
        menu.append('</ul></details>')
        alternates.append(f'<link rel="alternate" hreflang="x-default" href="{self.canonical("en",kind)}">')
        return Template((SITE/'templates/shell.html').read_text()).substitute(
            lang=LANGUAGES[lang][0],title=escape(title),description=self.description(catalog,kind),kind=kind,document=document,
            home=self.url(page_path(lang,'home')),wordmark=self.url(catalog['strings']['site.wordmark.image']),wordmark_alt=escape(catalog['strings']['site.wordmark.alt'],quote=True),
            stylesheet=self.url('assets/style.css'),canonical=self.canonical(lang,kind),
            alternates='\n'.join(alternates),menu='\n'.join(menu),
            script=('<script defer src="' + self.url('assets/depth.js') + '"></script>') if kind == 'home' else '')


class TagParser(HTMLParser):
    def handle_starttag(self, tag, attrs): self.tag, self.attrs = tag, dict(attrs)


def build(output, cfg):
    catalogs = load_catalogs()
    if catalogs != extract(): raise ValueError('Stale or edited catalogues; run site/import_strings.py and review')
    if json.loads((SITE/'missing.json').read_text()) != missing_report(catalogs):
        raise ValueError('Missing-key inventory is stale')
    # Render and validate all inputs before changing a previous output folder.
    renderer = Renderer(catalogs,cfg)
    pages = {page_path(lang,kind): renderer.render(lang,kind)
             for lang,c in catalogs.items() for kind in c['pages']}
    links = ''.join(f'<li><a href="{renderer.url(page_path(l,"home"))}" lang="{tag}" hreflang="{tag}">{flag} {name}</a></li>' for l,(tag,flag,name) in LANGUAGES.items())
    document = Template((SITE/'templates/404.html').read_text()).substitute(links=links)
    pages['404.html'] = Template((SITE/'templates/shell.html').read_text()).substitute(
        lang='en',title='404 · Sparky Stereo OS',description=renderer.description(catalogs['en'],'home'),kind='error',document=document,
        home=renderer.url('index.html'),wordmark=renderer.url(catalogs['en']['strings']['site.wordmark.image']),wordmark_alt=escape(catalogs['en']['strings']['site.wordmark.alt'],quote=True),
        stylesheet=renderer.url('assets/style.css'),canonical=cfg['origin']+renderer.url('404.html'),
        alternates='',menu='',script='')
    if output.exists():
        if not (output/'.site-build.json').exists(): raise ValueError('Refusing to replace a folder not created by this generator')
        for child in output.iterdir():
            if child.is_dir(): shutil.rmtree(child)
            else: child.unlink()
    output.mkdir(parents=True, exist_ok=True)
    for path,text in pages.items():
        dest = output/path; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text(text,encoding='utf-8')
    renderer.assets['assets/wordmark.png'] = SITE/'assets/wordmark.png'
    renderer.assets['assets/style.css'] = SITE/'style.css'
    renderer.assets['assets/depth.js'] = SITE/'depth.js'
    for path,src in renderer.assets.items():
        dest = output/path; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dest)
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += '\n'.join('<url><loc>'+escape(renderer.canonical(l,k))+'</loc></url>' for l,c in catalogs.items() for k in c['pages'])
    (output/'sitemap.xml').write_text(sitemap+'\n</urlset>\n')
    (output/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+cfg['origin']+renderer.url('sitemap.xml')+'\n')
    (output/'.nojekyll').touch()
    dump(output/'.site-build.json',cfg)
    print(f'PASS: built {len(pages)} HTML pages, {len(renderer.assets)} local assets in {output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=SITE/'_build')
    parser.add_argument('--origin',default='http://localhost:8548')
    parser.add_argument('--base-path',default='/')
    args = parser.parse_args()
    build(args.output.resolve(), config(args.origin,args.base_path))

if __name__ == '__main__': main()
