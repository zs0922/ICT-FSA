import importlib.util
import json
import hashlib
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest

p=Path(__file__).resolve().parents[1]/'scripts/ict_deps.py'
spec=importlib.util.spec_from_file_location('ict_deps',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def cmd(root,*args):
 return subprocess.check_output(['git','-C',str(root),*args],text=True,stderr=subprocess.DEVNULL).strip()
def init(root):
 root.mkdir(parents=True);cmd(root,'init');cmd(root,'config','user.name','test');cmd(root,'config','user.email','test@example.invalid')
def commit(root):
 cmd(root,'add','.');cmd(root,'commit','-m','fixture');return cmd(root,'rev-parse','HEAD')

class Dependencies(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
  self.old=self.base/'old';self.dep=self.old/'lib';init(self.dep);(self.dep/'file').write_text('test');self.sha=commit(self.dep)
  self.root=self.base/'new';init(self.root)
  (self.root/'.gitmodules').write_text(f'[submodule "lib"]\n path = lib\n url = {self.dep}\n')
  self.lock=self.root/'lock.json';self.lock.write_text(json.dumps({'schema_version':1,'root_gitlinks':{'lib':self.sha},'dependencies':{'lib':self.sha}}))
  (self.root/'lib').mkdir();cmd(self.root,'add','.');cmd(self.root,'update-index','--add','--cacheinfo',f'160000,{self.sha},lib');cmd(self.root,'commit','-m','root fixture')
 def test_local_independent_and_reusable(self):
  r=m.initialize(self.root,self.lock,local=self.old);self.assertEqual(r['count'],1)
  self.assertFalse((self.root/'lib/.git/objects/info/alternates').exists())
  self.assertEqual(m.initialize(self.root,self.lock)['count'],1)
  self.assertEqual(cmd(self.root,'submodule','status','--','lib').split()[0],self.sha)
  self.assertEqual(cmd(self.root/'lib','remote'),'')
  shutil.rmtree(self.old)
  self.assertEqual(cmd(self.root/'lib','rev-parse','HEAD'),self.sha)
  cmd(self.root/'lib','fsck','--connectivity-only')
 def test_plan_no_mutation(self):
  self.assertEqual(m.initialize(self.root,self.lock,plan=True)['count'],1);self.assertFalse(any((self.root/'lib').iterdir()))
 def test_dirty_dependency_preserved(self):
  m.initialize(self.root,self.lock,local=self.old);(self.root/'lib/file').write_text('user edit')
  with self.assertRaisesRegex(ValueError,'Uncommitted'):m.initialize(self.root,self.lock)
  self.assertEqual((self.root/'lib/file').read_text(),'user edit')
 def test_nonempty_failed_clone_preserved(self):
  (self.root/'lib/failure.log').write_text('keep')
  with self.assertRaisesRegex(ValueError,'Nonempty'):m.initialize(self.root,self.lock,local=self.old)
 def test_wrong_root_pin(self):
  data=json.loads(self.lock.read_text());data['root_gitlinks']={};self.lock.write_text(json.dumps(data));commit(self.root)
  with self.assertRaisesRegex(ValueError,'Root gitlinks'):m.initialize(self.root,self.lock,plan=True)
 def test_unsafe_path(self):
  for p in ['../secret','/tmp/secret','a/../../secret','a//b','a\\b']:
   with self.assertRaises(ValueError):m.safe_path(p)
 def bundle_fixture(self):
  # Match the old nm37 source_bundle exporter: refs/heads/locked and fields below.
  directory=self.base/'offline';(directory/'bundles').mkdir(parents=True)
  bundle=directory/'bundles/locked.bundle'
  cmd(self.dep,'update-ref','refs/heads/locked',self.sha)
  cmd(self.dep,'bundle','create',str(bundle),'refs/heads/locked')
  record={'commit':self.sha,'bundle':'bundles/locked.bundle',
          'sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'bytes':bundle.stat().st_size,
          'parent':'.','parent_relative_gitlink':'lib','refs':{'refs/heads/locked':self.sha}}
  (directory/'dependencies.json').write_text(json.dumps({'schema_version':1,'kind':'nm37-pinned-dependencies','dependencies':{'lib':record}}))
  return directory,bundle
 def test_real_offline_bundle_independent_and_active(self):
  directory,bundle=self.bundle_fixture();shutil.rmtree(self.old)
  r=m.initialize(self.root,self.lock,offline=directory)
  self.assertEqual(r['source'],'offline-bundles')
  self.assertEqual(cmd(self.root,'submodule','status','--','lib').split()[0],self.sha)
  self.assertEqual(cmd(self.root/'lib','remote'),'')
  self.assertEqual((self.root/'lib/file').read_text(),'test')
  shutil.rmtree(directory)
  self.assertEqual(m.initialize(self.root,self.lock)['count'],1)
 def test_bad_offline_hash_prevents_clone(self):
  directory,bundle=self.bundle_fixture();bundle.write_bytes(bundle.read_bytes()+b'corrupt')
  with self.assertRaisesRegex(ValueError,'hash mismatch'):m.initialize(self.root,self.lock,offline=directory)
  self.assertFalse((self.root/'lib/.git').exists())
 def test_missing_offline_record_is_explicit(self):
  directory,bundle=self.bundle_fixture();(directory/'dependencies.json').write_text('{"dependencies":{}}')
  with self.assertRaisesRegex(ValueError,'lacks dependency: lib'):m.initialize(self.root,self.lock,offline=directory)
 def test_recursive_unclassified_gitlink_fails(self):
  (self.dep/'.gitmodules').write_text('[submodule "nested"]\n path = nested\n url = https://example.invalid/nested.git\n')
  cmd(self.dep,'add','.');cmd(self.dep,'update-index','--add','--cacheinfo',f'160000,{self.sha},nested');cmd(self.dep,'commit','-m','nested gitlink')
  outer=cmd(self.dep,'rev-parse','HEAD')
  lock=json.loads(self.lock.read_text());lock['dependencies']['lib']=outer;lock['root_gitlinks']['lib']=outer
  self.lock.write_text(json.dumps(lock));cmd(self.root,'add','.');cmd(self.root,'update-index','--add','--cacheinfo',f'160000,{outer},lib');cmd(self.root,'commit','-m','outer pin')
  with self.assertRaisesRegex(ValueError,'Unclassified dependency: lib/nested'):m.initialize(self.root,self.lock,local=self.old)
  self.assertFalse((self.root/'lib/nested/.git').exists())
 def test_explicit_recursive_exclusion_is_preserved(self):
  (self.dep/'.gitmodules').write_text('[submodule "nested"]\n path = nested\n url = https://example.invalid/nested.git\n')
  cmd(self.dep,'add','.');cmd(self.dep,'update-index','--add','--cacheinfo',f'160000,{self.sha},nested');cmd(self.dep,'commit','-m','nested gitlink')
  outer=cmd(self.dep,'rev-parse','HEAD')
  lock=json.loads(self.lock.read_text());lock['dependencies']['lib']=outer;lock['root_gitlinks']['lib']=outer
  lock['excluded_dependencies']={'lib/nested':{'gitlink':self.sha,'reason':'fixture explicit out of scope'}}
  self.lock.write_text(json.dumps(lock));cmd(self.root,'add','.');cmd(self.root,'update-index','--add','--cacheinfo',f'160000,{outer},lib');cmd(self.root,'commit','-m','outer pin')
  r=m.initialize(self.root,self.lock,local=self.old)
  self.assertEqual(r['omitted'],{'lib/nested':self.sha})
 def test_dependency_symlink_rejected(self):
  (self.root/'lib').rmdir();(self.root/'spare').mkdir();(self.root/'lib').symlink_to('spare')
  # The user-modified gitlink is not traversed or overwritten, even inside root.
  with self.assertRaisesRegex(ValueError,'Uncommitted|Symlink'):m.initialize(self.root,self.lock,local=self.old)
  self.assertTrue((self.root/'lib').is_symlink())
if __name__=='__main__':unittest.main()
