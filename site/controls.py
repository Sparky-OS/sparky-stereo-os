#!/usr/bin/env python3
"""Prove that the gates reject missing translations and corrupted output."""
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from build import build, config
from check import check
from model import SITE, load_catalogs


def must_fail(label, action, expected):
    try:
        with redirect_stdout(io.StringIO()) as capture: action()
    except (ValueError,KeyError) as error:
        message=capture.getvalue()+str(error)
        if expected not in message:raise AssertionError(label+': failed for another reason: '+message)
        print('PASS negative control:',label)
    else:raise AssertionError(label+': corruption was accepted')


def main():
    with tempfile.TemporaryDirectory(prefix='controls-',dir=SITE) as folder:
        output=Path(folder)/'site'
        cfg=config('https://example.invalid','/sparky-stereo-os/')
        catalogs=load_catalogs()
        for label,change in [
            ('missing translated key',lambda c:c['pt_BR']['strings'].pop('home.intro.paragraph01')),
            ('English substituted for Portuguese',lambda c:c['pt_BR']['strings'].__setitem__('home.intro.paragraph01',c['en']['strings']['home.intro.paragraph01']))]:
            modified=copy.deepcopy(catalogs);change(modified)
            with patch('build.load_catalogs',return_value=modified):
                must_fail(label,lambda:build(output,cfg),'Stale or edited catalogues')
        with redirect_stdout(io.StringIO()):build(output,cfg);check(output,tidy=False)
        cases=[
            ('broken relative link','index.html','href="/sparky-stereo-os/edition-in-detail.html#seen-in-3d"','href="/sparky-stereo-os/missing.html"','broken local link'),
            ('lost README anchor','index.html','id="science-and-engineering"','id="lost-science-anchor"','lost anchor'),
            ('English in built Portuguese','pt-BR/index.html','<h1>Sparky Stereo OS</h1>','<h1>Create and explore in 3D</h1>','generated content differs'),
            ('outside image request','index.html','src="/sparky-stereo-os/assets/wordmark.png"','src="https://example.invalid/tracker.png"','remote resource'),
            ('insufficient text contrast','assets/style.css','--text: #262423;','--text: #eeeeee;','light text/page'),
        ]
        for label,path,old,new,expected in cases:
            target=output/path;original=target.read_text()
            assert old in original,label
            target.write_text(original.replace(old,new,1))
            try:must_fail(label,lambda:check(output,tidy=False),expected)
            finally:target.write_text(original)
        with redirect_stdout(io.StringIO()):check(output,tidy=False)
        print('PASS: seven negative controls; valid project-base output restored')

if __name__=='__main__':main()
