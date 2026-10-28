#!/usr/bin/env python3
"""Restore pinned external repositories; vendored cores never require patching."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


def require(ok, message):
    if not ok:
        raise ValueError(message)


def git_env():
    return {k:v for k,v in os.environ.items() if not k.startswith('GIT_')}


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True, env=git_env()).strip()


def run(argv):
    subprocess.run(argv, check=True, env=git_env())


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def safe_path(name):
    require(isinstance(name,str) and name and not PurePosixPath(name).is_absolute() and
            all(x not in ('','.', '..') for x in name.split('/')) and '\\' not in name,
            'Unsafe dependency path: '+str(name))


def links(root):
    data=subprocess.check_output(['git','-C',str(root),'ls-tree','-rz','HEAD'],env=git_env()).split(b'\0')
    result={}
    for line in data:
        if not line:continue
        header,name=line.split(b'\t',1);mode,kind,commit=header.split()
        if mode==b'160000':result[name.decode()]=commit.decode()
    return result


def clean(root):
    require(not git(root,'status','--porcelain','--untracked-files=all','--ignore-submodules=all'),
            'Uncommitted changes in '+str(root)+'; preserve them and use a clean checkout before deps.')


def repo_at(path):
    return (path/'.git').exists()


def register_submodule(parent, relative, commit):
    """Local clones must also be active for legacy Makefile submodule checks."""
    names=[]
    data=git(parent,'config','-z','--file','.gitmodules','--get-regexp',r'^submodule\..*\.path$')
    for item in data.split('\0'):
        if item:
            key,path=item.split('\n',1)
            if path==relative:names.append(key[len('submodule.'):-len('.path')])
    require(len(names)==1,'Gitlink needs exactly one .gitmodules path: '+relative)
    git(parent,'config','--local','submodule.'+names[0]+'.active','true')
    status=git(parent,'submodule','status','--',relative)
    # git() trims whitespace; +/- prefixes remain and therefore fail this check.
    require(bool(status) and status.split()[0]==commit,'Dependency is not active at its exact pin: '+relative)


def initialize(root, lock_path, offline=None, local=None, plan=False):
    root=Path(root).resolve(strict=True);lock=json.loads(Path(lock_path).read_text())
    require(Path(git(root,'rev-parse','--show-toplevel')).resolve()==root,'Not an independent repository root')
    require(lock['schema_version']==1,'Unsupported dependency lock schema')
    clean(root)
    root_links=links(root)
    require(root_links==lock['root_gitlinks'],'Root gitlinks differ from locks/dependencies.json')
    pins=lock['dependencies']
    for name,sha in pins.items():
        safe_path(name);require(re.fullmatch('[0-9a-f]{40}',sha) is not None,'Invalid commit for '+name)
        require(any(name==p or name.startswith(p+'/') for p in root_links),'Pin has no root gitlink: '+name)
    if plan:return {'plan_only':True,'count':len(pins),'dependencies':pins}
    require(not (offline and local),'Choose either --offline-dir or --local-source')
    bundles=None
    if offline:
        offline=Path(offline).resolve(strict=True);bundles=json.loads((offline/'dependencies.json').read_text())['dependencies']
    if local:local=Path(local).resolve(strict=True)
    queue=[('.',root_links)];restored={};omitted={}
    while queue:
        parent_name,children=queue.pop(0);parent=root if parent_name=='.' else root/parent_name
        for rel,commit in sorted(children.items()):
            name=rel if parent_name=='.' else parent_name+'/'+rel;safe_path(name)
            require(re.fullmatch('[0-9a-f]{40}',commit) is not None,'Invalid gitlink: '+name)
            if name not in pins:
                excluded=lock.get('excluded_dependencies',{}).get(name)
                expected=excluded.get('gitlink') if isinstance(excluded,dict) else excluded
                allowed=(expected==commit or (parent_name=='.' and lock.get('out_of_scope_root_gitlinks',{}).get(name)==commit))
                require(allowed,'Unclassified dependency: '+name)
                omitted[name]=commit;continue
            require(pins[name]==commit,'Pin/gitlink mismatch: '+name)
            target=root/name
            require(not any(p.is_symlink() for p in [target,*target.parents] if p!=root and p.is_relative_to(root)),
                    'Symlink in dependency path: '+name)
            require(target.resolve().is_relative_to(root),'Dependency escapes checkout: '+name)
            if repo_at(target):
                require(Path(git(target,'rev-parse','--show-toplevel')).resolve()==target.resolve(),'Invalid child repository: '+name)
                require(git(target,'rev-parse','HEAD')==commit,'Existing dependency has wrong HEAD: '+name+'; use a new checkout, do not reset it.')
                clean(target)
            else:
                require(not target.exists() or (target.is_dir() and not any(target.iterdir())),
                        'Nonempty failed/uninitialized dependency: '+name+'; preserve it and retry in a new checkout.')
                print('Initializing '+name+' @ '+commit,flush=True)
                if bundles is not None:
                    require(name in bundles,'Offline bundle manifest lacks dependency: '+name)
                    record=bundles[name];safe_path(record['bundle']);bundle=(offline/record['bundle']).resolve()
                    require(bundle.is_relative_to(offline),'Bundle escapes offline directory')
                    require(record['commit']==commit,'Offline commit mismatch: '+name)
                    require(bundle.is_file() and digest(bundle)==record['sha256'],'Offline bundle hash mismatch: '+name)
                    run(['git','clone','--no-recurse-submodules','--no-checkout',str(bundle),str(target)])
                    run(['git','-C',str(target),'checkout','--detach',commit])
                elif local:
                    source=local/name
                    require(repo_at(source),'Local dependency repository missing: '+str(source))
                    require(git(source,'rev-parse',commit+'^{commit}')==commit,'Local dependency pin missing: '+name)
                    # No --shared or alternates: deletion of the old repo must not break this one.
                    run(['git','clone','--no-recurse-submodules','--no-hardlinks','--no-checkout',str(source),str(target)])
                    run(['git','-C',str(target),'checkout','--detach',commit])
                else:
                    run(['git','-c','submodule.recurse=false','-c','url.https://github.com/.insteadOf=git@github.com:',
                         '-C',str(parent),'submodule','update','--init','--checkout','--',rel])
                require(git(target,'rev-parse','HEAD')==commit,'Fetched wrong commit: '+name)
                clean(target)
                if offline or local:
                    git(target,'remote','remove','origin')
                require(not (Path(git(target,'rev-parse','--absolute-git-dir'))/'objects/info/alternates').exists(),
                        'Restored dependency unexpectedly has Git object alternates: '+name)
            register_submodule(parent,rel,commit)
            restored[name]=commit
            queue.append((name,links(target)))
    require(restored==pins,'Incomplete dependency traversal; inspect lock and recursive gitlinks')
    return {'plan_only':False,'count':len(restored),'root_commit':git(root,'rev-parse','HEAD'),
            'lock_sha256':digest(lock_path),'dependencies':restored,'omitted':omitted,
            'source':'offline-bundles' if offline else ('local-repositories' if local else 'upstream-git'),
            'hardware_built':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--lock',type=Path,default=Path('locks/dependencies.json'))
    p.add_argument('--offline-dir',type=Path);p.add_argument('--local-source',type=Path);p.add_argument('--plan',action='store_true');p.add_argument('--report',type=Path)
    a=p.parse_args()
    try:
        if a.report:
            require(not a.report.exists(),'Report exists; select a new path')
            require(not a.report.resolve().is_relative_to(a.root.resolve()),'Dependency report must be outside source checkout')
        lock=a.lock if a.lock.is_absolute() else a.root/a.lock
        result=initialize(a.root,lock,a.offline_dir,a.local_source,a.plan)
        if a.report:
            a.report.parent.mkdir(parents=True,exist_ok=True)
            with a.report.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
        print(json.dumps(result if a.plan else {'count':result['count'],'status':'dependencies ready; no hardware validation performed'},indent=2))
        return 0
    except (ValueError,KeyError,OSError,subprocess.CalledProcessError) as e:
        print('ERROR: '+str(e),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
