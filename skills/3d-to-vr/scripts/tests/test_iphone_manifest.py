#!/usr/bin/env python3
"""Offline synthetic IPAs only: no phone, account, network or xtool execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import plistlib
import tempfile
import unittest
from unittest.mock import patch
import subprocess
import zipfile

HERE=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
join=module('join','iphone-manifest.py');renew=module('renew','iphone-renew.py')

class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.out=self.root/'private/apps.json';self.out.parent.mkdir()
        self.commit='a'*40
        for role,(folder,bundle) in join.ROLES.items():
            d=self.root/folder;d.mkdir();ipa=d/(role+'.ipa')
            with zipfile.ZipFile(ipa,'w') as z:z.writestr('Payload/Test.app/Info.plist',plistlib.dumps({'CFBundleIdentifier':bundle}))
            record={'commit':self.commit,'workflow_commit':self.commit,'apps':[{'role':role,'path':ipa.name,'bundle_id':bundle,'sha256':hashlib.sha256(ipa.read_bytes()).hexdigest()}]}
            (d/(role+'-artifact.json')).write_text(json.dumps(record))
    def assemble(self):
        # Deliberately synthetic identifier; never a real device.
        result=join.assemble(self.root,self.commit,'0'*40,self.out)
        self.out.write_text(json.dumps(result));return renew.prepare(self.out)
    def change(self,fn):
        p=self.root/'cardboard/cardboard-artifact.json';r=json.loads(p.read_text());fn(r);p.write_text(json.dumps(r))
    def test_three_hashes_and_roles(self):
        udid,apps=self.assemble();self.assertEqual([a[0] for a in apps],list(join.ROLES))
    def test_mixed_commit(self):
        self.change(lambda r:r.update(workflow_commit='b'*40))
        with self.assertRaises(ValueError):self.assemble()
    def test_wrong_id(self):
        self.change(lambda r:r['apps'][0].update(bundle_id='wrong'))
        with self.assertRaises(ValueError):self.assemble()
    def test_hash_mismatch(self):
        self.change(lambda r:r['apps'][0].update(sha256='0'*64))
        with self.assertRaises(ValueError):self.assemble()
    def test_path_escape(self):
        self.change(lambda r:r['apps'][0].update(path='../elsewhere.ipa'))
        with self.assertRaises(ValueError):self.assemble()
    def test_missing_app(self):
        (self.root/'cardboard/cardboard.ipa').unlink()
        with self.assertRaises(OSError):self.assemble()
    def test_extension_refused(self):
        p=self.root/'cardboard/cardboard.ipa'
        with zipfile.ZipFile(p,'a') as z:z.writestr('Payload/Test.app/Plugins/Extra.appex/Info.plist',b'')
        self.change(lambda r:r['apps'][0].update(sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        with self.assertRaises(ValueError):self.assemble()
    def test_bad_udid(self):
        result=join.assemble(self.root,self.commit,'invalid',self.out);self.out.write_text(json.dumps(result))
        with self.assertRaises(ValueError):renew.prepare(self.out)

class SignerPolicyTests(unittest.TestCase):
    def test_reviewed_signer(self):
        with patch.object(renew.subprocess, 'run', return_value=subprocess.CompletedProcess([],0,'sparky-shared-pairing-1\nAnisette endpoint: http://127.0.0.1:6969\n')) as call:
            renew.verify_signer('reviewed-xtool')
            self.assertEqual(call.call_args.args[0], ['reviewed-xtool','sparky-policy'])
    def test_stock_or_failed_signer(self):
        for code, output in [(0,'xtool 1.24.0\n'),(1,'sparky-shared-pairing-1\n'),(0,'')]:
            with patch.object(renew.subprocess, 'run', return_value=subprocess.CompletedProcess([],code,output)):
                with self.assertRaises(ValueError): renew.verify_signer('wrong-xtool')

if __name__=='__main__':unittest.main()
